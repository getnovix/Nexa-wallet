# auth هذا الملف هنا يخص التوكن تبع المستخدم فقط يعني لازم يكون موجود عشام نفك الjwt بنجاح

import os

SECRET_KEY = os.getenv("SECRET_KEY")
admin_phone = os.getenv("admin_phone")
admin_email = os.getenv("admin_email")
admin_password = os.getenv("admin_password")

WDGZONE_BASE_URL = "https://wdgzone.tech/api/v1"
WDGZONE_API_KEY = os.getenv("WDGZONE_API_KEY")
# $email الايميل الخاص بالمشروع """
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
ALGORITHM = "HS256"

# netork كلف الشبكلت والعملات المدعومة
SUPPORTED_TOKENS = [
    ("TRON", "USDT"),
    ("BSC", "USDT"),
    ("POLYGON", "USDT"),
    ("TRON", "TRX"),
    ("BSC", "BNB"),
    ("POLYGON", "MATIC"),
]



