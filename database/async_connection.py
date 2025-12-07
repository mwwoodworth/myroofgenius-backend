import asyncio
import asyncpg

from config import get_database_url

# Shared pool for ad-hoc routes that aren't initialized through main.py.
_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    """Return a singleton asyncpg pool, creating it on first use."""
    global _pool
    if _pool:
        return _pool

    async with _lock:
        if _pool:
            return _pool

        database_url = get_database_url()
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            statement_cache_size=0,  # Required for pgBouncer compatibility
            command_timeout=15,
        )
        return _pool
