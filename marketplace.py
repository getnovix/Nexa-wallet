#===============start=================
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from database import get_db
from auth import decode_token, get_current_user
from decimal import Decimal
from storage import upload_file, delete_file
from uuid import uuid4
from wallets import send_balance
router = APIRouter()

#===================== create store===========
@router.post("/store")
def create_store_request(
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    id_type: str = Form(...),
    id_number: str = Form(...),
    delivery_type: str = Form(...),
    store_image: UploadFile = File(...),
    owner_photo: UploadFile = File(...),
    id_document: UploadFile = File(...),
    phone: str = Depends(get_current_user)
):
    file_id = str(uuid4())
    store_image_key = f"stores/{file_id}/store_image"
    owner_photo_key = f"stores/{file_id}/owner_photo"
    id_document_key = f"stores/{file_id}/id_document"

    try:
        upload_file(store_image.file, store_image_key)
        upload_file(owner_photo.file, owner_photo_key)
        upload_file(id_document.file, id_document_key)
    except Exception as e:
        delete_file(store_image_key)
        raise HTTPException(status_code=500, detail="فشل رفع الصور")
        print(e)
        return {
            "ok": False,
            "message": "حدث خطأ أثناء فتح المتجر حاول مرة اخرى"
        }

    with get_db() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO marketplace_store_requests
                    (owner_phone, store_name, store_description, location, id_type, id_number, delivery_type, store_image, owner_photo, id_document)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, name, description, location, id_type, id_number, delivery_type, store_image_key, owner_photo_key, id_document_key)
                )
                conn.commit()
                return {
                    "ok": True,
                    "message": "جار معالجة الطلب ..."
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ يرجى المحاولة"
                }

#=============================================
#New Product Upgrade Path
#=============================================

@router.post("/marketplace/products")
def create_marketplace_product(
    name: str = Form(...),
    description: str = Form(...),
    price: Decimal = Form(...),
    quantity: int = Form(...),
    delivery_type: str = Form(...),
    image_1: UploadFile = File(...),
    image_2: UploadFile | None = File(None),
    image_3: UploadFile | None = File(None),
    phone: str = Depends(get_current_user)
):
    if price <= 0:
        return {
            "ok": False,
            "message": "السعر غير صالح"
        }
    if quantity <= 0:
        return {
            "ok": False,
            "message": "الكمية غير صالحة"
        }

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, status
                FROM marketplace_stores
                WHERE owner_phone = %s
                """,
                (phone,)
            )
            db_store = cursor.fetchone()

            if not db_store:
                return {
                    "ok": False,
                    "message": "المتجر غير موجود"
                }
            if db_store["status"] != "active":
                return {
                    "ok": False,
                    "message": "المتجر غير متاح بعد"
                }

            file_id = str(uuid4())

            image_1_key = f"products/{file_id}/image_1"
            image_2_key = f"products/{file_id}/image_2" if image_2 else None
            image_3_key = f"products/{file_id}/image_3" if image_3 else None

            try:
                upload_file(image_1.file, image_1_key)
                if image_2:
                    upload_file(image_2.file, image_2_key)
                if image_3:
                    upload_file(image_3.file, image_3_key)
            except Exception as e:
                print(e)
                return {
                    "ok": False,
                    "message": "حدث خطاء اثناء رفع المنتج"
                }

            try:
                cursor.execute(
                    """
                    INSERT INTO marketplace_products
                    (store_id, name, description, price, quantity, image_1, image_2, image_3, delivery_type)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                    """,
                    (db_store["id"], name, description, price, quantity, image_1_key, image_2_key, image_3_key, delivery_type)
                )
                product_db = cursor.fetchone()
                conn.commit()

                return {
                    "ok": True,
                    "message": "تم نشر المنتج بنجاح",
                    "product": {
                        "id": product_db["id"],
                        "name": name,
                        "description": description,
                        "price": float(price),
                        "quantity": quantity,
                        "delivery_type": delivery_type,
                        "created_at": product_db["created_at"],
                    }
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطاء اثناء رفع المنتج"
                }
@router.get("/marketplace/products")
def get_marketplace_products():
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT
            id,
            name,
            description,
            price,
            quantity,
            image_1,
            image_2,
            image_3,
            delivery_type,
            status,
            created_at
            FROM marketplace_products
            WHERE status = %s
            ORDER BY created_at DESC
            """,
            ("active",)
            )
            products = cursor.fetchall()
            return {
            "ok": True,
            "products": products}
    
    
