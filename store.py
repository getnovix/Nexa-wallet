from fastapi import APIRouter, Depends
from pydantic import BaseModel
from decimal import Decimal
from database import get_db
from auth import get_current_user
from config import admin_phone
from wallets import send_balance
router = APIRouter()
class StoreRequest(BaseModel):
    store_name: str
    store_description: str
    store_type: str
    verification_document: str | None = None
@router.post("/storeRequest")
def new_store(new_store: StoreRequest, phone: str =  Depends(get_current_user)):
    store_name = new_store.store_name
    store_description = new_store.store_description
    store_type = new_store.store_type
    verification_document = new_store.verification_document
    if not store_name:
        return {"ok": False,
            "message": "الاسم مطلوب"}
    if not store_description:
        return {"ok": False,
            "message":"وصف المتجر مطلوب"}
    if len (store_description) <= 20:
        return {"ok": False,
            "message": "يجب ان يكون الوصف اكبر من 20 حرف على الأقل"}
    if store_type != "رقمي":
        return {"ok": False,
            "message": "لايتوفر انشاء متجر غير رقمي بعد.."}
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM stores
            WHERE owner_phone = %s
            """,
            (phone,)
            )
            db_stor = cursor.fetchone()
            if db_stor:
                return {"ok": False,
                    "message": "لديك متجر بالفعل"}
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
            FROM stores
            WHERE name = %s
            """,
            (store_name,)
            )
            db_name_store = cursor.fetchone()
            if db_name_store:
                return {"ok": False,
                    "message": "هذا الإسم مستخدم" }
            try:
                cursor.execute(
                """
                INSERT INTO store_requests(
                owner_phone,
                store_name,
                store_description,
                store_type,
                verification_document
                )
                VALUES(%s, %s, %s, %s, %s)
                """,
                (phone, store_name, store_description, store_type, verification_document)
                )
                conn.commit()
                return {"ok" :True,
                    "message": "تم إرسال الطلب بنجاح"}
                        
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ عند فتح المتجر"
                }
                
                
                
                
                
class Products(BaseModel):
    store_id: int
    name: str
    description: str
    price: Decimal
    file_key: str
    image_1: str
    image_2: str
    image_3: str
@router.post("/products")
def create_store(data: Products, phone:str = Depends(get_current_user)):
    store_id = data.store_id
    name = data.name
    description = data.description
    price = data.price
    file_key = data.file_key
    image_1 = data.image_1
    image_2 = data.image_2
    image_3 = data.image_3
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM stores 
            WHERE id = %s
            AND owner_phone = %s
            """,
            (store_id, phone)
            )
            db_store = cursor.fetchone()
            if not db_store:
                return {"ok": False,
                    "message": "المتجر غير متوفر"}
            if price <= 0:
                return {"ok": False,
                    "message": "يجب ان يكون السعر اكبر من صفر"}
            
            
            if not name:
                return {"ok": False,
                    "message": "إسم المنتج مطلوب"}
            if not description:
                return {"ok": False,
                    "message": "الوصف مطلوب"}
            if len (description) > 100:
                return {"ok": False,
                    "message": "الوصف طويل للغاية"}
            if not image_1:
                return {
                "ok": False,
                    "message": "الصورة الأولى مطلوبة"}
            if not image_2:
                return {"ok": False,
                    "message": "الصورة الثانية مطلوبة "}
            if not image_3:
                return {"ok": False,
                    "message": "الصورة الثالثة مطلوبة "}
            if not file_key:
                return {"ok": False,
                    "message": "ملف المنتج مطلوب"}
            try:
                cursor.execute(
                """
                INSERT INTO products
                (store_id, name, description, price, file_key, image_1, image_2, image_3)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (store_id, name, description, price, file_key, image_1, image_2, image_3)
                )
                conn.commit()
                return {"ok": True,
                    "message": " تم إنشاء المنتج بنجاح"}
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ أثناء إنشاء المنتج"
                }
                
                
@router.get("/products")
def get_products():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT
            id,
            store_id,
            name,
            description,
            price,
            image_1,
            image_2,
            image_3
            FROM products
            ORDER BY created_at DESC
            """)
            products = cursor.fetchall()
            return {
               "ok": True,
               "products": products}
                   
                   
@router.get("/products/{product_id}")
def get_product(product_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT
            id,
            store_id,
            name,
            description,
            price,
            image_1,
            image_2,
            image_3
            FROM products
            WHERE id = %s
            """,
            (product_id,)
            )
            product = cursor.fetchone()
            if not product:
                return {"ok": False,
                    "message": "المنتج غير موجو"}
            return {
                "ok": True,
                "product": product
            }
            
@router.post("/products/{product_id}/purchase")
async def purchase_product(
    product_id: int,
    phone: str = Depends(get_current_user)
):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                id,
                store_id,
                price
                FROM products
                WHERE id = %s
                """,
                (product_id,)
            )

            product = cursor.fetchone()

            if not product:
                return {
                    "ok": False,
                    "message": "المنتج غير موجود"}
            price = product["price"]
            cursor.execute(
            """
            SELECT owner_phone
            FROM stores
            WHERE id = %s
            """,
            (product["store_id"],)
            )
            db_store = cursor.fetchone()
            if not db_store:
                return {
                "ok": False,
                    "message": "المتجر غير موجود"
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
            db_user = cursor.fetchone()
            if not db_user:
                return {"ok": False,
                    "message": "الحساب غير موجود"}
            if db_user["balance"] < price:
                return {"ok":False,
                    "message": "رصيدك غير كاف"}
                
            store_phone = db_store["owner_phone"]
            try:
                
                cursor.execute(
                """
                UPDATE usdt_balances
                SET balance = balance - %s
                WHERE phone = %s AND balance >= %s
                """,
                (price, phone, price)
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
                (price, admin_phone)
                )
                cursor.execute("""
                INSERT INTO transactions
                (user_phone, receiver_phone, type, network, amount, fee, net_amount, status)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """, 
                (phone, admin_phone, "purchase", "INTERNAL", price, 0, price, "pending")
                )
                transaction_id = cursor.fetchone()["id"]
                cursor.execute("""
                INSERT INTO purchases
                (buyer_phone, product_id, transaction_id, amount, status)
                VALUES(%s, %s, %s, %s, %s)
                """, (phone, product_id, transaction_id, price, "pending")
                )
                conn.commit()
                await send_balance(phone)
                await send_balance(admin_phone)
                return {
                    "ok": True,
                    "status": "pending",
                    "amount": price,
                    "fee": 0,
                    "type": "purchase",
                    "network": "INTERNAL",
                    "message": "جاري معالجة الشراء ..."
                    }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                "ok": False,
                    "message": "حدث خطأ أثناء عملية الشراء"}
                        

@router.get("/products/{product_id}/download")
async def download_pdf(
    product_id: int,
    phone: str = Depends(get_current_user)
):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM purchases
            WHERE buyer_phone = %s
            AND product_id = %s
            AND status = %s
            """, 
            (phone, product_id, "success"))
            purchase = cursor.fetchone()
            if not purchase:
                return {
                "ok": False,
                "message": "لم تملك صلاحية تحميل هذا المنتج"}
            cursor.execute(
            """
            SELECT file_key
            FROM products
            WHERE id = %s
            """, 
            (product_id,)
            )
            product = cursor.fetchone()
            if not product:
                return {
                "ok": False,
                    "message": "المنتج غير موجود"
                        }
            file_key = product["file_key"]
            return {
            "ok": True,
            "download_url": file_key }