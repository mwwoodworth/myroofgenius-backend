"""
Database compatibility layer for BrainOps Backend.

Provides both async (asyncpg) and sync (SQLAlchemy) interfaces for routes.
Most new code should use async get_pool(). Legacy SQLAlchemy is for compatibility.
"""

import os
from typing import Optional, Generator
from contextlib import contextmanager

from .async_connection import get_pool

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
# Exports
# =============================================================================
__all__ = [
    "get_pool",
    "get_db",
    "get_db_connection",
    "get_db_session",
    "DATABASE_URL",
    "engine",
    "Session",
    "SessionLocal",
]
