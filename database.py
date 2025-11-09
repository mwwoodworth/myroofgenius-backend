"""
Centralized database connection management.
"""

import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def get_db():
    """
    Creates and yields a database connection pool.
    Reads connection details from environment variables.
    """
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    try:
        yield conn
    finally:
        await conn.close()
