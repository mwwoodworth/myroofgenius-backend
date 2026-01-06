"""
Database compatibility layer for BrainOps Backend.

Provides both async (asyncpg) and sync (SQLAlchemy) interfaces for routes.
Most new code should use async get_pool(). Legacy SQLAlchemy is for compatibility.
"""

import os
import logging
from typing import Optional, Generator
from contextlib import contextmanager, asynccontextmanager

from .async_connection import get_pool

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE_URL - Needed by multiple routes
# =============================================================================
def _get_database_url() -> str:
    """Resolve database URL from environment."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Build from components
    host = os.getenv("DB_HOST") or os.getenv("SUPABASE_DB_HOST")
    port = os.getenv("DB_PORT") or os.getenv("SUPABASE_DB_PORT") or "6543"
    name = os.getenv("DB_NAME") or os.getenv("SUPABASE_DB_NAME") or "postgres"
    user = os.getenv("DB_USER") or os.getenv("SUPABASE_DB_USER")
    password = os.getenv("DB_PASSWORD") or os.getenv("SUPABASE_DB_PASSWORD")

    if all([host, user, password]):
        return f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=require"

    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set DATABASE_URL or DB_HOST/DB_USER/DB_PASSWORD in the environment."
    )

# Export DATABASE_URL as a module-level variable
DATABASE_URL: str = _get_database_url()

# =============================================================================
# SQLAlchemy Engine & Session (for legacy routes)
# =============================================================================
_engine = None
_SessionLocal = None

def _init_sqlalchemy():
    """Lazily initialize SQLAlchemy engine and session factory."""
    global _engine, _SessionLocal

    if _engine is not None:
        return

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        _engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"} if "supabase" in DATABASE_URL else {}
        )

        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )
    except ImportError:
        # SQLAlchemy not installed - provide stubs
        pass

@property
def engine():
    """Get SQLAlchemy engine (lazy initialization)."""
    if _engine is None:
        _init_sqlalchemy()
    if _engine is None:
        raise RuntimeError("SQLAlchemy is not available. Use async get_pool() instead.")
    return _engine

# Make engine accessible as module attribute
class _EngineProxy:
    """Proxy to allow lazy access to engine as database.engine"""
    def __getattr__(self, name):
        _init_sqlalchemy()
        if _engine is None:
            raise RuntimeError("SQLAlchemy not available. Install sqlalchemy or use get_pool().")
        return getattr(_engine, name)

    def __bool__(self):
        _init_sqlalchemy()
        return _engine is not None

engine = _EngineProxy()


def SessionLocal():
    """Get a SQLAlchemy session (legacy compatibility)."""
    _init_sqlalchemy()
    if _SessionLocal is None:
        raise RuntimeError("SQLAlchemy not available. Use async get_pool() instead.")
    return _SessionLocal()


# Also provide Session as alias
Session = SessionLocal


@contextmanager
def get_db_session() -> Generator:
    """Context manager for SQLAlchemy sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# =============================================================================
# Async database access (preferred)
# =============================================================================
async def get_db_connection():
    """Return an asyncpg connection for legacy callers."""
    pool = await get_pool()
    return pool


async def get_db():
    """Async context manager yielding a connection for FastAPI dependencies."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


# =============================================================================
# Tenant-aware Database class (for RLS enforcement)
# =============================================================================
class Database:
    """Database wrapper with tenant context for RLS enforcement."""

    def __init__(self, pool, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        self.pool = pool
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def _set_context(self, conn):
        """Set tenant context on connection for RLS enforcement."""
        if self.tenant_id:
            await conn.execute("SELECT set_config('app.current_tenant_id', $1, false)", self.tenant_id)
        if self.user_id:
            await conn.execute("SELECT set_config('app.current_user_id', $1, false)", self.user_id)

    async def fetch_one(self, query: str, *args):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await self._set_context(conn)
            return await conn.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await self._set_context(conn)
            return await conn.fetch(query, *args)

    async def execute(self, query: str, *args):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await self._set_context(conn)
            return await conn.execute(query, *args)


# =============================================================================
# Tenant-aware FastAPI dependency
# =============================================================================
async def get_tenant_db(request):
    """
    FastAPI dependency that provides tenant-isolated database access.

    Usage in routes:
        @router.get("/items")
        async def get_items(db: Database = Depends(get_tenant_db)):
            return await db.fetch_all("SELECT * FROM items")  # RLS enforced
    """
    pool = await get_pool()

    # Extract tenant_id and user_id from request state (set by auth middleware)
    tenant_id = getattr(request.state, 'tenant_id', None)
    user_id = getattr(request.state, 'user_id', None)

    if not tenant_id:
        logger.warning(f"No tenant_id in request to {request.url.path} - RLS may not filter correctly")

    return Database(pool, tenant_id=tenant_id, user_id=user_id)


# =============================================================================
# Exports
# =============================================================================
__all__ = [
    "get_pool",
    "get_db",
    "get_db_connection",
    "get_db_session",
    "get_tenant_db",
    "Database",
    "DATABASE_URL",
    "engine",
    "Session",
    "SessionLocal",
]
