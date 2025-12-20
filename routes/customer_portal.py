"""
Customer Portal Module - Task 86
Self-service customer portal
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


@router.get("/dashboard/{customer_id}", response_model=dict)
async def get_customer_dashboard(
    customer_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get customer portal dashboard"""
    # Get customer info
    customer_query = "SELECT * FROM customers WHERE id = $1"
    customer = await conn.fetchrow(customer_query, uuid.UUID(customer_id))

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get recent tickets
    tickets_query = """
        SELECT id, title, status, priority, created_at
        FROM support_tickets
        WHERE customer_id = $1
        ORDER BY created_at DESC
        LIMIT 5
    """
    tickets = await conn.fetch(tickets_query, uuid.UUID(customer_id))

    # Get recent orders
    orders_query = """
        SELECT id, order_number, total_amount, status, created_at
        FROM invoices
        WHERE customer_id = $1
        ORDER BY created_at DESC
        LIMIT 5
    """
    orders = await conn.fetch(orders_query, uuid.UUID(customer_id))

    return {
        "customer": {
            **dict(customer),
            "id": str(customer['id'])
        },
        "recent_tickets": [
            {
                **dict(ticket),
                "id": str(ticket['id'])
            } for ticket in tickets
        ],
        "recent_orders": [
            {
                **dict(order),
                "id": str(order['id'])
            } for order in orders
        ],
        "stats": {
            "open_tickets": len([t for t in tickets if t['status'] == 'open']),
            "total_spent": sum(o['total_amount'] or 0 for o in orders)
        }
    }

@router.get("/tickets/{customer_id}", response_model=List[dict])
async def get_customer_tickets(
    customer_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get all customer tickets"""
    query = """
        SELECT * FROM support_tickets
        WHERE customer_id = $1
        ORDER BY created_at DESC
    """

    rows = await conn.fetch(query, uuid.UUID(customer_id))
    return [
        {
            **dict(row),
            "id": str(row['id'])
        } for row in rows
    ]

@router.post("/profile/{customer_id}/update", response_model=dict)
async def update_customer_profile(
    customer_id: str,
    profile_data: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update customer profile"""
    # Build update query dynamically
    set_clauses = []
    params = []

    allowed_fields = ['name', 'email', 'phone', 'address', 'preferences']

    for field, value in profile_data.items():
        if field in allowed_fields:
            params.append(value)
            set_clauses.append(f"{field} = ${len(params)}")

    if not set_clauses:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    params.append(uuid.UUID(customer_id))
    query = f"""
        UPDATE customers
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params)}
        RETURNING *
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        **dict(result),
        "id": str(result['id'])
    }
