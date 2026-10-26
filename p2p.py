print('I,M master robot')
#===============start=================
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from database import get_db
from auth import decode_token, get_current_user
from decimal import Decimal
from storage import upload_file, delete_file
from uuid import uuid4
from wallets import send_balance
from validators import validate_name
from psycopg.types.json import Jsonb
router = APIRouter(
prefix="/p2p",
    tags=["p2p"]
    )
PAYMENT_METHODS = {
    "bankak": "بنكك",
    "fawry": "فوري",
    "mycashi": "ماي كاشي",
    "bravo": "برافو",
    "ocash": "أوكاش",
    "momo": "موMo",
    "sudanpay": "سودان باي",
    "zikher": "زِخِر",
    "sah": "SAH",
    "bede": "بيدي",
    "nilpay": "نيل باي",
    "amin_plus": "أمين بلس",
    "mashreq": "مشرق",
    "albaraka": "البركة",
    "yallapay": "يلا باي",
    "ritapay": "ريتا باي",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024 
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 20_000_000


def validate_image_upload(upload: UploadFile, field_name: str) -> None:
    if upload is None or not upload.filename:
        raise HTTPException(status_code=400, detail=f"يجب رفع {field_name}")

    upload.file.seek(0)
    content = upload.file.read(MAX_IMAGE_SIZE + 1)
    upload.file.seek(0)

    if not content:
        raise HTTPException(status_code=400, detail=f"ملف {field_name} فارغ")

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"حجم {field_name} يتجاوز 5 MB"
        )

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail=f"صيغة {field_name} غير مدعومة"
                )

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=400,
                    detail=f"أبعاد {field_name} كبيرة جدًا"
                )

            image.verify()

    except HTTPException:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError
    ):
        raise HTTPException(
            status_code=400,
            detail=f"ملف {field_name} ليس صورة سليمة أو أن الصورة تالفة"
        )

#==============
# create.p2p
#==============
@router.post("/merchant/apply")
def create_p2p(
    name: str = Form(...),
    country: str = Form(...),
    ID_type: str = Form(...),
    ID_document_number: str = Form(...),
    id_photo: UploadFile = File(...),
    Personal_photo: UploadFile = File(...),
    Experience_in_P2P_trading: int = Form(...),
    Expected_daily_trading_volume: int = Form(...),
    Agreement_to_the_terms: str = Form(...),
    phone: str = Depends(get_current_user)
):
    if Agreement_to_the_terms != "True":
        return{"ok": False,
            "message": "يجب الموافقة على الشروط والأحكام"}
    if not name:
        return {
            "ok": False,
            "message": "يجب إدخال الاسم الخاص بك"
        }
    error_name = validate_name(name)
    if error_name:
        return{"ok": False,
            "message": error_name}

    if not country:
        return {
            "ok": False,
            "message": "يجب توفير بلد التاجر الخاصة بك"
        }

    if len(ID_document_number) < 9:
        return {
            "ok": False,
            "message": "رقم الهوية غير صحيح"
        }
    if Experience_in_P2P_trading <= 0:
        return{"ok": False,
            "message": "لايعجوز خبرة صفر p2p وتقديم طلب تاحر"}
    validate_image_upload(id_photo, "صورة الهوية الشخصية")
    validate_image_upload(Personal_photo, "الصورة الشخصية")

    if Expected_daily_trading_volume <=0:
        return{"ok": False,
            "message": "هذا الرقم قليل جدآ" }
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM p2p_merchant_applications
            WHERE user_phone = %s
            """,
            (phone,)
            )
            db_user = cursor.fetchone()
            if not db_user:
                file_id = str(uuid4())
                id_photo_key = f"p2p/{file_id}/id_photo"
                Personal_photo_key = f"p2p/{file_id}/Personal_photo"
                
                uploaded_keys = []
                try:
                    upload_file(Personal_photo, Personal_photo_key)
                    uploaded_keys.append(Personal_photo_key)
                    
                    upload_file(id_photo, id_photo_key)
                    uploaded_keys.append(id_photo_key)
                    cursor.execute(
                    """
                    INSERT INTO p2p_merchant_applications
                    (user_phone, full_name, country, id_type, id_document_number,  id_photo_key, personal_photo_key, experience, expected_daily_volume, terms_accepted)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, name, country, ID_type, ID_document_number, id_photo_key, Personal_photo_key, Experience_in_P2P_trading, Expected_daily_trading_volume, True)
                    )
                    title = f"تم استلام طلب التسجيل كتاجر P2P"

                    message = f" مرحبًا {name}، تم استلام طلبك للتسجيل كتاجر في خدمة P2P بنجاح، وهو الآن قيد المراجعة من فريق Nexa. سنُطلعك على نتيجة المراجعة فور الانتهاء منها. شكرًا لاهتمامك بالانضمام إلينا."
                    cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title,message)
                    VALUES(%s, %s, %s)
                    """,
                    (phone, title, message)
                    )
                    conn.commit()
                    return{"ok": True,
                        "message": "تم إرسال طلب تاحر p2p بنجاح"}
                except Exception as e:
                    conn.rollback()
                    
                    for key in uploaded_keys:
                        try:
                            delete_file(key)
                        except Exception as cleanup_error:
                            print(f' فشل {cleanup_error}')
                    return{"ok": False, 'message': "فشلت عملية تقديم الطلب"}
                    
                
                
            if db_user["status"] == "under_review":
                return{"ok": False,
                    "message": "الطلب قيد المراجعة..."}
            if db_user["status"] == "pending":
                return{"ok": False,
                    "message": "الطلب بانتظار المراجعة..."}
            if db_user["status"] == "rejected":
                file_id = str(uuid4())
                id_photo_key = f"p2p/{file_id}/id_photo"
                Personal_photo_key = f"p2p/{file_id}/Personal_photo"                
                
                uploaded_keys = []
                try:
                    upload_file(Personal_photo, Personal_photo_key)
                    uploaded_keys.append(Personal_photo_key)
                    
                    upload_file(id_photo, id_photo_key)
                    uploaded_keys.append(id_photo_key)
                    title = f"تم استلام طلبك مجددًا"
                    message = f"مرحبًا {name}، تم استلام طلبك مجددًا للتسجيل كتاجر في خدمة P2P بعد تحديث بياناتك. طلبك الآن قيد المراجعة من فريق Nexa، وسنُشعرك بالنتيجة فور الانتهاء من مراجعته."
                    cursor.execute(
                    """
                    UPDATE p2p_merchant_applications
                    SET full_name = %s,
                    terms_accepted = %s,
                    expected_daily_volume = %s,
                    experience = %s,
                    personal_photo_key = %s,
                    id_photo_key = %s,
                    id_document_number = %s,
                    id_type = %s,
                    country = %s,
                    status = %s
                    WHERE user_phone = %s
                    """,
                    (name, True, Expected_daily_trading_volume, Experience_in_P2P_trading, Personal_photo_key, id_photo_key, ID_document_number, ID_type, country, "pending", phone)
                    )
                    cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s, %s, %s)
                    """,
                    (phone, title,message)
                    )
                    conn.commit()
                    return{"ok": True,
                        "message": "تمت إعادة إرسال طلب تاجر p2p بنجاح"}
                except Exception as e:
                    conn.rollback()
                    for key in uploaded_keys:
                        try:
                            delete_file(key)
                        except Exception as cleanup_error:
                            pass
                    return{'ok': False, 'message': "فشلت عملية تقديم الطلب"}
                    
            if db_user["status"] == "approved":
                return{"ok": False,
                    "message": "أنت تاحر بالفعل"}
            
            