@router.get("/marketplace/products/{product_id}")
def get_marketplace_product(product_id: int):
    with get_db()as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s
            """,
            (product_id,)
            )
            db_product = cursor.fetchone()
            if not db_product:
                return{"ok": False,
                    "message": "المنتج غير موجود"}
            if db_product["status"] != "active":
                return{"ok": False,
                    "message": "المنتج غير مشط حاليا"}
            return{"ok": True,
                "product": db_product}
                    
#=================================
#User basket
#==================================
@router.post("/marketplace/cart")
def add_product_to_cart(product_id: int, quantity: int,
phone: str = Depends(get_current_user)):
    if quantity <= 0:
        return {
        "ok": False,
        "message": "الكمية يجب أن تكون أكبر من صفر"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s           
            """,
            (product_id,)
            )
            db_product = cursor.fetchone()
            if not db_product:
                return{"ok": False,
                    "message": "المنتج غير موجود"}
            if db_product["status"] != "active":
                return{"ok": False,
                    "message": "المنتج غير متوفر بعد"}
            if quantity > db_product["quantity"]:
                return{"ok": False,
                    "message": f"الكمية غير متوفرة المتوفر فقط هو {db_product['quantity']}"}
            cursor.execute(
            """
            SELECT * 
            FROM cart_items
            WHERE user_phone = %s
            AND product_id = %s 
            """,
            (phone, product_id)
            )
            db_cart = cursor.fetchone()
            
            
            if db_cart:
                if db_cart["quantity"] + quantity > db_product["quantity"]:
                        return{"ok": False,
                            "message": "الكمية غير متوفرة!"}
                try:
                    cursor.execute(
                    """
                    UPDATE cart_items
                    SET quantity = quantity + %s
                    WHERE user_phone = %s
                    AND product_id = %s
                    """,
                    (quantity, phone, product_id)
                    )
                    conn.commit()
                    
                    return{"ok": True,
                        "message": f"تم إضافة كمية {quantity} بنجاح"}
                except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": f" تعذر إضاقة كمية {quantity} للمنتج"}
            else:
                try:
                    cursor.execute(
                    """
                    INSERT INTO cart_items
                    (user_phone, quantity, product_id)
                    VALUES(%s, %s, %s)
                    """,
                    (phone, quantity, product_id)
                    )
                    conn.commit()
                    return{"ok": True,
                        "message": "تمت إضاقة المنتج جديد"}
                except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": " تعذر إضافة المنتج الجديد"}
                
#====================================================
#Bring the basket products with all product details. 
#================/////===============================
@router.get("/marketplace/cart")
def get_cart(
    phone: str = Depends(get_current_user)
):
    with get_db() as conn:
        with conn.cursor()as cursor:
            cursor.execute(
            """
            SELECT
            cart_items.product_id,
            cart_items.quantity,
            marketplace_products.name,
            marketplace_products.price,
            marketplace_products.price * 
            cart_items.quantity AS item_total,
            marketplace_products.image_1,
            marketplace_products.image_2,
            marketplace_products.image_3
            FROM cart_items
            JOIN marketplace_products
            ON cart_items.product_id = marketplace_products.id
            WHERE cart_items.user_phone = %s
            """,
            (phone,)
            )
            cart = cursor.fetchall()
            cart_total = sum(item["item_total"] for item in cart)
            
            return {
            "ok": True,
            "cart": cart,
            "cart_total": cart_total}
                
#=========================×÷=///==========
#🛒 Adjust the quantity of a product in the cart 
#============================================
class UpdateCart(BaseModel):
    product_id: int
    quantity: int
