from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, WebSocket, Depends, BackgroundTasks
from auth import decode_token, get_current_user
from database import get_db
from uuid import UUID
import asyncio
from decimal import Decimal
router = APIRouter()
connections = {}


@router.websocket("/balance")
async def balance(websocket: WebSocket):
    await websocket.accept()

    token = await websocket.receive_text()
    phone = decode_token(token)

    if phone not in connections:
        connections[phone] = []
    connections[phone].append(websocket)

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM usdt_balances
                WHERE phone = %s
                """,
                (phone,)
            )
            balances = cursor.fetchone()

    if not balances:
        return

    await websocket.send_json({
        "ok": True,
        "balance": balances["balance"]
    })

    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(e)
        if phone in connections:
            connections[phone].remove(websocket)
            if len(connections[phone]) == 0:
                del connections[phone]

async def send_balance(phone):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance
                FROM usdt_balances
                WHERE phone = %s
                """,
                (phone,)
            )
            balances = cursor.fetchone()

    if not balances:
        return

    user_connections = connections.get(phone, [])

    for websocket in user_connections.copy():
        try:
            await websocket.send_json({
                "ok": True,
                "balance": balances["balance"]
            })
        except Exception as e:
            print(f"WebSocket error: {e}")

            if websocket in user_connections:
                user_connections.remove(websocket)

    if not user_connections:
        connections.pop(phone, None)


class Transfer(BaseModel):
    resever_phone: str
    amount: Decimal 
    idempotency_key: UUID
        


@router.post("/transfer")
async def transfer(background_tasks: BackgroundTasks,
transfer: Transfer, phone: str = Depends(get_current_user)):
    resever = transfer.resever_phone
    amount = transfer.amount
    idempotency_key = transfer.idempotency_key

    if not resever.isdigit():
        return {
            "ok": False,
            "message": "رقم الهاتف يجب أن يحتوي على أرقام فقط"
        }
    if not (resever.startswith("09") or resever.startswith("01")):
        return {
            "ok": False,
            "message": "رقم الهاتف غير صحيح"
        }
    if len(resever) != 10:
        return {
            "ok": False,
            "message": "رقم غير صحيح"
        }


    if amount <= 0:
        return {
            "ok": False,
            "message": "يجب ان يكون المبلغ اكبر من صفر"
        }
    if resever == phone:
        return {
            "ok": False,
            "message": "لايمكنك التحويل لنفسك"
        }
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM users 
            WHERE phone = %s
            """,
            (phone,)
            )
            db_user = cursor.fetchone()
            if not db_user:
                return {"ok": False,
                    "message": "الحساب غير موجود"}
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE phone = %s
                """,
                (resever,)
            )
            db_resever = cursor.fetchone()
            if not db_resever:
                return {
                    "ok": False,
                    "message": "المستلم غير موجود"
                }
            cursor.execute(
                """
                SELECT *
                FROM usdt_balances
                WHERE phone = %s
                FOR UPDATE
                """,
                (phone,)
            )
            balance_row = cursor.fetchone()
            if not balance_row:
                return {
                    "ok": False,
                    "message": "يبدو انه لايوجد لديك محفظة بعد تواصل مع الدعم لحل المشكلة"
                }
            balance = balance_row["balance"]

            if amount > balance:
                return {
                    "ok": False,
                    "message": "رصيدك غير كاف"
                }
            cursor.execute(
            """
            INSERT INTO transfer_requests
            (idempotency_key, phone, receiver_phone, amount)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING id
            """,
            (idempotency_key, phone, resever, amount)
            )
            request = cursor.fetchone()
            if request is None:
                cursor.execute(
                """
                SELECT *
                FROM transfer_requests
                WHERE idempotency_key = %s
                FOR UPDATE
                """,
                (idempotency_key,)
                )
                existing_request = cursor.fetchone()
                if (
                existing_request["phone"] != phone
                or existing_request["receiver_phone"] != resever
                or existing_request["amount"] != amount
                ):
                    return {
                    "ok": False,
                    "message": "معرف المعاملة مستخدم من قبل"
                            }
                if existing_request["status"] == "success":
                    return {
                    "ok": True,
                    "status": "success",
                    "receiver_name": db_resever["name"],
                    "receiver_phone": existing_request["receiver_phone"],
                    "amount": existing_request["amount"],
                    "total": existing_request["amount"],
                    "fee": 0,
                    "type": "transfer",
                    "network": "INTERNAL",
                    "message": "تم التحويل بنجاح",
                    "created_at": existing_request["created_at"]
                    }
                if existing_request["status"] == "processing":
                    return {
                    "ok": False,
                        "message": "العملية قيد المعالجة"
                            }
            
                
            try:
                cursor.execute(
                    """
                    UPDATE usdt_balances
                    SET balance = balance - %s
                    WHERE phone = %s AND balance >= %s
                    """,
                    (amount, phone, amount)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": "رصيدك غير كاف"
                    }
                cursor.execute(
                    """
                    UPDATE usdt_balances
                    SET balance = balance + %s
                    WHERE phone = %s
                    """,
                    (amount, resever)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": f"حدث خطأ اثناء إستلام المبلغ {amount}"
                    }

                cursor.execute(
                    """
                    INSERT INTO transactions
                    (user_phone, receiver_phone, type, network, amount, fee, net_amount, status)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, resever, "transfer_sent", "INTERNAL", amount, 0, amount, "success")
                )
                cursor.execute(
                    """
                    INSERT INTO transactions
                    (user_phone, receiver_phone, type, network, amount, fee, net_amount, status)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (resever, phone, "transfer_received", "INTERNAL", amount, 0, amount, "success")
                )

                message = f"تم تحويل {amount} USDT إلى {db_resever['name']}"
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s, %s, %s)
                    """,
                    (phone, f" تم تحويل {amount} إلى {db_resever['name']} بنجاح", message)
                )

                message = f"تم إستلام {amount} من {db_user['name']} بنجاح"
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s, %s, %s)
                    """,
                    (resever, f"تم إستلام {amount} من {db_user['name']} بنجاح", message)
                )
                cursor.execute(
                """
                UPDATE transfer_requests
                SET status = 'success'
                WHERE idempotency_key = %s
                """,
                (idempotency_key,)
                )

                conn.commit()
                await send_balance(phone)
                await send_balance(resever)
                #background_tasks.add_task(send_balance, phone)
                #background_tasks.add_task(send_balance, resever)
                #asyncio.run(send_balance(phone))     # ← بدل await
                #asyncio.run(send_balance(resever))   
                created_at = datetime.now()
                return {
                    "ok": True,
                    "status": "success",
                    "receiver_name": db_resever["name"],
                    "receiver_phone": resever,
                    "amount": amount,
                    "total": amount,
                    "fee": 0,
                    "type": "transfer",
                    "network": "INTERNAL",
                    "message": "تم التحويل بنجاح",
                    "created_at": created_at
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ داخلي"
                }
