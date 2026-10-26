from fastapi import APIRouter, Depends
import httpx
from config import WDGZONE_BASE_URL, WDGZONE_API_KEY
from database import get_db
from auth import decode_token, get_current_user
router = APIRouter(
    prefix="/digital-store",
    tags=["Digital Store"]
)

@router.get("/products")
async def get_products():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
            f"{WDGZONE_BASE_URL}/products",
            headers={
            "X-API-Key": WDGZONE_API_KEY,
            "Accept": "application/json"
            },
            params={
            "type": "topup",
            "limit": 100,
            "page": 1
            },
            timeout=20
            )
        if response.status_code != 200:
            return {
            "ok": False,
            "message": " الخدمة متوقفة حاليآ",
            "status_code": response.status_code
            }
        data = response.json()
        return data
    except httpx.RequestError:
        return {
            "ok": False,
            "message": "تعذر الاتصال بمزود المنتجات"
                }
                
@router.get("/catalog/topup/categories")
async def get_topup_categories():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
             f"{WDGZONE_BASE_URL}/catalog/topup/categories",
             headers={
             "X-API-Key": WDGZONE_API_KEY,
            "Accept": "application/json"
            },
            timeout=20   
            )
            data = response.json()
            return data
    except httpx.RequestError:
        return {
            "ok": False,
            "message": "تعذر الاتصال بمزود المنتجات"
        }
        
@router.get("/catalog/topup/categories/{category_id}/products")
async def get_category_products(category_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
             f"{WDGZONE_BASE_URL}/catalog/topup/categories/{category_id}/products",
             headers={
             "X-API-Key": WDGZONE_API_KEY,
            "Accept": "application/json"
            },
            timeout=20   
            )
            data = response.json()
            if response.status_code != 200:
                return {
                "ok": False,
                "message": "تعذر جلب المنتجات",
                "status_code": response.status_code
                }
            return data
    except httpx.RequestError:
        return {
            "ok": False,
            "message": "تعذر الاتصال بمزود المنتجات"
        }
async def sync_products():
    page = 1
    all_products = []
    try:
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                f"{WDGZONE_BASE_URL}/products",
                headers={
                "X-API-Key": WDGZONE_API_KEY,
                "Accept": "application/json"
                },
                params={
                "type": "topup",
                "limit": 100,
                "page": page
                },
                timeout=20
                )
                if response.status_code != 200:
                    return {
                    "ok": False,
                    "message": "تعذر جلب المنتجات",
                    "status_code": response.status_code
                    }
                data = response.json()
                products = data["data"]
                all_products.extend(products)
                pagination = data["pagination"]
                if page >= pagination["total_pages"]:
                    break
                page += 1
            return {
            "ok": True,
                "total": len(all_products),
                "products": all_products
                }
    except httpx.RequestError:
        return {
        "ok": False,
        "message": "تعذر الاتصال بمزود المنتجات"
        }