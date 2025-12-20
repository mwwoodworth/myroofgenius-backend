"""
Real-Time WebSocket System - Live Updates for WeatherCraft ERP
Transforms static dashboard into dynamic, live-updating powerhouse
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import logging
from datetime import datetime
import redis
import os

router = APIRouter(prefix="/api/v1/live", tags=["Real-Time"])
logger = logging.getLogger(__name__)

from database import get_db_connection

# Redis for pub/sub (optional)
try:
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
except:
    redis_client = None

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, channel: str = "general"):
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = []

        self.active_connections[channel].append(websocket)
        self.user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to channel {channel}")

        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "message": "🚀 Real-time updates activated!"
        }, websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, channel: str = "general"):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)

        if user_id in self.user_connections:
            del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from channel {channel}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            await self.send_personal_message(message, self.user_connections[user_id])

    async def broadcast_to_channel(self, message: dict, channel: str = "general"):
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[channel].remove(conn)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    channel: str = "dashboard",
    tenant_id: str | None = None,
):
    """
    🔴 LIVE WEBSOCKET CONNECTION
    Connect to real-time updates for dashboard, jobs, revenue, etc.
    """
    if not tenant_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id, channel)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle different message types
            message_type = message_data.get("type", "unknown")

            if message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)

            elif message_type == "subscribe":
                # Subscribe to specific updates
                subscription = message_data.get("subscription", [])
                await manager.send_personal_message({
                    "type": "subscription_confirmed",
                    "subscriptions": subscription,
                    "message": f"✅ Subscribed to {', '.join(subscription)}"
                }, websocket)

            elif message_type == "request_update":
                # Request immediate update for specific data
                update_type = message_data.get("update_type", "dashboard")
                await send_live_update(update_type, user_id, tenant_id, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, channel)

async def send_live_update(update_type: str, user_id: str, tenant_id: str, websocket: WebSocket):
    """Send specific live updates based on type"""

    if update_type == "dashboard":
        # Get live dashboard data
        update_data = await get_live_dashboard_data(tenant_id)
        await manager.send_personal_message({
            "type": "dashboard_update",
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif update_type == "jobs":
        # Get live job updates
        job_data = await get_live_job_updates(tenant_id)
        await manager.send_personal_message({
            "type": "jobs_update",
            "data": job_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif update_type == "revenue":
        # Get live revenue data
        revenue_data = await get_live_revenue_data(tenant_id)
        await manager.send_personal_message({
            "type": "revenue_update",
            "data": revenue_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def get_live_dashboard_data(tenant_id: str) -> Dict[str, Any]:
    """Fetch real-time dashboard metrics"""
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        active_jobs = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM jobs
            WHERE tenant_id = $1
              AND status IN ('in_progress', 'scheduled')
            """,
            tenant_id,
        )
        pending_estimates = await conn.fetchval(
            "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1 AND status = 'pending'",
            tenant_id,
        )
        today_revenue = await conn.fetchval(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices
            WHERE tenant_id = $1
              AND status = 'paid'
              AND created_at >= CURRENT_DATE
            """,
            tenant_id,
        )

    return {
        "active_jobs": int(active_jobs or 0),
        "today_revenue": float(today_revenue or 0),
        "crew_locations": [],
        "pending_estimates": int(pending_estimates or 0),
        "weather_alerts": [],
    }

async def get_live_job_updates(tenant_id: str) -> Dict[str, Any]:
    """Fetch real-time job status updates"""
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        jobs_in_progress = await conn.fetchval(
            "SELECT COUNT(*) FROM jobs WHERE tenant_id = $1 AND status = 'in_progress'",
            tenant_id,
        )
        jobs_completed_today = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM jobs
            WHERE tenant_id = $1
              AND status = 'completed'
              AND completed_date >= CURRENT_DATE
            """,
            tenant_id,
        )
        recent = await conn.fetch(
            """
            SELECT j.id, j.job_number, j.status, j.created_at, c.name AS customer_name
            FROM jobs j
            LEFT JOIN customers c ON c.id = j.customer_id
            WHERE j.tenant_id = $1
            ORDER BY j.created_at DESC
            LIMIT 10
            """,
            tenant_id,
        )

    recent_updates = []
    for row in recent:
        recent_updates.append(
            {
                "job_id": str(row.get("job_number") or row["id"]),
                "customer": row.get("customer_name"),
                "status": row.get("status"),
                "timestamp": (row.get("created_at") or datetime.utcnow()).isoformat(),
            }
        )

    return {
        "jobs_in_progress": int(jobs_in_progress or 0),
        "jobs_completed_today": int(jobs_completed_today or 0),
        "recent_updates": recent_updates,
    }

