"""
WebSocket Manager for real-time communication
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    CHAT = "chat"
    NOTIFICATION = "notification"
    UPDATE = "update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    AI_RESPONSE = "ai_response"
    JOB_UPDATE = "job_update"
    SYSTEM_ALERT = "system_alert"

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    Features:
    - Room/channel support
    - Broadcasting
    - Connection health monitoring
    - Message history
    """
    
    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Room subscriptions
        self.rooms: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_data: Dict[str, Dict[str, Any]] = {}
        
        # Message history (last 100 per room)
        self.message_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Health check task
        self.health_check_task = None
        
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        self.active_connections[client_id] = websocket
        self.connection_data[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "rooms": set(),
            "last_ping": datetime.utcnow()
        }
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": MessageType.NOTIFICATION.value,
                "message": "Connected to BrainOps real-time system",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            client_id
        )
        
        logger.info(f"Client {client_id} connected")
        
        # Start health check if not running
        if not self.health_check_task:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    def disconnect(self, client_id: str):
        """Remove connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Remove from all rooms
            if client_id in self.connection_data:
                for room in self.connection_data[client_id]["rooms"]:
                    if room in self.rooms:
                        self.rooms[room].discard(client_id)
                
                del self.connection_data[client_id]
            
            logger.info(f"Client {client_id} disconnected")
    
    async def join_room(self, client_id: str, room: str):
        """Join a room/channel"""
        if client_id not in self.active_connections:
            return
        
        if room not in self.rooms:
            self.rooms[room] = set()
            self.message_history[room] = []
        
        self.rooms[room].add(client_id)
        self.connection_data[client_id]["rooms"].add(room)
        
        # Send room history
        if self.message_history[room]:
            await self.send_personal_message(
                {
                    "type": MessageType.UPDATE.value,
                    "room": room,
                    "history": self.message_history[room][-10:]  # Last 10 messages
                },
                client_id
            )
        
        # Notify room
        await self.broadcast_to_room(
            {
                "type": MessageType.NOTIFICATION.value,
                "message": f"User {client_id} joined {room}",
                "room": room,
                "timestamp": datetime.utcnow().isoformat()
            },
            room,
            exclude=[client_id]
        )
        
        logger.info(f"Client {client_id} joined room {room}")
    
    async def leave_room(self, client_id: str, room: str):
        """Leave a room/channel"""
        if room in self.rooms and client_id in self.rooms[room]:
            self.rooms[room].discard(client_id)
            
            if client_id in self.connection_data:
                self.connection_data[client_id]["rooms"].discard(room)
            
            # Notify room
            await self.broadcast_to_room(
                {
                    "type": MessageType.NOTIFICATION.value,
                    "message": f"User {client_id} left {room}",
                    "room": room,
                    "timestamp": datetime.utcnow().isoformat()
                },
                room
            )
            
            logger.info(f"Client {client_id} left room {room}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude: List[str] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or []
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            if client_id in exclude:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {str(e)}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def broadcast_to_room(
        self,
        message: Dict[str, Any],
        room: str,
        exclude: List[str] = None
    ):
        """Broadcast message to all clients in a room"""
        exclude = exclude or []
        
        if room not in self.rooms:
            return
        
        # Store in history
        if room not in self.message_history:
            self.message_history[room] = []
        
        self.message_history[room].append(message)
        
        # Keep only last 100 messages
        if len(self.message_history[room]) > 100:
            self.message_history[room] = self.message_history[room][-100:]
        
        # Send to room members
        disconnected = []
        for client_id in self.rooms[room]:
            if client_id in exclude:
                continue
                
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {client_id} in room {room}: {str(e)}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def handle_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message.get("type", MessageType.CHAT.value)
        
        # Update last activity
        if client_id in self.connection_data:
            self.connection_data[client_id]["last_ping"] = datetime.utcnow()
        
        # Handle different message types
        if message_type == MessageType.PING.value:
            # Respond with pong
            await self.send_personal_message(
                {"type": MessageType.PONG.value, "timestamp": datetime.utcnow().isoformat()},
                client_id
            )
            
        elif message_type == MessageType.CHAT.value:
            # Broadcast chat message to room
            room = message.get("room", "general")
            await self.broadcast_to_room(
                {
                    "type": MessageType.CHAT.value,
                    "from": client_id,
                    "message": message.get("message", ""),
                    "room": room,
                    "timestamp": datetime.utcnow().isoformat()
                },
                room
            )
            
        elif message_type == "join_room":
            room = message.get("room")
            if room:
                await self.join_room(client_id, room)
                
        elif message_type == "leave_room":
            room = message.get("room")
            if room:
                await self.leave_room(client_id, room)
    
    async def _health_check_loop(self):
        """Periodic health check for connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = datetime.utcnow()
                disconnected = []
                
                for client_id, data in self.connection_data.items():
                    last_ping = data.get("last_ping")
                    if last_ping:
                        # If no activity for 60 seconds, send ping
                        diff = (now - last_ping).total_seconds()
                        if diff > 60:
                            try:
                                await self.send_personal_message(
                                    {"type": MessageType.PING.value},
                                    client_id
                                )
                            except:
                                disconnected.append(client_id)
                
                # Clean up dead connections
                for client_id in disconnected:
                    self.disconnect(client_id)
                    
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        room_stats = {}
        for room, clients in self.rooms.items():
            room_stats[room] = {
                "clients": len(clients),
                "messages": len(self.message_history.get(room, []))
            }
        
        return {
            "total_connections": len(self.active_connections),
            "rooms": room_stats,
            "clients": list(self.active_connections.keys())
        }
    
    async def notify_job_update(self, job_id: str, status: str, details: Dict[str, Any]):
        """Send job update notification"""
        await self.broadcast({
            "type": MessageType.JOB_UPDATE.value,
            "job_id": job_id,
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_ai_response(self, client_id: str, response: str, metadata: Dict[str, Any]):
        """Send AI response to specific client"""
        await self.send_personal_message({
            "type": MessageType.AI_RESPONSE.value,
            "response": response,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)
    
    async def send_system_alert(self, alert_level: str, message: str):
        """Send system-wide alert"""
        await self.broadcast({
            "type": MessageType.SYSTEM_ALERT.value,
            "level": alert_level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

# Global WebSocket manager
ws_manager = ConnectionManager()