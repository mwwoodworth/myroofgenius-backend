import asyncio
import asyncpg
import os
from config import get_database_url

DATABASE_URL = get_database_url()

async def inspect_tables():
    print(f"Connecting to {DATABASE_URL.split('@')[1]}...")
    try:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        conn = await asyncpg.connect(DATABASE_URL, ssl=ssl_ctx)
        
        tables = ['leads', 'marketing_campaigns', 'customers']
        
        for table in tables:
            print(f"\n--- Table: {table} ---")
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if not exists:
                print("DOES NOT EXIST")
                continue
                
            print("Exists. Columns:")
            columns = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = $1
                ORDER BY ordinal_position
                """,
                table
            )
            has_tenant = False
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")
                if col['column_name'] == 'tenant_id':
                    has_tenant = True
            
            if has_tenant:
                print("✅ Has tenant_id")
            else:
                print("❌ MISSING tenant_id")

        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_tables())
