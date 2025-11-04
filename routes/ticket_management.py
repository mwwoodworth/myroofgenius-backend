"""
Ticket Management Module - Task 81
Complete support ticket system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

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

class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    category: str = "general"
    customer_id: str
    attachments: Optional[List[str]] = []

class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    title: str
    description: str
    priority: str
    status: str
    category: str
    customer_id: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create support ticket"""
    query = """
        INSERT INTO support_tickets (
            title, description, priority, category,
            customer_id, attachments, ticket_number, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    result = await conn.fetchrow(
        query,
        ticket.title,
        ticket.description,
        ticket.priority,
        ticket.category,
        uuid.UUID(ticket.customer_id),
        json.dumps(ticket.attachments),
        ticket_number,
        'open'
    )

    background_tasks.add_task(notify_support_team, str(result['id']))

    return format_ticket_response(result)

@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List support tickets"""
    params = []
    conditions = []

    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    if priority:
        params.append(priority)
        conditions.append(f"priority = ${len(params)}")

    if assigned_to:
        params.append(uuid.UUID(assigned_to))
        conditions.append(f"assigned_to = ${len(params)}")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limit)

    query = f"""
        SELECT * FROM support_tickets
        {where_clause}
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            created_at DESC
        LIMIT ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [format_ticket_response(row) for row in rows]

@router.put("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    agent_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Assign ticket to agent"""
    query = """
        UPDATE support_tickets
        SET assigned_to = $1,
            status = 'in_progress',
            updated_at = NOW()
        WHERE id = $2
        RETURNING id
    """

    result = await conn.fetchrow(query, uuid.UUID(agent_id), uuid.UUID(ticket_id))
    if not result:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"status": "assigned", "ticket_id": ticket_id, "agent_id": agent_id}

async def notify_support_team(ticket_id: str):
    """Notify support team of new ticket"""
    
def format_ticket_response(row: dict) -> dict:
    return {
        **dict(row),
        "id": str(row['id']),
        "customer_id": str(row['customer_id']) if row['customer_id'] else None,
        "assigned_to": str(row['assigned_to']) if row.get('assigned_to') else None
    }
