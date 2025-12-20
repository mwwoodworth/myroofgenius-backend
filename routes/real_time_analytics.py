"""
Real-time Analytics Module - Task 95
Live streaming analytics and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json
import asyncio
import psutil

from core.supabase_auth import get_authenticated_user

router = APIRouter()

from fastapi import Request


async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool

class MetricSubscription(BaseModel):
    metric_type: str  # revenue, orders, traffic, conversions
    update_frequency: int = 5  # seconds
    filters: Optional[Dict[str, Any]] = {}

@router.get("/live/dashboard")
async def get_live_metrics(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get real-time dashboard metrics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    now = datetime.now()
    start_hour = now - timedelta(hours=1)

    active_users = None
    orders_last_hour = None
    revenue_today = None

    async with pool.acquire() as conn:
        # Best-effort queries (schema may differ per deployment).
        try:
            active_users = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_id)
                FROM user_sessions
                WHERE tenant_id = $1
                  AND created_at >= NOW() - INTERVAL '5 minutes'
                """,
                tenant_id,
            )
        except Exception:
            active_users = None

        try:
            orders_last_hour = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM invoices
                WHERE tenant_id = $1
                  AND created_at >= $2
                """,
                tenant_id,
                start_hour,
            )
        except Exception:
            orders_last_hour = None

        try:
            revenue_today = await conn.fetchval(
                """
                SELECT COALESCE(SUM(total_amount), 0)
                FROM invoices
                WHERE tenant_id = $1
                  AND (status = 'paid' OR payment_status = 'paid')
                  AND created_at >= CURRENT_DATE
                """,
                tenant_id,
            )
        except Exception:
            revenue_today = None

    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    metrics = {
        "timestamp": now.isoformat(),
        "active_users": int(active_users) if active_users is not None else None,
        "orders_last_hour": int(orders_last_hour) if orders_last_hour is not None else None,
        "revenue_today": float(revenue_today) if revenue_today is not None else None,
        "conversion_rate": None,
        "avg_response_time_ms": None,
        "error_rate": None,
        "system": {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
        },
        "throughput": None,
    }

    return metrics

@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming"""
    await websocket.accept()

    try:
        while True:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "type": "metrics_update",
                "data": {
                    "cpu_usage": round(cpu_percent, 2),
                    "memory_usage": round(memory.percent, 2),
                }
            }

            await websocket.send_json(metrics)
            await asyncio.sleep(5)  # Update every 5 seconds

    except Exception as e:
        await websocket.close()

@router.get("/stream/events")
async def get_event_stream(
    event_type: Optional[str] = None,
    limit: int = 100,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get stream of recent events"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    events: List[Dict[str, Any]] = []
    # This endpoint requires a real event log table. If none exists, return an empty stream.
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT id, created_at, event_type, metadata
                FROM event_log
                WHERE tenant_id = $1
                  AND ($2::text IS NULL OR event_type = $2)
                ORDER BY created_at DESC
                LIMIT $3
                """,
                tenant_id,
                event_type,
                min(limit, 200),
            )
            events = [dict(r) for r in rows]
        except Exception:
            events = []

    return {
        "total_events": len(events),
        "events": events,
        "streaming": True,
    }

@router.post("/alerts/configure")
async def configure_alert(
    metric: str,
    threshold: float,
    condition: str = "greater_than",  # greater_than, less_than, equals
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Configure real-time alerts"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        INSERT INTO realtime_alerts (
            tenant_id, metric, threshold, condition, is_active
        ) VALUES ($1, $2, $3, $4, true)
        RETURNING *
    """

    async with pool.acquire() as conn:
        result = await conn.fetchrow(query, tenant_id, metric, threshold, condition)

    return {
        **dict(result),
        "id": str(result['id']),
        "status": "alert_configured"
    }