@router.put("/marketplace/cart")
def update_cart(data: UpdateCart,
phone: str = Depends(get_current_user)):
    product_id = data.product_id
    quantity = data.quantity
    if quantity <= 0:
        return {
        "ok": False,
        "message": "الكمية يجب أن تكون أكبر من صفر"}
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_products
            WHERE id = %s
            """,
            (product_id,)
            )
            db_product = cursor.fetchone()
            if not db_product:
                return{"ok": False,
                    "message": "المنتج غير موجود"}
                    
            if db_product["status"] != "active":
                return {
                "ok": False,
                "message": "المنتج غير متوفر حاليا"}
                
            if quantity > db_product["quantity"]:
                return {
                "ok": False,
                "message": f"الكمية غير متوفرة، المتوفر فقط هو {db_product['quantity']}",
                'quantity': db_product['quantity']}
                    
            cursor.execute(
            """
            SELECT * 
            FROM cart_items
            WHERE product_id = %s
            AND user_phone = %s
            """,
            (product_id, phone)
            )
            db_cart = cursor.fetchone()
            if not db_cart:
                return{"ok": False,
                    "message": "المنتج غير موجود في السلة"}
            try:
                cursor.execute(
                """
                UPDATE cart_items
                SET quantity = %s
                WHERE id = %s
                AND user_phone = %s
                """,
                (quantity, db_cart["id"], phone)
                )
                conn.commit()
                return{"ok": True,
                    "message": "تم تعديل المنتج بنجاح"}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "تعذر تعديل كمية المنتج"}
#================================
#Delete product from user cart 
#================================
class Delete_product_Cart(BaseModel):
    product_id: int       
@router.delete("/marketplace/cart")
def delete_product_cart(data:Delete_product_Cart, 
phone: str = Depends(get_current_user)):
    product_id = data.product_id
    with get_db() as conn:
        with conn.cursor()as cursor:
            try:
                cursor.execute(
                """
                DELETE FROM cart_items
                WHERE product_id = %s
                AND user_phone = %s
                """,
                (product_id, phone)
                )
                if cursor.rowcount == 0:
                    return{"ok": False,
                        "message": "المنتج غير موجود"}
                conn.commit()
                return{"ok": True,
                    "message": "تم حذف المنتج بنجاح"}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "تعذر حزف المنتج "}
                        
                        
                        
                        
#=================================
#
#=================================
@router.post("/marketplace/checkout")
def marketplace_checkout(background_tasks: BackgroundTasks,
phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM usdt_balances
            WHERE phone = %s
            FOR UPDATE
            """,
            (phone,)
            )
            db_balance = cursor.fetchone()
            if not db_balance:
                return{"ok": False,
                    "message": "ليس لديك محفظة بعد"}
            cursor.execute(
            """
            SELECT
            cart_items.product_id,
            cart_items.quantity,
            marketplace_products.name,
            marketplace_products.price,
            marketplace_products.store_id,
            marketplace_products.quantity AS stock,
            marketplace_products.status
            FROM cart_items
            JOIN marketplace_products
            ON cart_items.product_id = marketplace_products.id
            WHERE cart_items.user_phone = %s
            """,
            (phone,)
            )
            db_cart = cursor.fetchall()
            if not db_cart:
                return{"ok": False,
                    "message": "السلة فارغة"}
            cursor.execute(
            """
            SELECT * 
            FROM users 
            WHERE phone = %s
            """,
            (phone,)
            )
            db_user = cursor.fetchone()
            buyer_name = db_user["name"]
            total = 0 
            store_totals = {}
            for item in db_cart:
                if item["status"] != "active":
                    return {"ok": False,
                        "message": "المنتج غير متوفر"}
                if item["quantity"] > item["stock"]:
                    return{"ok": False,
                        "message": " الكمية غير موجودة",
                            "stock": item["stock"]}
                total += item["price"] * item["quantity"]
                store_id = item["store_id"]
                item_total = item["price"] * item["quantity"]
                if store_id in store_totals:
                    store_totals[store_id] += item_total
                    
                else:
                    store_totals[store_id] = item_total
            if total > db_balance["balance"]:
                return{"ok": False,
                    "message": "رصيدك غير كاف",
                    "balance": db_balance["balance"]}
            try:
                cursor.execute(
                """
                UPDATE usdt_balances
                SET balance = balance - %s
                WHERE phone = %s
                AND balance >= %s
                """,
                (total, phone, total)
                )
                
                if cursor.rowcount == 0:
                    raise Exception("رصيدك غير كاف")
                
                for store_id, store_total in store_totals.items():
                    cursor.execute(
                    """
                    SELECT owner_phone
                    FROM marketplace_stores
                    WHERE id = %s
                    """,
                    (store_id,)
                    )
                    
                    db_store = cursor.fetchone()
                    
                    if not db_store:
                        raise Exception("المتجر غير موجود")
                        
                    seller_phone = db_store["owner_phone"]
                    
                    cursor.execute(
                    """
                    INSERT INTO marketplace_orders
                    (
                    buyer_phone, seller_phone, store_id, total)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (phone, seller_phone, store_id, store_total) )
                    order = cursor.fetchone()
                    order_id = order["id"]
                    cursor.execute("""
                    INSERT INTO transactions
                    (
                    user_phone,
                    receiver_phone,
                    type,
                    network,
                    amount,
                    fee,
                    net_amount,
                    status,
                    txid,
                    order_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                    phone,
                    seller_phone,
                    "marketplace_purchase",
                    "internal",
                    store_total,
                    0,
                    store_total,
                    "held",
                    None,
                    order_id
                    )
                    )
                    cursor.execute(
                    """
                    INSERT INTO marketplace_held_funds
                    (order_id, buyer_phone, seller_phone, amount)
                    VALUES(%s, %s, %s, %s)
                    """,
                    (order_id, phone, seller_phone, store_total)
                    )
                    for item in db_cart:
                        if item["store_id"] == store_id:
                            cursor.execute(
                            """
                            UPDATE marketplace_products
                            SET quantity = quantity - %s
                            WHERE id = %s
                            AND quantity >= %s
                            """,
                            (item["quantity"], item["product_id"], item["quantity"])
                            )
                            if cursor.rowcount == 0:
                                raise Exception("المنتج غير متوفر")
                            cursor.execute(
                            """
                            INSERT INTO marketplace_order_items
                            (order_id, product_id, quantity, price)
                            VALUES(%s, %s, %s, %s)
                            """,
                            (order_id, item["product_id"], item["quantity"], item["price"])
                            )
                            cursor.execute(
                            """
                            INSERT INTO notifications
                            (title, message, phone)
                            VALUES(%s,%s,%s)
                            """,
                            ('🔔 «طلب جديد»',
                            f"طلب جديد على المنتج: {item['name']} الكمية: ({item['quantity']}) المشتري: {buyer_name}", 
                            seller_phone)
                            )  
                cursor.execute(
                """
                DELETE FROM cart_items
                WHERE user_phone = %s
                 """,
                (phone,)
                )
                conn.commit()
                background_tasks.add_task(send_balance, phone)
                return{
                "ok": True,
                    "message": "تم إنشاء الطلب بنجاح"}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    if str(e) == "رصيدك غير كاف":
                        return{'ok': False,
                            'message': 'رصيدك غير كاف!',
                            'balance': db_balance['balance']}
                    return {
                    "ok": False,
                    "message": "تعذر إتمام العملية"}
                        
        
        
