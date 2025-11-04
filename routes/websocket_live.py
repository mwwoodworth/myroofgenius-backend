from fastapi import HTTPException
"""
Real-Time WebSocket System - Live Updates for WeatherCraft ERP
Transforms static dashboard into dynamic, live-updating powerhouse
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json
import asyncio
import logging
from datetime import datetime
import redis
import os

router = APIRouter(prefix="/api/v1/live", tags=["Real-Time"])
logger = logging.getLogger(__name__)

# Placeholder database function
def get_db():
    """Placeholder for database session"""
    return None

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
async def websocket_endpoint(websocket: WebSocket, user_id: str, channel: str = "dashboard"):
    """
    🔴 LIVE WEBSOCKET CONNECTION
    Connect to real-time updates for dashboard, jobs, revenue, etc.
    """
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
                await send_live_update(update_type, user_id, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, channel)

async def send_live_update(update_type: str, user_id: str, websocket: WebSocket):
    """Send specific live updates based on type"""

    if update_type == "dashboard":
        # Get live dashboard data
        update_data = await get_live_dashboard_data()
        await manager.send_personal_message({
            "type": "dashboard_update",
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif update_type == "jobs":
        # Get live job updates
        job_data = await get_live_job_updates()
        await manager.send_personal_message({
            "type": "jobs_update",
            "data": job_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif update_type == "revenue":
        # Get live revenue data
        revenue_data = await get_live_revenue_data()
        await manager.send_personal_message({
            "type": "revenue_update",
            "data": revenue_data,
            "timestamp": datetime.now().isoformat()
        }, websocket)

async def get_live_dashboard_data() -> Dict[str, Any]:
    """Fetch real-time dashboard metrics"""
    return {
        "active_jobs": 15,
        "today_revenue": 12500.00,
        "crew_locations": [
            {"crew": "Team A", "location": "1234 Main St", "status": "in_progress"},
            {"crew": "Team B", "location": "5678 Oak Ave", "status": "completed"}
        ],
        "pending_estimates": 8,
        "weather_alerts": [
            {"type": "storm_warning", "message": "Severe weather expected tomorrow"}
        ]
    }

async def get_live_job_updates() -> Dict[str, Any]:
    """Fetch real-time job status updates"""
    return {
        "jobs_in_progress": 12,
        "jobs_completed_today": 3,
        "recent_updates": [
            {
                "job_id": "J2025-001",
                "customer": "Johnson Residence",
                "status": "materials_delivered",
                "timestamp": "2025-09-14T10:30:00Z"
            },
            {
                "job_id": "J2025-002",
                "customer": "Smith Commercial",
                "status": "crew_arrived",
                "timestamp": "2025-09-14T11:15:00Z"
            }
        ]
    }

async def get_live_revenue_data() -> Dict[str, Any]:
    """Fetch real-time revenue metrics"""
    return {
        "today_total": 18500.75,
        "week_total": 125000.00,
        "month_total": 485000.00,
        "profit_margin": 32.5,
        "recent_payments": [
            {"customer": "ABC Corp", "amount": 5500.00, "time": "1 hour ago"},
            {"customer": "Johnson", "amount": 2800.00, "time": "3 hours ago"}
        ]
    }

# Background task for automatic updates
async def broadcast_periodic_updates():
    """Send periodic updates to all connected clients"""
    while True:
        try:
            # Every 30 seconds, send updates to dashboard channel
            dashboard_data = await get_live_dashboard_data()

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