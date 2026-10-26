from fastapi import APIRouter, Depends
from pydantic import BaseModel
from config import *
from auth import *
from validators import *
from database import get_db
from wallets import send_balance
from storage import delete_file
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
prefix="/admin",
    tags=["admin"]
    )


def admin():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT phone
                FROM users
                WHERE phone = %s
                """,
                (admin_phone,)
            )
            db_admin = cursor.fetchone()
            if not db_admin:
                cursor.execute(
                    """
                    INSERT INTO users
                    (phone, name, email)
                    VALUES(%s, %s, %s)
                    """,
                    (admin_phone, "Nexa Platform", admin_email)
                )
                cursor.execute(
                    """
                    INSERT INTO usdt_balances
                    (phone, balance)
                    VALUES(%s, %s)
                    """,
                    (admin_phone, 0)
                )
                conn.commit()


class Login_admin(BaseModel):
    phone: str
    email: str
    password: str


@router.post("/admin/login")
def login_admin(admin: Login_admin):
    phone = admin.phone
    email = admin.email
    password = admin.password
    if phone != admin_phone or email != admin_email or password != admin_password:
        return {
            "ok": False,
            "message": "ليس لديك صلاحية "
        }
    token = create_admin_token(phone)#create_token(phone)
    return {
        "ok": True,
        "token": token,
        "message": "تم تسجيل دخول الأدمن بنجاح."
    }


@router.get("/admin/dashboard")
def dashboard(phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return {
            "ok": False,
            "message": "ليس لديك صلاحية الوصول"
        }
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM users
            """)
            result = cursor.fetchone()
    return {
        "ok": True,
        "users": result["total"]
    }


@router.get("/admin/store-requests")
def admin_stored(phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return {
        "ok": False,
        "message": "ليس لديك صلاحية الوصول"
            }
            
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM store_requests
            WHERE status = %s
            """,
            ("pending",)
            )
            requests = cursor.fetchall()
            return {
            "ok": True,
                "requests": requests
                    }
                    
                    
                    
class StoreRequestDecision(BaseModel):
    decision: str
        
    
@router.patch("/admin/store-requests/{request_id}")
def decide_store_request(
    request_id: int,
    store: StoreRequestDecision,
    phone: str = Depends(get_current_user)
):
    if phone != admin_phone:
        return {"ok": False,
            "message": "ليس لديك صلاححية"}
    if store.decision not in ["approved", "rejected"]:
        return {"ok": False,
            "message":"القرار غير صالح"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM store_requests
            WHERE id = %s
            """,
            (request_id,)
            )
            db_store = cursor.fetchone()
            if not db_store:
                return {
                "ok": False,
                    "message": "الطلب غير موجود"}
            if db_store["status"] != "pending":
                return {
                "ok": False,
                    "message": "تمت معالجة هذا الطلب مسبقًا"}
            if store.decision == "approved":
                try:
                    cursor.execute(
                    """
                    INSERT INTO stores(
                    owner_phone,
                    name,
                    description
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    db_store["owner_phone"],
                    db_store["store_name"],
                    db_store["store_description"]
                    )
                    )
                    cursor.execute(
                    """
                    UPDATE store_requests
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("approved", request_id)
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    db_store["owner_phone"],
                    "تمت الموافقة على متجرك",
                    "تمت الموافقة على طلب إنشاء متجرك بنجاح."
                    )
                    )
                    conn.commit()
                    return {"ok": True,
                        "message": "تمت الموافقة على المتجر"}
                except Exception as e :
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                        "message": "حدث خطأ أثناء الموافقة على الطلب"
                            }
            elif store.decision == "rejected":
                try:
                    cursor.execute(
                    """
                    UPDATE store_requests
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("rejected", request_id)
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    db_store["owner_phone"],
                    "تم رفض طلب المتجر",
                    "نأسف، تم رفض طلب إنشاء متجرك."
                    )
                    )
                    conn.commit()
                    return {
                    "ok": True,
                        "message": "تم رفض الطلب"
                            }
                except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                        "message": "حدث خطأ أثناء رفض الطلب"
                            }
                            
                            
                            
                            
@router.get("/admin/purchases")
def admin_purchases(phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return {"ok": False,
            "message": "ليس لديك صلاحية"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM purchases
            WHERE status = %s
            ORDER BY created_at DESC
            """, ("pending",)
            )
            purchases = cursor.fetchall()
            return {
                "ok": True,
                "purchases": purchases}
                    
                    
