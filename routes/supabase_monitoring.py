"""
Supabase Database Monitoring Routes

Provides basic database overview metrics using the application's configured database
connection (no hardcoded credentials, no mock responses).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/supabase", tags=["Supabase Monitoring"])


async def _get_conn(request: Request) -> asyncpg.Connection:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return await pool.acquire()


@router.get("/overview")
async def get_database_overview(request: Request) -> Dict[str, Any]:
    """Get database statistics from the connected Postgres instance."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        counts = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE table_type = 'BASE TABLE') as tables,
                COUNT(*) FILTER (WHERE table_type = 'VIEW') as views,
                COUNT(DISTINCT table_schema) as schemas
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            """
        )

        size = await conn.fetchrow(
            """
            SELECT
                pg_database_size(current_database()) / 1024 / 1024 as size_mb,
                pg_database_size(current_database()) / 1024 / 1024 / 1024 as size_gb
            """
        )

        connections = await conn.fetchrow(
            """
            SELECT
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
                (SELECT count(*) FROM pg_stat_activity) as current_connections,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                (SELECT count(*) FROM pg_stat_activity WHERE wait_event_type IS NOT NULL) as waiting_queries
            """
        )

        performance = await conn.fetchrow(
            """
            SELECT
                (SELECT sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100
                 FROM pg_statio_user_tables) as cache_hit_ratio,
                (SELECT count(*) FROM pg_stat_user_tables WHERE n_dead_tup > 1000) as tables_need_vacuum,
                (SELECT count(*) FROM pg_stat_user_tables WHERE last_autovacuum < NOW() - INTERVAL '7 days') as stale_tables
            """
        )

    max_connections = int(connections["max_connections"] or 0) if connections else 0
    current_connections = int(connections["current_connections"] or 0) if connections else 0

    return {
        "database": {
            "tables": int(counts["tables"] or 0) if counts else 0,
            "views": int(counts["views"] or 0) if counts else 0,
            "schemas": int(counts["schemas"] or 0) if counts else 0,
            "size_mb": float(size["size_mb"]) if size and size["size_mb"] is not None else None,
            "size_gb": float(size["size_gb"]) if size and size["size_gb"] is not None else None,
        },
        "connections": {
            "max": max_connections or None,
            "current": current_connections or None,
            "active": int(connections["active_queries"] or 0) if connections else None,
            "idle": int(connections["idle_connections"] or 0) if connections else None,
            "waiting": int(connections["waiting_queries"] or 0) if connections else None,
            "usage_percent": round((current_connections / max_connections) * 100, 2)
            if max_connections
            else None,
        },
        "performance": {
            "cache_hit_ratio": round(float(performance["cache_hit_ratio"] or 0), 2) if performance else None,
            "tables_need_vacuum": int(performance["tables_need_vacuum"] or 0) if performance else None,
            "stale_tables": int(performance["stale_tables"] or 0) if performance else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

