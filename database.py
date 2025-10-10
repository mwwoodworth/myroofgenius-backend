"""
Database connection module for BrainOps AI OS
"""

import os
import asyncpg
import asyncio
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

# Global connection pool (AsyncPG)
_connection_pool: Optional[asyncpg.Pool] = None

# SQLAlchemy engine and SessionLocal for sync routes
engine = create_engine(
    DATABASE_URL.replace("+asyncpg", ""),  # Remove async driver if present
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_db_connection():
    """
    Get database connection from pool
    """
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300.0,
            command_timeout=60.0
        )

    return _connection_pool

async def close_db_connection():
    """
    Close database connection pool
    """
    global _connection_pool

    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None

# Simple database wrapper for compatibility
class Database:
    def __init__(self, pool):
        self.pool = pool

    async def fetch_one(self, query: str, values: dict = None):
        async with self.pool.acquire() as conn:
            if values:
                # Convert named parameters to positional
                query_parts = query.split(':')
                positional_query = query_parts[0]
                param_count = 1

                for part in query_parts[1:]:
                    param_name = part.split()[0].rstrip(',').rstrip(')')
                    positional_query += f"${param_count}" + part[len(param_name):]
                    param_count += 1

                # Extract values in order
                param_values = []
                for part in query_parts[1:]:
                    param_name = part.split()[0].rstrip(',').rstrip(')')
                    param_values.append(values.get(param_name))

                return await conn.fetchrow(positional_query, *param_values)
            else:
                return await conn.fetchrow(query)

    async def fetch_all(self, query: str, values: dict = None):
        async with self.pool.acquire() as conn:
            if values:
                # Similar parameter conversion
                return await conn.fetch(query, *values.values())
            else:
                return await conn.fetch(query)

    async def execute(self, query: str, values: dict = None):
        async with self.pool.acquire() as conn:
            if values:
                return await conn.execute(query, *values.values())
            else:
                return await conn.execute(query)

# Sync get_db for SQLAlchemy Session routes
def get_db():
    """
    Synchronous database session for SQLAlchemy routes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async get_db for asyncpg routes
async def get_db_async():
    """
    Get database instance for FastAPI dependency injection (async)
    """
    pool = await get_db_connection()
    return Database(pool)

__all__ = ["get_db_connection", "close_db_connection", "get_db", "get_db_async", "Database", "SessionLocal", "engine"]