class PurchaseDecision(BaseModel):
    decision: str          
@router.patch("/admin/purchases/{purchase_id}")
async def decide_purchase(
    purchase_id: int,
    purchase: PurchaseDecision,
    phone: str = Depends(get_current_user)
):
    if phone != admin_phone:
        return {
            "ok": False,
            "message": "ليس لديك صلاحية"
        }

    if purchase.decision not in ["approved", "rejected"]:
        return {
            "ok": False,
            "message": "القرار غير صالح"
        }
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM purchases
            WHERE id = %s
            """,
            (purchase_id,)
            )
            db = cursor.fetchone()
            if not db:
                return {"ok": False,
                    "message": "عملية الشراء غير موجودة"}
            if db["status"] != "pending":
                return {
                "ok": False,
                "message": "تمت معالجة عملية الشراء مسبقًا"}
            amount = db["amount"]
            cursor.execute(
            """
            SELECT * 
            FROM products 
            WHERE id = %s
            """,
            (db["product_id"],)
            )
            db_product = cursor.fetchone()
            if not db_product:
                return {"ok": False,
                    "message": "التاحر غير موجود"}
            store_id = db_product["store_id"]
            product_name = db_product["name"]
            cursor.execute(
            """
            SELECT owner_phone
            FROM stores
            WHERE id = %s
            """,
            (store_id,)
            )
            db_store = cursor.fetchone()
            if not db_store:
                return {
                "ok": False,
                "message": "المتجر غير موجود"}
            store_phone = db_store["owner_phone"]
            transaction_id = db["transaction_id"]
            if purchase.decision == "approved":
                try:
                    cursor.execute(
                    """
                    UPDATE usdt_balances
                    SET balance = balance - %s
                    WHERE phone =%s AND balance >= %s
                    """,
                    (amount, admin_phone, amount)
                    )
                    if cursor.rowcount == 0:
                        conn.rollback()
                        return {
                        "ok": False,
                            "message": "رصيدك غير كاف"}
                    cursor.execute(
                    """
                    UPDATE usdt_balances 
                    SET balance = balance + %s
                    WHERE phone = %s
                    """,
                    (amount, store_phone )
                    )
                    cursor.execute(
                    """
                    UPDATE transactions
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("success", transaction_id)
                    )
                    cursor.execute(
                    """
                    UPDATE purchases
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("success", purchase_id)
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    db["buyer_phone"],
                    "تمت الموافقة على عملية الشراء",
                    f"تمت الموافقة على شراء «{product_name}»، ويمكنك الآن تحميل المنتج."
                    )
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    store_phone,
                    "عملية شراء ناجحة",
                    f"تم شراء منتجك «{product_name}» بنجاح. المبلغ: {amount} USDT."
                    )
                    )
                    conn.commit()
                    await send_balance(store_phone)
                    await send_balance(admin_phone)
                    return {
                    "ok": True,
                    "message": "تمت الموافقة على عملية الشراء بنجاح"}
                except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "حدث خطأ أثناء الموافقة على عملية الشراء"}
            elif purchase.decision == "rejected":
                try:
                    cursor.execute(
                    """
                    UPDATE usdt_balances
                    SET balance = balance - %s
                    WHERE phone = %s AND balance >= %s
                    """,
                    (amount, admin_phone, amount)
                    )
                    if cursor.rowcount == 0:
                        conn.rollback()
                        return {
                        "ok": False,
                        "message": "رصيد المنصة غير كاف"
                        }
                    cursor.execute(
                    """
                    UPDATE usdt_balances
                    SET balance = balance + %s
                    WHERE phone = %s
                    """,
                    (amount, db["buyer_phone"])
                    )
                    cursor.execute(
                    """
                    UPDATE transactions
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("rejected", transaction_id)
                    )
                    cursor.execute(
                    """
                    UPDATE purchases
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("rejected", purchase_id)
                    )                        
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    db["buyer_phone"],
                    "تم رفض عملية الشراء واسترجاع المبلغ",
                    f"تم رفض شراء منتج «{product_name}»، وتم استرجاع مبلغ {amount} USDT إلى رصيدك."
                    )
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications(
                    phone,
                    title,
                    message
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                    store_phone,
                    "تم رفض عملية الشراء",
                    f"تم رفض عملية شراء منتجك «{product_name}» بمبلغ {amount} USDT."
                    )
                    )
                    conn.commit()
                    await send_balance(db["buyer_phone"])
                    await send_balance(admin_phone)
                    return {
                    "ok": True,
                    "message": "تم رفض عملية الشراء واسترجاع المبلغ بنجاح"}
                except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                        "message": "حدث خطأ أثناء رفض عملية الشراء"
                            }
#======================================|==
#Searching for store opening requests  |
#======================================|==
@router.get("/store-requests")
def get_marketplace_store_requests(phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return{"ok": False,
            "message": "ليس لديك صلاحية"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM marketplace_store_requests
            WHERE status = %s
            ORDER BY created_at DESC
            """,
            ("pending",)
            )
            requests = cursor.fetchall()
            return {
            "ok": True,            
            "requests": requests}