@router.get("/marketplace/orders")
def get_marketplace_orders(phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT
            marketplace_orders.id,
            marketplace_stores.name AS store_name,
            marketplace_orders.total,
            marketplace_orders.status,
            marketplace_orders.created_at
            FROM marketplace_orders
            JOIN marketplace_stores
            ON marketplace_orders.store_id = marketplace_stores.id
            WHERE marketplace_orders.buyer_phone = %s
            ORDER BY marketplace_orders.created_at DESC
            """, 
            (phone,))
            db_orders = cursor.fetchall()
            if not db_orders:
                return {
                "ok": False,
                "message": "لا توجد طلبات"}
            return {
            "ok": True,
            "orders": db_orders}
                
@router.get("/marketplace/orders/{order_id}")
def get_marketplace_order_details(
    order_id: int,
    phone: str = Depends(get_current_user)
):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT
            marketplace_orders.id,
            marketplace_stores.name AS store_name,
            marketplace_orders.total,
            marketplace_orders.status,
            marketplace_orders.created_at,
            
            marketplace_order_items.product_id,
            marketplace_order_items.quantity,
            marketplace_order_items.price,
            
            marketplace_products.name AS product_name
            
            FROM marketplace_orders
            
            JOIN marketplace_stores
            ON marketplace_orders.store_id = marketplace_stores.id
            
            JOIN marketplace_order_items
            ON marketplace_orders.id = marketplace_order_items.order_id
            
            JOIN marketplace_products
            ON marketplace_order_items.product_id = marketplace_products.id
            
            WHERE marketplace_orders.id = %s
            AND marketplace_orders.buyer_phone = %s
            
            ORDER BY marketplace_order_items.id
            """, 
            (order_id, phone))
            
            db_order = cursor.fetchall()
            if not db_order:
                return {
                    "ok": False,
                    "message": "الطلب غير موجود"}
            return {
                "ok": True,
                "order": db_order}
                    
