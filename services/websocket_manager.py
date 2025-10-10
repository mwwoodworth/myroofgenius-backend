"""
WebSocket Manager for Real-time Synchronization
Handles bidirectional real-time communication
"""

from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        # Room/channel subscriptions
        self.room_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        # Connection metadata
        self.connection_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str, metadata: dict = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id].append(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Clean up metadata
        if websocket in self.connection_info:
            del self.connection_info[websocket]

        # Remove from all room subscriptions
        for room_users in self.room_subscriptions.values():
            room_users.discard(user_id)

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)

            # Clean up broken connections
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)

    async def broadcast(self, message: dict, exclude_user: str = None):
        """Broadcast message to all connected clients"""
        disconnected = []
        for user_id, connections in self.active_connections.items():
            if user_id == exclude_user:
                continue

            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error to user {user_id}: {e}")
                    disconnected.append((user_id, connection))

        # Clean up broken connections
        for user_id, conn in disconnected:
            if conn in self.active_connections[user_id]:
                self.active_connections[user_id].remove(conn)

    async def broadcast_to_room(self, room: str, message: dict, exclude_user: str = None):
        """Broadcast message to all users in a specific room"""
        if room not in self.room_subscriptions:
            return

        for user_id in self.room_subscriptions[room]:
            if user_id != exclude_user:
                await self.send_personal_message(message, user_id)

    def join_room(self, user_id: str, room: str):
        """Add user to a room/channel"""
        self.room_subscriptions[room].add(user_id)
        logger.info(f"User {user_id} joined room {room}")

    def leave_room(self, user_id: str, room: str):
        """Remove user from a room/channel"""
        if room in self.room_subscriptions:
            self.room_subscriptions[room].discard(user_id)
            if not self.room_subscriptions[room]:
                del self.room_subscriptions[room]
        logger.info(f"User {user_id} left room {room}")

    def get_room_users(self, room: str) -> List[str]:
        """Get all users in a room"""
        return list(self.room_subscriptions.get(room, set()))

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_user_count(self) -> int:
        """Get number of unique connected users"""
        return len(self.active_connections)

# Global manager instance
manager = ConnectionManager()

# Message types for real-time events
class MessageTypes:
    # Data sync events
    DATA_CREATE = "data:create"
    DATA_UPDATE = "data:update"
    DATA_DELETE = "data:delete"

    # Notification events
    NOTIFICATION = "notification"
    ALERT = "alert"

    # System events
    SYSTEM_STATUS = "system:status"
    USER_ONLINE = "user:online"
    USER_OFFLINE = "user:offline"

    # Collaboration events
    DOC_LOCK = "doc:lock"
    DOC_UNLOCK = "doc:unlock"
    DOC_UPDATE = "doc:update"

    # Job events
    JOB_CREATED = "job:created"
    JOB_UPDATED = "job:updated"
    JOB_COMPLETED = "job:completed"

    # Customer events
    CUSTOMER_CREATED = "customer:created"
    CUSTOMER_UPDATED = "customer:updated"

async def notify_data_change(
    table: str,
    operation: str,
    record_id: str,
    data: dict = None,
    user_id: str = None
):
    """Notify all connected clients of a data change"""
    message = {
        "type": f"data:{operation}",
        "table": table,
        "record_id": record_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id
    }

    # Broadcast to all except the user who made the change
    await manager.broadcast(message, exclude_user=user_id)

async def send_notification(
    user_id: str,
    title: str,
    message: str,
    severity: str = "info",
    data: dict = None
):
    """Send notification to specific user"""
    notification = {
        "type": MessageTypes.NOTIFICATION,
        "title": title,
        "message": message,
        "severity": severity,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.send_personal_message(notification, user_id)

async def broadcast_system_status(status: dict):
    """Broadcast system status to all users"""
    message = {
        "type": MessageTypes.SYSTEM_STATUS,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }

    await manager.broadcast(message)

# WebSocket endpoint handler
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint handler"""
    await manager.connect(websocket, user_id)

    # Notify others that user is online
    await manager.broadcast({
        "type": MessageTypes.USER_ONLINE,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude_user=user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

            elif message_type == "subscribe":
                # Subscribe to a room/channel
                room = data.get("room")
                if room:
                    manager.join_room(user_id, room)
                    await websocket.send_json({
                        "type": "subscribed",
                        "room": room
                    })

            elif message_type == "unsubscribe":
                # Unsubscribe from a room/channel
                room = data.get("room")
                if room:
                    manager.leave_room(user_id, room)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "room": room
                    })

            elif message_type == "broadcast":
                # Broadcast message to room
                room = data.get("room")
                message = data.get("message")
                if room and message:
                    await manager.broadcast_to_room(room, {
                        "type": "room:message",
                        "room": room,
                        "message": message,
                        "from": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            else:
                # Echo unknown messages back
                await websocket.send_json({
                    "type": "echo",
                    "original": data
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

        # Notify others that user is offline
        await manager.broadcast({
            "type": MessageTypes.USER_OFFLINE,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)