#===========================
#Finish End
#===========================

#=================================================|
#Approval of the request to open a physical store |
#=================================================|
class MarketplaceStoreDecision(BaseModel):
    decision: str
@router.patch("/store-requests/{request_id}")
def decide_marketplace_store(
    request_id: int,
    store: MarketplaceStoreDecision,
    phone: str = Depends(get_current_user)
):
    if phone != admin_phone:
        return {
        "ok": False,
        "message": "ليس لديك صلاحية"
        }
    if store.decision not in ["approved", "rejected"]:
        return {
        "ok": False,
        "message": "القرار غير صالح"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_store_requests
            WHERE id = %s
            """,
            (request_id,)
            )
            store_db = cursor.fetchone()
            if not store_db:
                return {
                "ok": False,
                "message": "طلب المتجر غير موجود"}
            if store_db["status"] != "pending":
                return {
                "ok": False,
                "message": "تمت معالجة هذا الطلب مسبقًا"}
            if store.decision == "approved":
                        try:
                            cursor.execute(
                            """
                            INSERT INTO marketplace_stores
                            (owner_phone, name, description, location, delivery_type, store_image, owner_photo)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                            store_db["owner_phone"], store_db["store_name"], store_db["store_description"], store_db["location"],
                            store_db["delivery_type"], store_db["store_image"], store_db["owner_photo"]
                            )
                            )
                            cursor.execute(
                            """
                            UPDATE marketplace_store_requests
                            SET status = %s
                            WHERE id = %s
                            """,
                            ("approved", request_id)
                            )
                            cursor.execute(
                            """
                            INSERT INTO notifications
                            (phone, title, message)
                            VALUES (%s, %s, %s)
                            """,
                            (
                            store_db["owner_phone"],
                            "تمت الموافقة على متجرك",
                            "تمت الموافقة على طلب فتح متجرك، يمكنك الآن البدء بإضافة منتجاتك."
                            )
                            )
                            conn.commit()
                            return{"ok": True,
                                "message": "تمت الموافقة على طلب فتح المتجر بنجاح"}
                        except Exception as e:
                            print(e)
                            conn.rollback()
                            return {
                            "ok": False,
                            "message": "حدث خطأ أثناء قبول الطلب"}   
            elif store.decision == "rejected":
                try:
                    cursor.execute(
                    """
                    SELECT name
                    FROM users
                    WHERE phone = %s
                    """,
                    (store_db["owner_phone"],)
                    )
                    db_user = cursor.fetchone()
                    if not db_user:
                        return{"ok": False,
                            "message": "الحساب غير موجود او محزوف"}
                    name = db_user["name"]
                    cursor.execute(
                    """
                    UPDATE marketplace_store_requests
                    SET status = %s
                    WHERE id = %s
                    """,
                    ("rejected", request_id)
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES (%s, %s, %s)
                    """,
                    (
                    store_db["owner_phone"],
                    "تم رفض طلب فتح المتجر",
                    f"«عزيزي الكريم {name}، نعتذر، تعذّر قبول طلب فتح المتجر الخاص بك. يرجى التواصل مع الدعم لمعرفة التفاصيل.»"                                                      
                    )
                    )
                    conn.commit()
                    return{"ok": True,
                        "message": f"تم رفض فتح متجر للمستخدم {name}"}
                except Exception as e:
                            print(e)
                            conn.rollback()
                            return {
                            "ok": False,
                            "message": "حدث خطاء اثناء عملية رفض الطلب"} 
                                
                                
                                
@router.get("/p2p/merchant-applications")
def get_p2p_merchant_applications(phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return{"ok": False,
            "message": "ليس لديك صلاحية"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM p2p_merchant_applications
            WHERE status = %s
            """,
            ("pending",)
            )
            db_p2p = cursor.fetchall()
            if not db_p2p:
                return{"ok": True,
                    "message": "لاتوجد طلبات تاجر p2p بعد",
                    "db_p2p": []}
            return{"ok": True,
            "message": "طلبات تجار p2p متوفرة",
            "db_p2p": db_p2p}
   
   
