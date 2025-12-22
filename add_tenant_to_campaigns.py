import asyncio
import asyncpg
import os
from config import get_database_url

DATABASE_URL = get_database_url()

async def migrate():
    print(f"Connecting to DB...")
    try:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        conn = await asyncpg.connect(DATABASE_URL, ssl=ssl_ctx)
        
        print("Adding tenant_id to marketing_campaigns...")
        await conn.execute("""
            ALTER TABLE marketing_campaigns 
            ADD COLUMN IF NOT EXISTS tenant_id UUID;
            
            CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_tenant 
            ON marketing_campaigns(tenant_id);
        """)
        print("✅ Added tenant_id column and index.")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
