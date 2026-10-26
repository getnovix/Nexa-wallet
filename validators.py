def validate_password(password):
    if not password:
        return "كلمة المرور مطلوبة"

    if not password.strip():
        return "لا يمكن أن تكون كلمة المرور فارغة"

    if len(password) < 8:
        return "يجب أن تكون كلمة المرور 8 أحرف على الأقل"

    if not any(c.isupper() for c in password):
        return "يجب أن تحتوي على حرف كبير"

    if not any(c.islower() for c in password):
        return "يجب أن تحتوي على حرف صغير"

    if not any(c.isdigit() for c in password):
        return "يجب أن تحتوي على رقم"

    if not any(not c.isalnum() for c in password):
        return "يجب أن تحتوي على رمز خاص"

    return None
def validate_email(email):
    if not email:
        return "البريد الإلكتروني مطلوب"

    email = email.strip()

    if not email:
        return "لا يمكن أن يكون البريد الإلكتروني فارغًا"

    if "@" not in email:
        return "البريد الإلكتروني غير صالح"

    if "." not in email:
        return "البريد الإلكتروني غير صالح"

    if len(email) > 254:
        return "البريد الإلكتروني طويل جدًا"

    return None
    
    
import re

def validate_name(name):
    if not name:
        return "الاسم مطلوب"

    name = name.strip()

    if not name:
        return "لا يمكن أن يكون الاسم فارغًا"

    if len(name) < 5:
        return "الاسم قصير جدًا"

    if len(name) > 50:
        return "الاسم طويل جدًا"

    # يجب أن يكون الاسم الأول واسم العائلة فقط
    if name.count(" ") != 1:
        return "يجب إدخال الاسم الأول واسم العائلة فقط"

    first_name, last_name = name.split(" ")

    if len(first_name) < 2:
        return "الاسم الأول قصير جدًا"

    if len(last_name) < 2:
        return "اسم العائلة قصير جدًا"

    # يسمح بالعربية والإنجليزية فقط
    if not re.fullmatch(r"[A-Za-z\u0600-\u06FF ]+", name):
        return "الاسم يجب أن يحتوي على حروف عربية أو إنجليزية فقط"

    return None
    
    
    
    
""" دالة تشغيير كلمات المرور """


import bcrypt

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