# ======================================
#Nexa : تحويل حالة الطلب! 
#========================================
@router.patch("/marketplace/orders/{order_id}/seller-confirm")
def seller_confirm_order(order_id: int, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM marketplace_orders
            WHERE id = %s
            AND seller_phone = %s
            """,
            (order_id, phone)
            )
            db_order = cursor.fetchone()
            if not db_order:
                return{"ok": False,
                    "message": 'الطلب غير موجود'}
            if db_order["status"] != 'pending':
                return{'ok': False,
                    "message": 'الطلب لم يجهز بعد'}
            try:
                cursor.execute(
                """
                UPDATE marketplace_orders
                SET seller_confirmed = %s,
                status = %s
                WHERE id = %s 
                AND seller_phone = %s
                AND status = 'pending'
                """,
                (True, "processing", order_id, phone)
                )
                if cursor.rowcount == 0:
                    raise Exception('فشلت عملية التغيير')
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, phone)
                    VALUES(%s,%s,%s)
                    """,
                    ('🔔 «البائع قبل الطلب»',
                    f'البائع قبل طلبك رقم ({order_id}) وبدأ في تجهيزه.',
                    db_order["buyer_phone"])
                    )  
                conn.commit()
                return{'ok': True,
                    'message': 'تمت العملية بنجاح'}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "تعذر إتمام العملية"}
                        
#=============================
#Nexa : تحويل حالة طلب الانظار
#==============================
                        
@router.patch("/marketplace/orders/{order_id}/ship")   
def seller_ship_order(order_id: int, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_orders
            WHERE id = %s
            AND seller_phone = %s
            """,
            (order_id, phone)
            )
            db_order = cursor.fetchone()
            if not db_order:
                return{'ok': False,
                    'message': 'الطلب غير متوفر'}
            
            
            if db_order["status"] != 'processing':
                return{'ok': False,
                'message' :"لا يمكن شحن الطلب في حالته الحالية"}
            try:
                cursor.execute(
                """
                UPDATE marketplace_orders
                SET status = %s
                WHERE id = %s
                AND seller_phone = %s
                AND status = 'processing'
                """,
                ('shipped', order_id, phone)
                )
                if cursor.rowcount == 0:
                    raise Exception('فشلت عملية التغيير')
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, phone)
                    VALUES(%s,%s,%s)
                    """,
                    ('🔔 «تم شحن الطلب»',
                    f'تم شحن طلبك رقم ({order_id}) وهو في طريقه إليك.', 
                    db_order["buyer_phone"])
                    )  
                conn.commit()
                return{'ok' : True,
                    'message': 'نجحت عملية التغيير'}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "تعذر إتمام العملية"}
                        
            
            
@router.patch("/marketplace/orders/{order_id}/buyer-confirm")
def buyer_confirm_order(order_id: int, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT *
            FROM marketplace_orders
            WHERE id = %s
            AND buyer_phone = %s
            """,
            (order_id, phone)
            )
            db_buyer = cursor.fetchone()
            if not db_buyer:
                return{'ok': False,
                    "message": 'الطلب غير متوفر'}
            if db_buyer['status'] != 'shipped': 
                return{'ok': False,
                    'message':'لا يمكن تأكيد استلام الطلب في حالته الحالية'}
            try:
                cursor.execute(
                """
                UPDATE marketplace_orders
                SET status = %s,
                buyer_confirmed = %s,
                delivered_at = NOW()
                WHERE id = %s
                AND buyer_phone = %s
                AND status = 'shipped'
                """,
                ('delivered',True, order_id, phone)
                )
                if cursor.rowcount == 0:
                    raise Exception('فشلت عملية التغيير')
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (title, message, phone)
                    VALUES(%s,%s,%s)
                    """,
                    ('🔔 «المشتري أكد الاستلام»',
                    f'المشتري أكد استلام الطلب رقم ({order_id}).', 
                    db_buyer["seller_phone"])
                    )  
                conn.commit()
                return{'ok': True,
                    'message': 'تمت عملية التغيير بنجاح'}
            except Exception as e:
                    print(e)
                    conn.rollback()
                    return {
                    "ok": False,
                    "message": "تعذر إتمام العملية"}
                        
                    
    
