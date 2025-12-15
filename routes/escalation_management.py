"""
Escalation Management Module - Task 90
Automated escalation workflows
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import uuid
import json

router = APIRouter()

async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

class EscalationRuleCreate(BaseModel):
    name: str
    trigger_condition: str  # time_based, priority_based, customer_based
    trigger_value: Dict[str, Any]
    escalation_level: int
    notify_users: List[str]
    actions: List[Dict[str, Any]]
    is_active: bool = True

@router.post("/rules", response_model=dict)
async def create_escalation_rule(
    rule: EscalationRuleCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create escalation rule"""
    query = """
        INSERT INTO escalation_rules (
            name, trigger_condition, trigger_value,
            escalation_level, notify_users, actions, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        rule.name,
        rule.trigger_condition,
        json.dumps(rule.trigger_value),
        rule.escalation_level,
        json.dumps(rule.notify_users),
        json.dumps(rule.actions),
        rule.is_active
    )

    return {
        **dict(result),
        "id": str(result['id'])
    }

@router.post("/tickets/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    reason: str,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Manually escalate a ticket"""
    # Get ticket details
    ticket_query = "SELECT * FROM support_tickets WHERE id = $1"
    ticket = await conn.fetchrow(ticket_query, uuid.UUID(ticket_id))

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Create escalation record
    escalation_query = """
        INSERT INTO ticket_escalations (
            ticket_id, escalation_level, reason, escalated_by
        ) VALUES ($1, $2, $3, $4)
        RETURNING *
    """

    current_level = ticket.get('escalation_level', 0) + 1

    escalation = await conn.fetchrow(
        escalation_query,
        uuid.UUID(ticket_id),
        current_level,
        reason,
        'manual'
    )

    # Update ticket
    update_query = """
        UPDATE support_tickets
        SET escalation_level = $1,
            priority = 'high',
            updated_at = NOW()
        WHERE id = $2
    """

    await conn.execute(update_query, current_level, uuid.UUID(ticket_id))

    # Trigger notifications
    background_tasks.add_task(
        notify_escalation,
        ticket_id,
        current_level,
        reason
    )

    return {
        "ticket_id": ticket_id,
        "escalation_level": current_level,
        "status": "escalated"
    }

@router.get("/active-escalations", response_model=List[dict])
async def get_active_escalations(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all active escalations"""
    query = """
        SELECT
            te.*,
            st.title as ticket_title,
            st.priority,
            st.customer_id
        FROM ticket_escalations te
        JOIN support_tickets st ON te.ticket_id = st.id
        WHERE te.resolved_at IS NULL
        ORDER BY te.escalation_level DESC, te.created_at DESC
    """

    rows = await conn.fetch(query)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "ticket_id": str(row['ticket_id']),
            "customer_id": str(row['customer_id'])
        } for row in rows
    ]

@router.post("/check-escalations")
async def check_and_apply_escalations(
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Check and apply escalation rules"""
    # Get active rules
    rules_query = "SELECT * FROM escalation_rules WHERE is_active = true"
    rules = await conn.fetch(rules_query)

    escalated_count = 0

    for rule in rules:
        trigger_value = json.loads(rule['trigger_value'])

        if rule['trigger_condition'] == 'time_based':
            # Find tickets that exceed time threshold
            hours = trigger_value.get('hours', 24)
            ticket_query = """
                SELECT id FROM support_tickets
                WHERE status = 'open'
                AND created_at < NOW() - INTERVAL '%s hours'
                AND (escalation_level < $1 OR escalation_level IS NULL)
            """ % hours

            tickets = await conn.fetch(ticket_query, rule['escalation_level'])

            for ticket in tickets:
                await escalate_ticket_internal(
                    str(ticket['id']),
                    rule,
                    conn,
                    background_tasks
                )
                escalated_count += 1

    return {
        "checked": len(rules),
        "escalated": escalated_count
    }

async def escalate_ticket_internal(
    ticket_id: str,
    rule: dict,
    conn: asyncpg.Connection,
    background_tasks: BackgroundTasks
):
    """Internal function to escalate ticket based on rule"""
    # Create escalation record
    await conn.execute(
        """
        INSERT INTO ticket_escalations (
            ticket_id, escalation_level, reason, escalated_by
        ) VALUES ($1, $2, $3, $4)
        """,
        uuid.UUID(ticket_id),
        rule['escalation_level'],
        f"Auto-escalated by rule: {rule['name']}",
        'system'
    )

    # Update ticket
    await conn.execute(
        """
        UPDATE support_tickets
        SET escalation_level = $1, updated_at = NOW()
        WHERE id = $2
        """,
        rule['escalation_level'],
        uuid.UUID(ticket_id)
    )

    # Schedule notifications
    notify_users = json.loads(rule['notify_users'])
    for user_id in notify_users:
        background_tasks.add_task(notify_user, user_id, ticket_id)

async def notify_escalation(ticket_id: str, level: int, reason: str):
    """Send escalation notifications"""
    # This would integrate with notification service
    
async def notify_user(user_id: str, ticket_id: str):
    """Notify specific user about escalation"""
    # This would send actual notifications
    