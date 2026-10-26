from pydantic import BaseModel
from fastapi import APIRouter
from auth import get_current_user
from validators import *
from fastapi import Depends
from database import get_db
import qrcode
from io import BytesIO
from PIL import Image
from fastapi.responses import StreamingResponse
router = APIRouter()


@router.get("/profile")
def profile(phone: str = Depends(get_current_user)):
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
                return {
                    "ok": False,
                    "message": "الحساب غير موجود"
                }
            name = db_user["name"]
            user_phone = db_user["phone"]
            email = db_user["email"]

            cursor.execute(
                """
                SELECT *
                FROM usdt_balances
                WHERE phone = %s
                """,
                (phone,)
            )
            db_balance = cursor.fetchone()
            if not db_balance:
                return {
                    "ok": False,
                    "message": "لايوجد محفظة لديك بعد"
                }
            balance = db_balance["balance"]

    return {
        "ok": True,
        "name": name,
        "phone": user_phone,
        "email": email,
        "balance": balance
    }


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


@router.put("/change-password")
def change_password(password: ChangePassword, phone: str = Depends(get_current_user)):
    old_password = password.old_password
    new_password = password.new_password
    error = validate_password(new_password)
    if error:
        return {
            "ok": False,
            "message": error
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
                return {
                    "ok": False,
                    "message": "الحساب غير موجود"
                }
            if not verify_password(old_password, db_user["password"]):
                return {
                    "ok": False,
                    "message": "كلمة المرور القديمة غير صحيحة"
                }
            if verify_password(new_password, db_user["password"]):
                return {
                    "ok": False,
                    "message": "كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة"
                }

            try:
                new_password = hash_password(new_password)
                cursor.execute(
                    """
                    UPDATE users
                    SET password = %s
                    WHERE phone = %s
                    """,
                    (new_password, phone)
                )

                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": "فشل تغيير كلمة المرور"
                    }

                message = "لقد تم تغيير كلمة مرور هذا الحساب"
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s ,%s, %s)
                    """,
                    (phone, "تم تغيير كلمة مرور حسابك بنجاح", message)
                )
                conn.commit()
                return {
                    "ok": True,
                    "message": "تم تغيير كلمة المرور بنجاح"
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطاء حاول مجددآ"
                }


class ChangeEmail(BaseModel):
    email: str
    password: str


@router.put("/change-email")
def change_email(change_email: ChangeEmail, phone: str = Depends(get_current_user)):
    password = change_email.password
    email = change_email.email
    if not password:
        return {
            "ok": False,
            "message": "كلمة المرور مطلوبة "
        }
    error_email = validate_email(email)
    if error_email:
        return {
            "ok": False,
            "message": error_email
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
                return {
                    "ok": False,
                    "message": "الحساب غير موجود "
                }
            if not verify_password(password, db_user["password"]):
                return {
                    "ok": False,
                    "message": "كلمة المرور غير صحيحة"
                }

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            db_user_email = cursor.fetchone()
            if db_user_email:
                return {
                    "ok": False,
                    "message": "هذا البريد مستخدم بالفعل"
                }

            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET email = %s
                    WHERE phone = %s
                    """,
                    (email, phone)
                )

                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": "فشل تغيير البريد الإلكتروني"
                    }

                message = "تم تغيير الإيميل الخاص بالحساب"
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s ,%s, %s)
                    """,
                    (phone, "تم تغيير البريد بنجاح", message)
                )
                conn.commit()
                return {
                    "ok": True,
                    "message": "تم تغيير الايميل الخاص بك بنجاح"
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطاء اثناء تغيير الايميل الخاص بك يرجى المحاولة "
                }


class ChangeName(BaseModel):
    name: str
    password: str


@router.put("/change-name")
def change_name(change_name: ChangeName, phone: str = Depends(get_current_user)):
    name = change_name.name
    password = change_name.password
    if not password:
        return {
            "ok": False,
            "message": "كلمة المرور مطلوبة "
        }
    error = validate_name(name)
    if error:
        return {
            "ok": False,
            "message": error
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
                return {
                    "ok": False,
                    "message": "الحساب غير موجود "
                }
            if not verify_password(password, db_user["password"]):
                return {
                    "ok": False,
                    "message": "كلمة المرور غير صحيحة"
                }
            if name == db_user["name"]:
                return {
                    "ok": False,
                    "message": "يجب ان يكون الاسم الجديد مختلف عن القديم"
                }

            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET name = %s
                    WHERE phone = %s
                    """,
                    (name, phone)
                )

                if cursor.rowcount == 0:
                    conn.rollback()
                    return {
                        "ok": False,
                        "message": "فشل تغيير الاسم"
                    }

                message = "تم تغيير إسم المستخدم الخاص بك بنجاح"
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES(%s, %s, %s)
                    """,
                    (phone, "تم تغيير إسم المستخدم الخاص بك بنجاح", message)
                )
                conn.commit()
                return {
                    "ok": True,
                    "message": "تم تغيير الاسم بنجاح"
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ أثناء تغيير الاسم"
                }


@router.get("/profile/qr")
def profile_qr(phone: str = Depends(get_current_user)):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(phone)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white",
    ).convert("RGBA")

    logo = Image.open("assets/nexa_logo.png").convert("RGBA")

    # حجم الشعار: 20% من عرض الـQR
    logo_size = qr_image.width // 5
    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

    # وضع الشعار في المنتصف
    x = (qr_image.width - logo.width) // 2
    y = (qr_image.height - logo.height) // 2

    qr_image.alpha_composite(logo, (x, y))

    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store"
        }
    )