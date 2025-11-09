import asyncpg
import asyncio
from config import get_database_url
from dotenv import load_dotenv
import os

async def create_tables():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
    load_dotenv(dotenv_path=dotenv_path)
    db_url = get_database_url()
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute("DROP TABLE IF EXISTS workflow_steps CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS workflows CASCADE;")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                step_order INTEGER NOT NULL,
                function_name TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (workflow_id, step_order)
            );
        """)
        print("Tables 'workflows' and 'workflow_steps' created successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