async def get_live_revenue_data(tenant_id: str) -> Dict[str, Any]:
    """Fetch real-time revenue metrics"""
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        today_total = await conn.fetchval(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices
            WHERE tenant_id = $1
              AND status = 'paid'
              AND created_at >= CURRENT_DATE
            """,
            tenant_id,
        )
        week_total = await conn.fetchval(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices
            WHERE tenant_id = $1
              AND status = 'paid'
              AND created_at >= date_trunc('week', NOW())
            """,
            tenant_id,
        )
        month_total = await conn.fetchval(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices
            WHERE tenant_id = $1
              AND status = 'paid'
              AND created_at >= date_trunc('month', NOW())
            """,
            tenant_id,
        )
        recent = await conn.fetch(
            """
            SELECT i.total_amount, i.created_at, c.name AS customer_name
            FROM invoices i
            LEFT JOIN customers c ON c.id = i.customer_id
            WHERE i.tenant_id = $1
              AND i.status = 'paid'
            ORDER BY i.created_at DESC
            LIMIT 10
            """,
            tenant_id,
        )

    recent_payments = []
    for row in recent:
        recent_payments.append(
            {
                "customer": row.get("customer_name"),
                "amount": float(row.get("total_amount") or 0),
                "time": row.get("created_at").isoformat() if row.get("created_at") else None,
            }
        )

    return {
        "today_total": float(today_total or 0),
        "week_total": float(week_total or 0),
        "month_total": float(month_total or 0),
        "profit_margin": None,
        "recent_payments": recent_payments,
    }

# Background task for automatic updates
async def broadcast_periodic_updates():
    """Send periodic updates to all connected clients"""
    while True:
        try:
            # Every 30 seconds, send updates to dashboard channel
            # Periodic broadcasts require a tenant context; omit data when not provided.
            dashboard_data = {"available": False}

            await manager.broadcast_to_channel({
                "type": "periodic_update",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat(),
                "interval": "30s"
            }, "dashboard")

            # Wait 30 seconds
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Periodic update error: {e}")
            await asyncio.sleep(30)

# API endpoints for triggering updates
@router.post("/trigger/job-update")
async def trigger_job_update(job_id: str, status: str, user_id: str = None):
    """
    🔄 TRIGGER JOB STATUS UPDATE
    Manually trigger real-time job status updates
    """

    update_message = {
        "type": "job_status_change",
        "job_id": job_id,
        "new_status": status,
        "timestamp": datetime.now().isoformat(),
        "message": f"Job {job_id} status changed to {status}"
    }

    await manager.broadcast_to_channel(update_message, "dashboard")

    return {
        "success": True,
        "message": "Job update broadcasted",
        "job_id": job_id,
        "status": status
    }

@router.post("/trigger/revenue-update")
async def trigger_revenue_update(amount: float, customer: str):
    """
    💰 TRIGGER REVENUE UPDATE
    Real-time revenue notifications
    """

    update_message = {
        "type": "new_payment",
        "amount": amount,
        "customer": customer,
        "timestamp": datetime.now().isoformat(),
        "message": f"💰 New payment: ${amount:,.2f} from {customer}"
    }

    await manager.broadcast_to_channel(update_message, "dashboard")

    return {
        "success": True,
        "message": "Revenue update sent",
        "amount": amount,
        "customer": customer
    }

@router.post("/trigger/weather-alert")
async def trigger_weather_alert(alert_type: str, message: str):
    """
    🌤️ TRIGGER WEATHER ALERT
    Send weather alerts to all connected users
    """

    alert_message = {
        "type": "weather_alert",
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "priority": "high" if alert_type == "storm_warning" else "medium"
    }

    await manager.broadcast_to_channel(alert_message, "dashboard")

    return {
        "success": True,
        "alert_sent": True,
        "type": alert_type,
        "message": message
    }

@router.get("/connections/status")
async def get_connection_status():
    """Get current WebSocket connection statistics"""

    total_connections = sum(len(connections) for connections in manager.active_connections.values())

    return {
        "total_connections": total_connections,
        "channels": {
            channel: len(connections)
            for channel, connections in manager.active_connections.items()
        },
        "active_users": len(manager.user_connections),
        "status": "operational"
    }