#=========================
#Nexa: مسار إنشأ إعلان بيع USDT 
#=========================
class P2PAdCreate(BaseModel):
    trade_type: str
    price: Decimal
    min_amount: Decimal
    max_amount: Decimal
    available_amount: Decimal
    payment_methods: list[str]
    terms: str
@router.post("/ads/sell")
def create_p2p_ad(background_tasks: BackgroundTasks, p2p: P2PAdCreate, phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT * 
            FROM p2p_merchant_applications
            WHERE user_phone = %s
            """,
            (phone,)
            )
            db_p2p = cursor.fetchone()
            if not db_p2p:
                return{"ok": False,
                    "message": "عذرا انت لست تاجر معتمد في p2p"}
            if db_p2p["status"] == "pending":
                return{"ok": False,
                    "message": "طلب قيد المراجعة لست تاجر بعد"}
            if db_p2p["status"] != "approved": 
                return{"ok": False,
                    "message": "عذرآ هذا القسم يخص تجار p2p فقط"}
                        
            if p2p.trade_type != "sell":
                return{"ok": False, "message": "خيار غير متوفر"}
            if p2p.price <= 0:
                return{"ok": False,"message": "يجب ام يكون المبلغ اكبى من صفر "}
            if p2p.min_amount <=0:
                return{"ok": False, "message": "يجب ان يكون المبلغ اكبر من صفر"}
            if p2p.max_amount < p2p.min_amount:
                return{"ok": False, "message": f"يجب ام يكون اكبر من {p2p.min_amount}"}
            if p2p.available_amount <= 0:
                return{"ok": False, "message": "يجب تكون كمية USDT اكبر من صفر"}
            cursor.execute(
            """
            SELECT balance
            FROM usdt_balances
            WHERE phone = %s
            FOR UPDATE
            """,
            (phone,)
            )
            db_balance_rwo = cursor.fetchone()
            if not db_balance_rwo:
                return{"ok": False, "message": "ليس لديك محفظة بعد تواصل مع الدعم"}
            if p2p.available_amount > db_balance_rwo["balance"]:
                return{"ok": False, "message": "رصيدك غير كاف لهذا العرض","balance": db_balance_rwo["balance"]}
            if not p2p.payment_methods:
                return {"ok": False, "message": "يجب اختيار طريقة دفع واحدة على الأقل"}
            for method in p2p.payment_methods:
                if method not in PAYMENT_METHODS:
                    return {"ok": False, "message": f"طريقة الدفع {method} غير مدعومة"}
            if len(p2p.payment_methods) != len(set(p2p.payment_methods)):
                return {"ok": False, "message": "لا يمكن تكرار طريقة الدفع"}
            if p2p.max_amount > p2p.available_amount:
                return{"ok": False, "message": "أكبر صفقة لا يمكن أن تتجاوز الكمية المتاحة"}
            if p2p.min_amount > p2p.available_amount:
                return{"ok": False, "message": "أصغر صفقة لايمكن ان تتجاوز الكمية المتاحة"}
            if not p2p.terms.strip():
                return{"ok": False,"message": "يجب ان تضع شروطك الخاصو "}
            title = "تم إنشاء إعلان P2P"
            message = "«تم إنشاء إعلانك في Nexa P2P بنجاح، وأصبح متاحًا للمستخدمين.»"
            try:
                
                cursor.execute(
                """
                INSERT INTO p2p_ads
                (merchant_phone, trade_type, fiat_currency, price, min_amount, max_amount, available_amount, payment_methods, status, terms)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (phone, p2p.trade_type, "SDG", p2p.price, p2p.min_amount, p2p.max_amount, p2p.available_amount, Jsonb(p2p.payment_methods), 'active', p2p.terms)
                )
                ad = cursor.fetchone()
                ad_id = ad["id"]
                created_at = ad["created_at"]
                cursor.execute(
                """
                INSERT INTO notifications
                (phone, title, message)
                VALUES(%s, %s, %s)
                """,
                (phone,title, message)
                )
                cursor.execute(
                """
                UPDATE usdt_balances
                SET balance = balance - %s
                WHERE phone = %s
                AND balance >= %s
                """,
                (p2p.available_amount, phone, p2p.available_amount)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                    "ok": False, "message": "رصيدك غير كاف لهذا الإعلان"}
                cursor.execute(
                """
                INSERT INTO p2p_ad_reservations
                (merchant_phone, amount, status, ad_id)
                VALUES(%s, %s, %s, %s)
                """,
                (phone, p2p.available_amount, "active", ad_id)
                )
                cursor.execute(
                """
                INSERT INTO transactions
                (user_phone, receiver_phone, type, network, amount,
                fee, net_amount, status, txid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (phone, None, "p2p_reservation", "Nexa", p2p.available_amount, 0, p2p.available_amount, "completed", f"p2p_ad_{ad_id}",
                )
                )

                conn.commit()
                
            except Exception as e:
                conn.rollback()
                print(e)
                return{"ok": False,"message": "تعذر نشر الإعلان"}
            try:
                background_tasks.add_task(send_balance, phone)
                return{"ok": True,"message": "تم إنشاء الإعلان بنجاح",
                    "id": ad_id, "trade_type": p2p.trade_type, 
                    "price": p2p.price, "min_amount": p2p.min_amount,
                    "max_amount": p2p.max_amount, "available_amount": p2p.available_amount,
                    "payment_methods": p2p.payment_methods, "status": "active", "terms": p2p.terms, "created_at": created_at}
            except Exception as e:
                
                print(f"خطأ جديد في p2p.py السطر 402 الخطاء هز {e}")
                return{"ok": True, "message": "تم نشر الإعلان بنجاح"}
                    
                    

@router.post("/ads/buy")
def create_buy_ad(
    p2p: P2PAdCreate,
    phone: str = Depends(get_current_user)
):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT status
            FROM p2p_merchant_applications
            WHERE user_phone = %s
            """,
            (phone,)
            )
            merchant = cursor.fetchone()
            if not merchant or merchant["status"] != "approved":
                return{"ok": False, "message": "هذا المسار مخصص للتجار المعتمدين فقط" }
            if p2p.trade_type != "buy":
                return{'ok': False, 'message': "هذا القسم مخصص لإعلانات شراء USDT فقط"}
            if p2p.price <= 0:
                return{"ok": False,'message': "سعر الشراء يجب أن يكون أكبر من صفر"}

            if p2p.min_amount <= 0:
                return{'ok': False, 'message': "الحد الأدنى يجب أن يكون أكبر من صفر"}

            if p2p.max_amount < p2p.min_amount:
                return{'ok': False,
                    'message': "الحد الأعلى يجب ألا يقل عن الحد الأدنى"}

            if p2p.available_amount <= 0:
                return{'ok': False,
                    'message': "كمية USDT المطلوبة يجب أن تكون أكبر من صفر"}

            if p2p.max_amount > p2p.available_amount:
                return{'ok': False,
                    'message': "الحد الأعلى للصفقة يتجاوز الكمية المطلوبة"}

            if not p2p.payment_methods:
                return{'ok': False,
                    'message': "اختر طريقة دفع واحدة على الأقل"}

            for method in p2p.payment_methods:
                if method not in PAYMENT_METHODS:
                    return{'ok': False,
                        'message':f"طريقة الدفع {method} غير مدعومة"}

            if len(p2p.payment_methods) != len(set(p2p.payment_methods)):
                return{'ok': False,
                    'message': "لا يمكن تكرار طريقة الدفع"}

            if not p2p.terms.strip():
                return{'ok': False,
                    'message': "يجب إدخال شروط الإعلان"}

            cursor.execute(
            """
            INSERT INTO p2p_ads (
            merchant_phone, trade_type,fiat_currency,
            price,min_amount,max_amount,available_amount,
            payment_methods,status,terms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (phone,"buy","SDG",p2p.price,p2p.min_amount,p2p.max_amount,p2p.available_amount,
            Jsonb(p2p.payment_methods),"active",p2p.terms.strip()
            )
            )

            ad = cursor.fetchone()
            cursor.execute(
            """
            INSERT INTO notifications (phone, title, message)
            VALUES (%s, %s, %s)
            """,
            (
            phone,
            "تم إنشاء إعلان شراء USDT",
            "تم نشر إعلان شراء USDT بنجاح وأصبح متاحًا للمستخدمين."              
            )
            conn.commit()
            return {
                "ok": True,
                "message": "تم نشر إعلان شراء USDT بنجاح",
                "id": ad["id"],
                "trade_type": "buy",
                "price": p2p.price,
                "min_amount": p2p.min_amount,
                "max_amount": p2p.max_amount,
                "available_amount": p2p.available_amount,
                "payment_methods": p2p.payment_methods,
                "status": "active",
                "terms": p2p.terms.strip(),
                "created_at": ad["created_at"]
                }

                
@router.get("/ads")
def get_p2p_ads(phone: str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT
            a.id, a.trade_type, a.asset, a.fiat_currency, a.price, a.min_amount,
            a.max_amount, a.available_amount, a.payment_methods,  a.terms, a.created_at
            FROM p2p_ads AS a
            WHERE a.status = %s
            AND a.available_amount > %s
            AND EXISTS (
            SELECT 1
            FROM p2p_merchant_applications AS m
            WHERE m.user_phone = a.merchant_phone
            AND m.status = %s
            )
            """,
            ("active", 0, "approved")
            )
            db_p2p = cursor.fetchall()
            if not db_p2p:
                return { "ok": True, "buy": [], "sell": []}
            buy_ads = []
            sell_ads = []

            for ad in db_p2p:
                ad_data = {
                    "id": ad["id"],
                    "trade_type": ad["trade_type"],
                    "asset": ad["asset"],
                    "fiat_currency": ad["fiat_currency"],
                    "price": ad["price"],
                    "min_amount": ad["min_amount"],
                    "max_amount": ad["max_amount"],
                    "available_amount": ad["available_amount"],
                    "payment_methods": ad["payment_methods"],
                    "terms": ad["terms"],
                    "created_at": ad["created_at"]
                }

                if ad["trade_type"] == "buy":
                    buy_ads.append(ad_data)

                elif ad["trade_type"] == "sell":
                    sell_ads.append(ad_data)
            return {"ok": True,"buy": buy_ads, "sell": sell_ads }
                
#
@router.get("/ads/{ad_id}")
def get_ads(ad_id: int , phone:str = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
            """
            SELECT
            id,
            trade_type,
            asset,
            fiat_currency,
            price,
            min_amount,
            max_amount,
            available_amount,
            payment_methods,
            terms,
            created_at
            FROM p2p_ads
            WHERE id = %s
            AND status = %s
            AND available_amount > %s
            AND EXISTS (
            SELECT 1
            FROM p2p_merchant_applications AS m
            WHERE m.user_phone = p2p_ads.merchant_phone
            AND m.status = %s
            )
            """,
            (ad_id, "active", 0, "approved")
            )
            db_p2p = cursor.fetchone()
            if not db_p2p:
                return{"ok": False, "message": "الإعلان غيى موجود"}
            return{"ok": True, "db_p2p": db_p2p}
            
class P2POrderCreate(BaseModel):
    amount: Decimal
@router.post("/orders/buy/{ad_id}")
def p2p_orders(amount:P2POrderCreate, ad_id: int, phone: str = Depends(get_current_user)):
    amount = amount.amount
    
    
    
    
@router.post("/orders/sell/{ad_id}")
pass
    