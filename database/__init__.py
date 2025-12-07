"""Lightweight database compatibility shims for legacy route imports."""

from .async_connection import get_pool

# Legacy SQLAlchemy-style API expected by some routes. We provide no-op stubs
# to keep route loading from failing in environments that rely on asyncpg.
def SessionLocal():
    raise RuntimeError("SessionLocal is not available; use async connections via get_pool()")


async def get_db_connection():
    """Return an asyncpg connection for legacy callers."""
    pool = await get_pool()
    return pool


async def get_db():
    """Async context manager yielding a connection for FastAPI dependencies."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
