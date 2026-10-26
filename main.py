from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import asyncio
import psutil
#print("I'm master robot 🤖)
import config
from database import init_db, pool

from users import router as users_router
from profile import router as profile_router
from transactions import router as transactions_router
from wallets import router as wallets_router
from admin import router as admin_router
from chat_bot import router as chat_bot_router
from store import router as store_router
from digital_store import router as digital_store_router
from marketplace import router as marketplace_router
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    init_db()
    yield
    pool.close()  

app = FastAPI(
    title="Nexa Wallet API",
    description="Nexa is a P2P Digital Wallet & Fintech API for underbanked users in MENA. Includes wallets, marketplace, and AI chatbot.",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(
            call_next(request),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return {"error": "Request timeout", "status": 504}

# ✅ تسجيل كل الـ Routers
app.include_router(users_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(wallets_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(chat_bot_router, prefix="/api")
app.include_router(store_router, prefix="/api")
app.include_router(digital_store_router, prefix="/api")
app.include_router(marketplace_router, prefix="/api")
# ✅ Health Check Endpoint
@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request):
    """فحص صحة السيرفر"""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "cpu": f"{cpu}%",
        "memory": f"{memory}%",
        "connections": 50
    }

# ✅ Root Endpoint
@app.get("/")
@limiter.limit("200/minute")
async def root(request: Request):
    """الصفحة الرئيسية"""
    return {
        "message": "مرحباً بك في Nexa Wallet API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    