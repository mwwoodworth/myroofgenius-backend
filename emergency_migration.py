import asyncpg
import asyncio
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

async def emergency_fix():
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Ensure critical tables exist
    tables_to_check = [
        ("customers", """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """),
        ("jobs", """
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                title VARCHAR(255),
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """),
        ("invoices", """
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                job_id INTEGER,
                amount DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """),
        ("estimates", """
            CREATE TABLE IF NOT EXISTS estimates (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                property_info JSONB,
                costs JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """),
        ("ai_agents", """
            CREATE TABLE IF NOT EXISTS ai_agents (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                status VARCHAR(50),
                capabilities TEXT,
                last_active TIMESTAMP DEFAULT NOW()
            )
        """)
    ]
    
    for table_name, create_sql in tables_to_check:
        try:
            await conn.execute(create_sql)
            print(f"✅ Table {table_name} ready")
        except Exception as e:
            print(f"⚠️ Table {table_name}: {str(e)[:50]}")
    
    await conn.close()
    print("✅ Database ready for production")

asyncio.run(emergency_fix())
