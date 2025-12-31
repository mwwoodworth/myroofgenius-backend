"""
Database connection module for BrainOps AI OS

SECURITY: This module provides tenant-isolated database connections.
All connections set the tenant context via PostgreSQL session variables,
which are used by RLS policies to enforce data isolation.
"""

import os
import asyncpg
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

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
    # SQLAlchemy with psycopg2 uses sslmode parameter (not ssl_context)
    # sslmode=require connects with SSL but doesn't verify certificates
    # This works with Supabase pooler's self-signed certs
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

# Tenant-aware connection context manager
@asynccontextmanager
async def get_tenant_connection(pool: asyncpg.Pool, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Acquire a connection with tenant context set for RLS enforcement.

    SECURITY: This is the preferred way to get database connections.
    It sets PostgreSQL session variables that RLS policies use for isolation.

    Usage:
        async with get_tenant_connection(pool, tenant_id="...") as conn:
            await conn.fetch("SELECT * FROM customers")  # RLS filters to tenant
    """
    async with pool.acquire() as conn:
        try:
            if tenant_id:
                await conn.execute("SELECT set_config('app.current_tenant_id', $1, false)", tenant_id)
            if user_id:
                await conn.execute("SELECT set_config('app.current_user_id', $1, false)", user_id)
            yield conn
        finally:
            # Clear context after use
            await conn.execute("SELECT set_config('app.current_tenant_id', '', false)")
            await conn.execute("SELECT set_config('app.current_user_id', '', false)")


# Simple database wrapper for compatibility
class Database:
    def __init__(self, pool, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        self.pool = pool
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _set_context(self, conn):
        """Set tenant context on connection for RLS enforcement"""
        if self.tenant_id:
            await conn.execute("SELECT set_config('app.current_tenant_id', $1, false)", self.tenant_id)
        if self.user_id:
            await conn.execute("SELECT set_config('app.current_user_id', $1, false)", self.user_id)

    async def fetch_one(self, query: str, values: dict = None):
        async with self.pool.acquire() as conn:
            await self._set_context(conn)
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
            await self._set_context(conn)
            if values:
                # Similar parameter conversion
                return await conn.fetch(query, *values.values())
            else:
                return await conn.fetch(query)

    async def execute(self, query: str, values: dict = None):
        async with self.pool.acquire() as conn:
            await self._set_context(conn)
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
async def get_db_async(tenant_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Get database instance for FastAPI dependency injection (async)

    Args:
        tenant_id: Optional tenant ID for RLS enforcement
        user_id: Optional user ID for RLS enforcement

    Returns:
        Database instance with tenant context set
    """
    pool = await get_db_connection()
    return Database(pool, tenant_id=tenant_id, user_id=user_id)


# FastAPI dependency for tenant-aware database access
async def get_tenant_db(request):
    """
    FastAPI dependency that provides tenant-isolated database access.

    Usage in routes:
        @router.get("/items")
        async def get_items(db: Database = Depends(get_tenant_db)):
            return await db.fetch_all("SELECT * FROM items")  # RLS enforced
    """
    from fastapi import Request
    pool = await get_db_connection()

    # Extract tenant_id and user_id from request state (set by auth middleware)
    tenant_id = getattr(request.state, 'tenant_id', None)
    user_id = getattr(request.state, 'user_id', None)

    if not tenant_id:
        logger.warning(f"No tenant_id in request to {request.url.path} - RLS may not filter correctly")

    return Database(pool, tenant_id=tenant_id, user_id=user_id)


__all__ = [
    "get_db_connection",
    "close_db_connection",
    "get_db",
    "get_db_async",
    "get_tenant_db",
    "get_tenant_connection",
    "Database",
    "SessionLocal",
    "engine"
]