class P2PMerchantApplicationDecision(BaseModel):
    decision: str
@router.patch("/p2p/merchant-applications/{application_id}")
def decide_p2p_merchant_application(application_id: int, decision: P2PMerchantApplicationDecision,phone: str = Depends(get_current_user)):
    if phone != admin_phone:
        return{"ok": False,
            "message": "ليس لديك صلاحية"}
    if decision.decision not in ["approved", "rejected"]:
        return{"ok": False,
            "message": "خيار غير متوفر"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM p2p_merchant_applications
            WHERE id = %s
            AND status = %s
            FOR UPDATE
            """,
            (application_id, "pending")
            )
            db_p2p = cursor.fetchone()
            if not db_p2p:
                return{"ok": False,
                    "message": "الطلب غير موجود"}
            if decision.decision == "approved":
                try:
                    cursor.execute(
                    """
                    UPDATE p2p_merchant_applications
                    SET status = %s,
                    reviewed_by = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = %s 
                    AND status = %s
                    """,
                    ("approved", admin_phone, application_id, "pending")
                    )
                    if cursor.rowcount != 1:
                        raise Exception('error_update')
                    cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, phone)
                    VALUES(%s, %s, %s)
                    """,
                    ("تمت الموافقة على طلبك", 
                    "مبارك! تمت الموافقة على طلب انضمامك كتاجر P2P في Nexa. يمكنك الآن الاستفادة من خدمات تجار P2P وفقًا للشروط المعتمدة في المنصة.", 
                    db_p2p["user_phone"])
                    )
                    conn.commit()
                    return{'ok': True,
                        'message': 'تمت الموافقة على طلب تاجر p2p بنجاح'}
                except Exception as e:
                            print(e)
                            conn.rollback()
                            return {
                            "ok": False,
                            "message": "حدث خطاء اثناء عملية قبول الطلب"} 
                                
                
            else:
                try:
                    cursor.execute(
                    """
                    UPDATE p2p_merchant_applications
                    SET status = %s,
                    reviewed_by = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    AND status = %s
                    """,
                    ("rejected", admin_phone, application_id, "pending")
                    )
                    if cursor.rowcount != 1:
                        raise Exception('error_update')
                    cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, phone)
                    VALUES(%s, %s, %s)
                    """,
                    ('تحديث طلب تاجر P2P',
                    'نأسف لإبلاغك بأنه لم تتم الموافقة على طلب انضمامك كتاجر P2P في Nexa. يمكنك مراجعة سبب الرفض والتواصل مع الدعم إذا كنت بحاجة إلى توضيح.',
                    db_p2p['user_phone'])
                    )
                    conn.commit()
                    try:
                        
                        delete_file(db_p2p["personal_photo_key"])
                    except Exception as cleanup_error:
                        print(f"فشل حذف صور طلب P2P: {cleanup_error}")
                    try:
                        delete_file(db_p2p["id_photo_key"])
                        
                    except Exception as cleanup_error:
                        print(f"فشل حذف صور طلب P2P: {cleanup_error}")
                    return{'ok': True,
                        'message': 'تم رفض الطلب بحالة نجاح'}
                except Exception as e:
                            print(e)
                            conn.rollback()
                            return {
                            "ok": False,
                            "message": "حدث خطاء اثناء عملية رفض الطلب"} 
                                
                
                    