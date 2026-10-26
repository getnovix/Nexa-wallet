from datetime import datetime, timedelta

from fastapi import Header, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError

from config import SECRET_KEY, ALGORITHM


def create_token(phone: str):
    expire = datetime.utcnow() + timedelta(days=7)

    payload = {
        "phone": phone,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        phone = payload.get("phone")

        if not phone:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )

        return phone

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


def get_current_user(Authorization: str = Header(...)):
    if not Authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )

    parts = Authorization.strip().split()

    if len(parts) != 2:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header"
        )

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Authorization type must be Bearer"
        )

    return decode_token(token)
    
    
# في ملف auth.py عند إنشاء التوكن للأدمن:
def create_admin_token(phone: str):
    payload = {
        "phone": phone,
        "role": "admin", # إضافة الصلاحية داخل التوكن المشفر
        "exp": datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#
# في ملف admin.py داخل الدوال الحساسة (مثال الـ dashboard):
#@router.get("/admin/dashboard")
#def dashboard(dependencies = Depends(get_current_user_payload)):
    # هنا نفك التوكن ونفحص الـ role المشفر جواه اللي مستحيل يتزور
#    if dependencies.get("role") != "admin":
#        return {
#            "ok": False,
#            "message": "ليس لديك صلاحية الوصول، هذه المنطقة للأدمن فقط"
#        }
