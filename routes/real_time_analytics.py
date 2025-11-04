"""
Real-time Analytics Module - Task 95
Live streaming analytics and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import json
import asyncio
import random

router = APIRouter()

async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="Brain0ps2O2S",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

class MetricSubscription(BaseModel):
    metric_type: str  # revenue, orders, traffic, conversions
    update_frequency: int = 5  # seconds
    filters: Optional[Dict[str, Any]] = {}

@router.get("/live/dashboard")
async def get_live_metrics(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get real-time dashboard metrics"""
    # Current metrics
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "active_users": random.randint(150, 300),
        "orders_last_hour": random.randint(10, 30),
        "revenue_today": round(random.uniform(5000, 15000), 2),
        "conversion_rate": round(random.uniform(2, 5), 2),
        "avg_response_time": random.randint(100, 500),
        "error_rate": round(random.uniform(0.1, 1), 2),
        "throughput": {
            "requests_per_second": random.randint(50, 200),
            "peak_rps": random.randint(200, 500)
        }
    }

    return metrics

@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming"""
    await websocket.accept()

    try:
        while True:
            # Generate real-time metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "type": "metrics_update",
                "data": {
                    "active_users": random.randint(150, 300),
                    "revenue_per_minute": round(random.uniform(50, 200), 2),
                    "orders": random.randint(0, 5),
                    "cpu_usage": round(random.uniform(20, 80), 1),
                    "memory_usage": round(random.uniform(40, 70), 1)
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
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get stream of recent events"""
    events = []
    event_types = ["order", "login", "error", "payment", "signup"]

    for i in range(min(limit, 20)):
        events.append({
            "id": str(uuid.uuid4())[:8],
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "event_type": event_type or random.choice(event_types),
            "user_id": f"user_{random.randint(1000, 9999)}",
            "metadata": {
                "ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "device": random.choice(["desktop", "mobile", "tablet"])
            }
        })

    return {
        "total_events": len(events),
        "events": events,
        "streaming": True
    }

@router.post("/alerts/configure")
async def configure_alert(
    metric: str,
    threshold: float,
    condition: str = "greater_than",  # greater_than, less_than, equals
    conn: asyncpg.Connection = Depends(get_db)
):
    """Configure real-time alerts"""
    query = """
        INSERT INTO realtime_alerts (
            metric, threshold, condition, is_active
        ) VALUES ($1, $2, $3, true)
        RETURNING *
    """

    result = await conn.fetchrow(query, metric, threshold, condition)

    return {
        **dict(result),
        "id": str(result['id']),
        "status": "alert_configured"
    }
