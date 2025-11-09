import asyncpg
import asyncio
from config import get_database_url
from dotenv import load_dotenv
import os

async def add_skills_column():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
    load_dotenv(dotenv_path=dotenv_path)
    db_url = get_database_url()
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute("""
            ALTER TABLE ai_agents
            ADD COLUMN IF NOT EXISTS skills TEXT[];
        """)
        print("Column 'skills' added to 'ai_agents' table successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_skills_column())