class Receiver(BaseModel):
    receiver_phone: str
    amount: Decimal #float
        
        
@router.post("/transfer/receiver")
def get_receiver(receiver: Receiver, phone: str = Depends(get_current_user)):
    amount = receiver.amount
    receiver = receiver.receiver_phone
    if not receiver:
        return {"ok": False,
            "message": "رقم الهاتف مطلوب"}
    if not receiver.isdigit():
        return {
        "ok": False,
        "message": "رقم الهاتف يجب أن يحتوي على أرقام فقط" }
    if not (receiver.startswith("09") or receiver.startswith("01")):
        return{
        "ok": False,
            "message": "رقم الهاتف غير صحيح"}
    if len(receiver) != 10:
        return{"ok": False,
            "message": "رقم الهاتف غير صحيح"}
  
    if receiver == phone:
        return {
        "ok": False,
        "message": "لايمكنك التحويل لنفسك"}
    if amount <= 0:
        return {
        "ok": False,
            "message": "يجب ان يكون المبلغ اكبر من صفر"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM users 
            WHERE phone = %s
            """,
            (receiver,)
            )
            db_resiver = cursor.fetchone()
            if not db_resiver:
                return {"ok": False,
                    "message": "المستلم غير موجود"}
                        
            cursor.execute(
            """
            SELECT *
            FROM usdt_balances
            WHERE phone = %s
            """,
            (phone,)
            )
            db_user = cursor.fetchone()
            
            if not db_user:
                return {"ok": False,
                    "message": "الحساب غير موجود"}
            if amount > db_user["balance"]:
                return {
                "ok": False,
                "message": "رصيدك غير كاف"}
            return {
                "ok": True, 
                    "name": db_resiver['name'],
                    "amount": amount,
                    "fee": 0,
                    "balance": db_user['balance'],
                    "total": amount}