@router.patch("/marketplace/orders/{order_id}/complete")
def complete_marketplace_order(background_tasks: BackgroundTasks,
order_id: int, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM marketplace_orders
            WHERE id = %s
            AND buyer_phone = %s
            FOR UPDATE
            """,
            (order_id, phone)
            )
            db_order = cursor.fetchone()
            if not db_order:
                return{"ok": False,
                    'message': 'الطلب غير موجود'}
            if db_order['status'] != 'delivered':
                return{'ok': False,
                    'message': 'الطلب غير جاهز بعد!'}
            
            cursor.execute(
            """
            SELECT * 
            FROM marketplace_held_funds
            WHERE order_id = %s
            AND status = %s
            FOR UPDATE
            """,
            (order_id, 'held')
            )
            db_held_fund = cursor.fetchone()
            if not db_held_fund:
                return{'ok': False,
                    'message': 'الأموال المحجوزة غير موجودة'}
            cursor.execute(
            """
            SELECT *
            FROM usdt_balances
            WHERE phone = %s
            FOR UPDATE
            """,
            (db_order["seller_phone"],)
            )
            db_balance = cursor.fetchone()
            if not db_balance:
                return{'ok': False,
                    'message': 'المحفظة غير نشطة تواصل مع الدعم'}
            try:
                cursor.execute(
                """
                UPDATE usdt_balances
                SET balance = balance + %s
                WHERE phone = %s
                """,
                (db_held_fund["amount"], db_order["seller_phone"])
                )
                if cursor.rowcount == 0:
                    raise Exception('فشلت إضافة الرصيد')
                cursor.execute(
                """
                UPDATE marketplace_held_funds
                SET status = %s,
                released_at = NOW()
                WHERE order_id = %s
                AND status = 'held'
                """,
                ('released', order_id)
                )
                if cursor.rowcount == 0:
                    raise Exception("فشل تحرير الأموال")
                cursor.execute(
                """
                UPDATE marketplace_orders
                SET status = %s
                WHERE id = %s
                AND status = %s
                AND buyer_phone = %s
                """,
                ('completed',order_id, 'delivered', phone))
                if cursor.rowcount == 0:
                    raise Exception('فشلت حالت تغيير الطلب الاخيرة')
                cursor.execute(
                """
                INSERT INTO transactions
                (
                user_phone,
                receiver_phone,
                type,
                network,
                amount,
                fee,
                net_amount,
                status,
                order_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                db_order["buyer_phone"],
                db_order["seller_phone"],
                "marketplace_release",
                "internal",
                db_held_fund["amount"],
                0,
                db_held_fund["amount"],
                "completed",
                order_id
                )
                )
                if cursor.rowcount != 1:
                    raise Exception("فشل تحديث معاملة الشراء")
                transaction_id = cursor.fetchone()["id"]
                cursor.execute("""
                UPDATE transactions
                SET status = %s
                WHERE order_id = %s
                AND type = %s
                AND status = %s
                """, 
                (
                "completed",
                order_id,
                "marketplace_purchase",
                "held"
                )
                )
                if cursor.rowcount != 1:
                    raise Exception("فشل تحديث معاملة الشراء")
                cursor.execute(
                """
                INSERT INTO notifications
                (title, message, phone)
                VALUES(%s,%s,%s)
                """,
                ('🔔 «تم تحرير الأموال»',
                f'تم تحرير مبلغ ({db_held_fund["amount"]}) من الطلب رقم ({order_id}) وإضافته إلى رصيدك.', 
                db_order["seller_phone"])
                )  
                conn.commit()
                background_tasks.add_task(send_balance, db_order["seller_phone"])
                return {
                "ok": True,
                "message": "تم إكمال عملية الشراء بنجاح",
                "transaction_id": transaction_id,
                "order_id": order_id,
                "amount": db_held_fund["amount"],
                "currency": "USDT",
                "status": "completed"
                }
                
            except Exception as e:
                print(e)    
                conn.rollback()
                return {
                "ok": False,
                "message": "تعذر إتمام الطلب"
                }
                    
                
