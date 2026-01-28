"""
BrainOps AI OS - Resilient Subsystem Mixin

Provides common reliability patterns for all AI OS subsystems:
- Safe asyncio task creation (prevents 'Task exception was never retrieved')
- Database operations with automatic retry on PgBouncer connection drops
"""

import asyncio
import logging
from typing import Any, Optional

import asyncpg

logger = logging.getLogger(__name__)


class ResilientSubsystem:
    """
    Mixin providing resilient task creation and database access helpers.

    Any subsystem class that inherits from this gains:
    - _create_safe_task()
    - _db_execute_with_retry()
    - _db_fetch_with_retry()
    - _db_fetchrow_with_retry()
    - _db_fetchval_with_retry()

    The class must have a `db_pool` attribute (asyncpg.Pool).
    """

    db_pool: Optional[asyncpg.Pool]

    # -- Safe task creation ----------------------------------------------------

    def _create_safe_task(self, coro, name: str = None) -> asyncio.Task:
        """Create an asyncio task with exception logging.

        Prevents 'Task exception was never retrieved' by attaching a
        done-callback that logs any unhandled exception.
        """
        task = asyncio.create_task(coro, name=name)

        def _on_done(t: asyncio.Task):
            if t.cancelled():
                return
            exc = t.exception()
            if exc is not None:
                logger.error(
                    "Background task %s failed: %s",
                    t.get_name(), exc, exc_info=exc,
                )

        task.add_done_callback(_on_done)
        return task

    # -- DB retry helpers (PgBouncer resilience) -------------------------------

    _RETRYABLE_ERRORS = (
        asyncpg.ConnectionDoesNotExistError,
        asyncpg.InterfaceError,
        asyncpg.InternalClientError,
        asyncpg.PostgresConnectionError,
    )

    async def _db_execute_with_retry(
        self, query: str, *args, max_retries: int = 2
    ) -> Any:
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.execute(query, *args)
            except self._RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _db_fetch_with_retry(
        self, query: str, *args, max_retries: int = 2
    ) -> Any:
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            except self._RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _db_fetchrow_with_retry(
        self, query: str, *args, max_retries: int = 2
    ) -> Any:
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.fetchrow(query, *args)
            except self._RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error

    async def _db_fetchval_with_retry(
        self, query: str, *args, max_retries: int = 2
    ) -> Any:
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with self.db_pool.acquire() as conn:
                    return await conn.fetchval(query, *args)
            except self._RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
                else:
                    raise
            except asyncio.CancelledError:
                raise
        if last_error:
            raise last_error
