from auth import get_current_user
from database import get_db
from pydantic import BaseModel
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/transactions")
def get_transactions(phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM transactions
                WHERE user_phone = %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (phone,)
            )
            transactions = cursor.fetchall()

    if not transactions:
        return {
            "ok": True,
            "message": "لا توجد معاملات بعد",
            "transactions": []
        }

    results = []
    for transaction in transactions:
        results.append({
            "receiver_phone": transaction["receiver_phone"],
            "type": transaction["type"],
            "network": transaction["network"],
            "amount": transaction["amount"],
            "fee": transaction["fee"],
            "net_amount": transaction["net_amount"],
            "status": transaction["status"],
            "txid": transaction["txid"],
            "created_at": transaction["created_at"]
        })

    return {
        "ok": True,
        "transactions": results
    }


@router.get("/notifications")
def get_notifications(phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM notifications
                WHERE phone = %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (phone,)
            )
            db_notifications = cursor.fetchall()

    if not db_notifications:
        return {
            "ok": True,
            "message": "لا توجد إشعارات بعد",
            "notifications": []
        }

    results = []
    for db_notification in db_notifications:
        results.append({
            "id": db_notification["id"],
            "title": db_notification["title"],
            "message": db_notification["message"],
            "is_read": db_notification["is_read"],
            "created_at": db_notification["created_at"]
        })

    return {
        "ok": True,
        "notifications": results
    }


class ReadNotification(BaseModel):
    id: int


@router.put("/notifications/read")
def read_notification(
    notification: ReadNotification,
    phone: str = Depends(get_current_user)
):
    notification_id = notification.id

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM notifications
                WHERE id = %s
                AND phone = %s
                """,
                (notification_id, phone)
            )
            db_notification = cursor.fetchone()

            if not db_notification:
                return {
                    "ok": False,
                    "message": "الإشعار غير موجود"
                }
            if db_notification["is_read"] == 1:
                return {
                    "ok": True,
                    "message": "الإشعار مقروء مسبقًا"
                }

            try:
                cursor.execute(
                    """
                    UPDATE notifications
                    SET is_read = 1
                    WHERE id = %s
                    AND phone = %s
                    """,
                    (notification_id, phone)
                )

                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": "فشل تحديث الإشعار"
                    }

                conn.commit()
                return {
                    "ok": True,
                    "message": "تم تعليم الإشعار كمقروء"
                }

            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ داخلي"
                }

    