@router.patch("/marketplace/orders/{order_id}/cancel")
def cancel_marketplace_order(background_tasks: BackgroundTasks,
order_id: int, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM marketplace_orders
            WHERE id = %s
            AND buyer_phone = %s
            FOR UPDATE
            """,
            (order_id, phone)
            )
            db_order = cursor.fetchone()
            if not db_order:
                return{'ok': False,
                    'message': 'الطلب غير متوفر'}
        
            if db_order['status'] != 'pending' and db_order['status'] != 'processing':
                return{'ok': False,
                'message': 'الطلب قيد التوصيل ولايمك إلقاؤه'}
            cursor.execute(
            """
            SELECT *
            FROM marketplace_held_funds
            WHERE order_id = %s
            AND status = 'held'
            FOR UPDATE
            """,
            (order_id, )
            )
            db_order_balance = cursor.fetchone()
            if not db_order_balance:
                return{'ok': False,
                    'message':'لا توجد أموال محجوزة لهذا الطلب'}
            amount = db_order_balance["amount"]
            cursor.execute(
            """
            SELECT *
            FROM usdt_balances 
            WHERE phone = %s 
            FOR UPDATE
            """,
            (phone,)
            )
            db_user_balance = cursor.fetchone()
            if not db_user_balance:
                return{'ok': False,
                    'message': 'محفظتك غسر نشطة تواصل مع الدعم!'}
            try:
                cursor.execute(
                """
                UPDATE usdt_balances
                SET balance = balance + %s
                WHERE phone = %s
                """,
                (db_order_balance['amount'], phone)
                )
                if cursor.rowcount == 0:
                    raise Exception("فشلت إعادة الأموال للمشتري")
                cursor.execute(
                """
                UPDATE marketplace_held_funds
                SET status = %s,
                refunded_at = NOW()
                WHERE order_id = %s
                AND status = 'held'
                """,
                ('refunded', order_id)
                )
                if cursor.rowcount == 0:
                    raise Exception("فشلت إعادة تعديل الجدول")
                cursor.execute("""
                UPDATE transactions
                SET status = %s
                WHERE order_id = %s
                AND type = %s
                AND status = %s
                """,
                (
                "refunded",
                order_id,
                "marketplace_purchase",
                "held"
                )
                )
                if cursor.rowcount == 0:
                    raise Exception("فشل تحديث معاملة الاسترجاع")
                cursor.execute(
                """
                SELECT product_id, quantity
                FROM marketplace_order_items
                WHERE order_id = %s
                """,
                (order_id,)
                )
                order_items = cursor.fetchall()
                for item in order_items:
                    cursor.execute(
                    """
                    UPDATE marketplace_products
                    SET quantity = quantity + %s
                    WHERE id = %s
                    """,
                    (item["quantity"], item["product_id"])
                    )
                cursor.execute(
                """
                UPDATE marketplace_orders
                SET status = %s
                WHERE id = %s 
                AND buyer_phone = %s
                AND status IN ('pending', 'processing')
                """,
                ('cancelled', order_id, phone)
                )
                if cursor.rowcount == 0:
                    raise Exception('فشل تعديل جدول الطلب')
                cursor.execute(
                """
                INSERT INTO notifications
                (title, message, phone)
                VALUES(%s,%s,%s)
                """,
                (
                "🔔 «تم إلغاء الطلب»",
                f"تم إلغاء طلبك رقم ({order_id}) وإرجاع مبلغ ({amount}) إلى رصيدك.",
                db_order["buyer_phone"]
                )
                )
                conn.commit()
                background_tasks.add_task(send_balance, db_order["buyer_phone"])
                return{'ok': True,
                    'message': 'تم إلغاء عملية الشراء بنجاح'}
            except Exception as e:
                    print(e)
                    
                    conn.rollback()
                    if str(e) == 'فشل تعديل جدول الطلب':
                        return{'ok': False,
                            'message': 'تعذر إتمام طلب المنتج'}
                                
                    return{'ok': False,
                        'message': 'تعذر إتمام عملية إضافة الرصيد'}