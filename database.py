import os
import psycopg
from psycopg_pool import ConnectionPool  # ← ثبّت: pip install psycopg_pool
#print("I'm master robot 🤖)
# ─── Connection Pool ← يدير الـ connections تلقائياً ───
# min_size=1: يبقي connection واحد جاهز
# max_size=10: ما يتجاوز 10 connections
# max_idle=300: يغلق الـ idle بعد 5 دقائق
pool = ConnectionPool(
    os.getenv("DATABASE_URL"),
    min_size=1,
    max_size=10,
    max_idle=60,
    timeout=10,
    check=ConnectionPool.check_connection,
    kwargs={"row_factory": psycopg.rows.dict_row}
)

def init_db():
    """تشغيل مرة واحدة عند بدء السيرفر"""
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users(
                    phone TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    password TEXT,
                    email_otp TEXT,
                    otp_expires_at TIMESTAMP,
                    is_verified INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usdt_balances(
                    phone TEXT UNIQUE,
                    balance NUMERIC(20, 8)
                )
            """)
            #=================================================================
            #Nexa المتجر جدول المتجر الكامل
            #=============//==============//==============//=============//====
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS digital_products (
            id BIGSERIAL PRIMARY KEY,
            -- WDG
            wdg_product_id BIGINT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            description TEXT,
            category_id BIGINT,
            category TEXT,
            type TEXT NOT NULL,
            
            -- WDG pricing
            price_usd NUMERIC(20, 8) NOT NULL,
            original_price_usd NUMERIC(20, 8),
            discount_percent NUMERIC(10, 4) DEFAULT 0,
            currency CHAR(3) NOT NULL DEFAULT 'USD',
            
            -- Nexa pricing
            exchange_rate NUMERIC(20, 8) NOT NULL,
            commission NUMERIC(20, 8) NOT NULL DEFAULT 0,
            price_sdg NUMERIC(20, 2) NOT NULL,
            
            -- Product status
            stock BIGINT,
            available BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            
            -- Purchase requirements
            requires_player_id BOOLEAN NOT NULL DEFAULT FALSE,
            required_fields JSONB,
            
            -- Media
            image_url TEXT,
            
            -- Timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            #======//============================================
            # Nexa انتهاء جدول المتحر!
            #======//========================///===========///===
            #====================================================//
            # marketace جدول الماركت الكامل تقريبا
            #=====================================================
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_store_requests (
            id SERIAL PRIMARY KEY,
            
            owner_phone TEXT NOT NULL,
            
            store_name TEXT NOT NULL,
            store_description TEXT NOT NULL,
            location TEXT NOT NULL,
            
            id_type TEXT NOT NULL,
            id_number TEXT NOT NULL,
            
            delivery_type TEXT NOT NULL,
            
            store_image TEXT NOT NULL,
            owner_photo TEXT NOT NULL,
            id_document TEXT NOT NULL,
            
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            #===================//=====================
            # انتهاء جدولmarketace الكامل تقريبا""""
            #==========≈=====================================
            
            
            #===============================
            #Merchant's Real Store Schedule
            #=================================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_stores (
            id SERIAL PRIMARY KEY,
            
            owner_phone TEXT NOT NULL,
            
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            
            delivery_type TEXT NOT NULL,          
            store_image TEXT NOT NULL,
            owner_photo TEXT NOT NULL,
            
            status TEXT NOT NULL DEFAULT 'active',
            
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            #===================================
            #End of merchant's shop, last table
            #=====================================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_products (
            id SERIAL PRIMARY KEY,
            
            store_id INTEGER NOT NULL,
            
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            
            price NUMERIC(20, 8) NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            
            image_1 TEXT,
            image_2 TEXT,
            image_3 TEXT,
            
            delivery_type TEXT NOT NULL,
            
            status TEXT NOT NULL DEFAULT 'active',
            
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            #===============÷================
            #User basket table 
            #===================÷==============
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
            id SERIAL PRIMARY KEY,
            user_phone TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            UNIQUE (user_phone, product_id)
            )
            """)
            #================================
            # order
            #================================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_orders (
            id BIGSERIAL PRIMARY KEY,
            
            buyer_phone TEXT NOT NULL,
            seller_phone TEXT NOT NULL,
            store_id INTEGER NOT NULL,
            
            total NUMERIC(20, 8) NOT NULL,
            
            status TEXT NOT NULL DEFAULT 'pending',
            
            seller_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
            buyer_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
            
            delivered_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """)
            #============================
            #💰 Schedule of Reserved Funds
            #============================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_held_funds (
            id BIGSERIAL PRIMARY KEY,
            
            order_id BIGINT NOT NULL,
            
            buyer_phone TEXT NOT NULL,
            seller_phone TEXT NOT NULL,
            
            amount NUMERIC(20, 8) NOT NULL,
            
            status TEXT NOT NULL DEFAULT 'held',
            
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            released_at TIMESTAMPTZ,
            refunded_at TIMESTAMPTZ
            )
            """)
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marketplace_order_items (
            id BIGSERIAL PRIMARY KEY,
            
            order_id BIGINT NOT NULL,
            product_id INTEGER NOT NULL,
            
            quantity INTEGER NOT NULL,
            price NUMERIC(20, 8) NOT NULL
            )
            """)
            #=====================
            #==p2p
            #=====================
            
            #================================//==
            #create p2p_merchant_applications
            #====================================
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS p2p_merchant_applications (
            id BIGSERIAL PRIMARY KEY,
            user_phone TEXT NOT NULL
            REFERENCES users(phone),
            
            full_name TEXT NOT NULL,
            country TEXT NOT NULL,
            id_type TEXT NOT NULL,
            id_document_number TEXT NOT NULL,
            
            id_photo_key TEXT NOT NULL,
            personal_photo_key TEXT NOT NULL,
            
            experience INTEGER NOT NULL
                CHECK (experience >= 0),
            expected_daily_volume NUMERIC(20, 8) NOT NULL
               CHECK (expected_daily_volume >= 0),
           terms_accepted BOOLEAN NOT NULL
              CHECK (terms_accepted = TRUE),
          status TEXT NOT NULL DEFAULT 'pending'
             CHECK (
             status IN (
             'pending',
             'under_review',
             'approved',
             'rejected'
             )
             ),
             
             reviewed_by TEXT,
             reviewed_at TIMESTAMPTZ,
             rejection_reason TEXT,
             
             created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
             updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
             )
             """)
            #==============
            #==Nexa: جدول إعلانات p2p
            #=======================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS p2p_ads (
            id BIGSERIAL PRIMARY KEY,
            
            merchant_phone TEXT NOT NULL
                REFERENCES users(phone),
                
                trade_type TEXT NOT NULL
                    CHECK (trade_type IN ('buy', 'sell')),
                asset TEXT NOT NULL DEFAULT 'USDT',
                fiat_currency TEXT NOT NULL DEFAULT 'SDG',
                price NUMERIC(20, 8) NOT NULL
                    CHECK (price > 0),
                min_amount NUMERIC(20, 8) NOT NULL
                    CHECK (min_amount > 0),
                max_amount NUMERIC(20, 8) NOT NULL
                    CHECK (max_amount >= min_amount),
                    
                available_amount NUMERIC(20, 8) NOT NULL
                    CHECK (available_amount >= 0),
                payment_methods JSONB NOT NULL
                    DEFAULT '[]'::jsonb,
                status TEXT NOT NULL DEFAULT 'active' 
                    CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
               terms TEXT, 
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    
                CHECK (available_amount <= max_amount),
                CHECK (jsonb_typeof(payment_methods) = 'array')
                );
                CREATE INDEX IF NOT EXISTS idx_p2p_ads_status_type
                ON p2p_ads (status, trade_type);
                
                CREATE INDEX IF NOT EXISTS idx_p2p_ads_merchant
                ON p2p_ads (merchant_phone)
                )
                """)
            #=============================
            #Nexa: حجز اموال p2p الذي تم إعلانه
            #=============================
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS p2p_ad_reservations (
            id BIGSERIAL PRIMARY KEY,
            
            ad_id BIGINT NOT NULL
                REFERENCES p2p_ads(id),
            merchant_phone TEXT NOT NULL 
                REFERENCES users(phone),
            amount NUMERIC(20, 8) NOT NULL
                CHECK (amount > 0),
                
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (
                status IN (
                'active',
                'partially_consumed',
                'consumed',
                'released'
                )
                ),
        created_at TIMESTAMPTZ NOT NULL
            DEFAULT CURRENT_TIMESTAMP,
       released_at TIMESTAMPTZ
       );
       
       CREATE INDEX IF NOT EXISTS idx_p2p_reservations_ad
           ON p2p_ad_reservations (ad_id);
           
       CREATE INDEX IF NOT EXISTS idx_p2p_reservations_merchant_status
           ON p2p_ad_reservations (merchant_phone, status);
           """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_requests(
            id SERIAL PRIMARY KEY,
            idempotency_key UUID UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            receiver_phone TEXT NOT NULL,
            amount NUMERIC(20, 8) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'processing'
            )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets(
                    id SERIAL PRIMARY KEY,
                    user_phone TEXT,
                    network TEXT,
                    address TEXT,
                    private_key TEXT,
                    public_key TEXT,
                    UNIQUE(user_phone, network)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_transactions(
                    id SERIAL PRIMARY KEY,
                    txid TEXT UNIQUE
                )
            """)
        
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores(
            id SERIAL PRIMARY KEY,
            owner_phone TEXT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions(
                    id SERIAL PRIMARY KEY,
                    user_phone TEXT,
                    receiver_phone TEXT,
                    type TEXT,
                    network TEXT,
                    amount NUMERIC(20, 8),
                    fee NUMERIC(20, 8),
                    net_amount NUMERIC(20, 8),
                    status TEXT,
                    txid TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
            ALTER TABLE transactions
            ADD COLUMN IF NOT EXISTS order_id BIGINT
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_tokens(
                    id SERIAL PRIMARY KEY,
                    phone TEXT,
                    network TEXT,
                    currency TEXT,
                    balance NUMERIC(20, 8),
                    UNIQUE(phone, network, currency)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    phone TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS store_requests(
            id SERIAL PRIMARY KEY,
            owner_phone TEXT NOT NULL,     
            store_name TEXT NOT NULL,
            store_description TEXT NOT NULL,
            store_type TEXT NOT NULL,
            verification_document TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            store_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price NUMERIC(20, 8) NOT NULL,
            file_key TEXT NOT NULL,
            image_1 TEXT NOT NULL,
            image_2 TEXT NOT NULL,
            image_3 TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """);
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases(
            id SERIAL PRIMARY KEY,
            buyer_phone TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            transaction_id INTEGER NOT NULL,
            amount NUMERIC(20, 8) NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            release_at TIMESTAMPTZ
            )
            """)
            conn.commit()

# ─── دالة مساعدة ← تفتح وتسكر الـ connection تلقائياً ───
def get_db():
    """استخدمها في كل endpoint: with get_db() as conn:"""
    return pool.connection()
    
    
# الحمد لله
print(" I'M mr.robor ")