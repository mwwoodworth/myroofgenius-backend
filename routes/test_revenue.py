"""
Test Revenue Route - Verify system is working
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Request

router = APIRouter(tags=["Test"])

@router.get("/")
async def test_revenue(request: Request) -> Dict[str, Any]:
    """Simple test endpoint (no fake targets or demo data)."""
    db_pool = getattr(request.app.state, "db_pool", None)
    db_status = "unavailable"
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        except Exception:
            db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
