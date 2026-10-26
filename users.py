from fastapi import APIRouter
from pydantic import BaseModel
from auth import create_token
from validators import *
from database import get_db
from config import SUPPORTED_TOKENS, admin_phone
import secrets

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: str
    password: str


@router.post("/register")
def register(user: RegisterRequest):
    name = user.name
    phone = user.phone
    email = user.email
    password = user.password

    if phone == admin_phone:
        return {
            "ok": False,
            "message": "رقم الهاتف غير متاح."
        }

    error = validate_password(password)
    if error:
        return {
            "ok": False,
            "message": error
        }
    if not phone.isdigit():
        return {
            "ok": False,
            "message": "رقم الهاتف يجب أن يحتوي على أرقام فقط"
        }
    if not phone.startswith("09"):
        return {
            "ok": False,
            "message": "رقم الهاتف غير صحيح"
        }
    if len(phone) != 10:
        return {
            "ok": False,
            "message": "رقم الهاتف يجب أن يكون 10 أرقام"
        }
    error_email = validate_email(email)
    if error_email:
        return{"ok": False,
            "message": error_email}
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
            if db_user:
                return {
                    "ok": False,
                    "message": "الحساب موجود بالفعل"
                }

            otp = ''.join(secrets.choice("0123456789") for _ in range(6))
            print(otp)

            try:
                password = hash_password(password)
                cursor.execute(
                    """
                    INSERT INTO users
                    (phone, name, email, password, email_otp)
                    VALUES(%s, %s, %s, %s, %s)
                    """,
                    (phone, name, email, password, otp)
                )
                cursor.execute(
                    """
                    INSERT INTO usdt_balances
                    (phone, balance)
                    VALUES(%s, %s)
                    """,
                    (phone, 0)
                )
                for network, currency in SUPPORTED_TOKENS:
                    cursor.execute(
                        """
                        INSERT INTO balance_tokens
                        (phone, network, currency, balance)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (phone, network, currency, 0)
                    )

                message = "سعداء بانضمامك إلى Nexa Wallet، نتمنى لك تجربة آمنة وسهلة معنا."
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (phone, title, message)
                    VALUES (%s, %s, %s)
                    """,
                    (phone, "مرحباً بك في Nexa Wallet", message)
                )
                conn.commit()
                token = create_token(phone)
                return {
                    "ok": True,
                    "token": token,
                    "message": "تم انشاء الحساب بنجاح"
                }
            except Exception as e:
                print(e)
                conn.rollback()
                return {
                    "ok": False,
                    "message": "حدث خطأ عند انشاء الحساب"
                }


class LoginRequest(BaseModel):
    phone: str
    password: str


@router.post("/login")
def login(user: LoginRequest):
    phone = user.phone
    password = user.password

    if not password:
        return {
            "ok": False,
            "message": "كلمة المرور مطلوبة"
        }
    if not phone.isdigit():
        return {
            "ok": False,
            "message": "رقم الهاتف يجب أن يحتوي على أرقام فقط"
        }
    if not phone.startswith("09"):
        return {
            "ok": False,
            "message": "رقم الهاتف غير صحيح"
        }
    if len(phone) != 10:
        return {
            "ok": False,
            "message": "رقم الهاتف يجب أن يكون 10 أرقام"
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
            if not verify_password(password, db_user["password"]):
                return {
                    "ok": False,
                    "message": "كلمة المرور غير صحيحة"
                }

    token = create_token(phone)
    return {
        "ok": True,
        "token": token,
        "message": "تم تسجيل الدخول بنجاح"
    }
