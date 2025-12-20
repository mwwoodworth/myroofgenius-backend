"""
Live Chat Module - Task 83
Real-time customer chat support
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json
import asyncio

router = APIRouter()

async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class ChatSessionCreate(BaseModel):
    customer_id: str
    initial_message: str
    metadata: Optional[Dict[str, Any]] = {}

class MessageCreate(BaseModel):
    session_id: str
    sender_type: str  # customer, agent, system
    sender_id: str
    message: str
    attachments: Optional[List[str]] = []

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

    async def send_to_session(self, message: str, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.post("/sessions", response_model=dict)
async def create_chat_session(
    session: ChatSessionCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new chat session"""
    query = """
        INSERT INTO chat_sessions (
            customer_id, status, metadata
        ) VALUES ($1, $2, $3)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(session.customer_id),
        'waiting',
        json.dumps(session.metadata)
    )

    # Save initial message
    msg_query = """
        INSERT INTO chat_messages (
            session_id, sender_type, sender_id, message
        ) VALUES ($1, $2, $3, $4)
    """

    await conn.execute(
        msg_query,
        result['id'],
        'customer',
        uuid.UUID(session.customer_id),
        session.initial_message
    )

    return {
        "session_id": str(result['id']),
        "status": result['status'],
        "created_at": result['created_at']
    }

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Save message to database
            conn = await asyncpg.connect(
                host="aws-0-us-east-2.pooler.supabase.com",
                port=5432,
                user="postgres.yomagoqdmxszqtdwuhab",
                password="<DB_PASSWORD_REDACTED>",
                database="postgres"
            )

            try:
                query = """
                    INSERT INTO chat_messages (
                        session_id, sender_type, sender_id, message
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id, created_at
                """

                result = await conn.fetchrow(
                    query,
                    uuid.UUID(session_id),
                    message_data['sender_type'],
                    uuid.UUID(message_data['sender_id']),
                    message_data['message']
                )

                # Broadcast to all participants
                response = {
                    "message_id": str(result['id']),
                    "session_id": session_id,
                    "sender_type": message_data['sender_type'],
                    "sender_id": message_data['sender_id'],
                    "message": message_data['message'],
                    "timestamp": result['created_at'].isoformat()
                }

                await manager.send_to_session(json.dumps(response), session_id)

            finally:
                await conn.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

@router.get("/sessions/waiting", response_model=List[dict])
async def get_waiting_sessions(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get chat sessions waiting for agent"""
    query = """
        SELECT
            cs.*,
            cm.message as last_message
        FROM chat_sessions cs
        LEFT JOIN LATERAL (
            SELECT message
            FROM chat_messages
            WHERE session_id = cs.id
            ORDER BY created_at DESC
            LIMIT 1
        ) cm ON true
        WHERE cs.status = 'waiting'
        ORDER BY cs.created_at
    """

    rows = await conn.fetch(query)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "customer_id": str(row['customer_id'])
        } for row in rows
    ]
