"""
Database connection module for BrainOps AI OS
"""

import os
import asyncpg
import asyncio
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

def _resolve_database_url() -> Optional[str]:
    """Resolve the database URL without embedding secrets in code."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Fallback to structured env vars via config.py when available.
    try:
        from config import get_database_url  # local import to avoid circular dependencies
        return get_database_url()
    except Exception:
        return None


DATABASE_URL = _resolve_database_url()

# Global connection pool (AsyncPG)
_connection_pool: Optional[asyncpg.Pool] = None

# SQLAlchemy engine and SessionLocal for sync routes
engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL.replace("+asyncpg", ""),  # Remove async driver if present
        pool_size=int(os.getenv("DB_POOL_SIZE", "2")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "3")),
        pool_pre_ping=True,
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "300")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "10")),
        connect_args={
            "sslmode": os.getenv("DB_SSLMODE", "require"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
        },
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_db_connection():
    """
    Get database connection from pool
    """
    global _connection_pool

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")

    if _connection_pool is None:
        _connection_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=int(os.getenv("ASYNCPG_POOL_MIN_SIZE", "1")),
            max_size=int(os.getenv("ASYNCPG_POOL_MAX_SIZE", "5")),
            max_queries=50000,
            max_inactive_connection_lifetime=float(os.getenv("ASYNCPG_MAX_INACTIVE_SECS", "60")),
            command_timeout=float(os.getenv("ASYNCPG_COMMAND_TIMEOUT_SECS", "30")),
            statement_cache_size=0,
            timeout=float(os.getenv("ASYNCPG_CONNECT_TIMEOUT_SECS", "10")),
            ssl=True,
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
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured.")

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
