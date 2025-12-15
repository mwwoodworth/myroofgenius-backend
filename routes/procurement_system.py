"""
Task 102: Procurement System
Purchase orders, requisitions, and approvals
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import asyncpg
import json
import asyncio
from decimal import Decimal

router = APIRouter()

# Database connection
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

@router.get("/orders")
async def list_purchase_orders(
    status: Optional[str] = None,
    vendor_id: Optional[str] = None,
    db=Depends(get_db)
):
    """List purchase orders"""
    query = """
        SELECT id, po_number, vendor_id, total_amount, status,
               order_date, delivery_date
        FROM purchase_orders
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::uuid IS NULL OR vendor_id = $2::uuid)
        ORDER BY created_at DESC
        LIMIT 100
    """
    rows = await db.fetch(query, status, vendor_id)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/orders")
async def create_purchase_order(
    order_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Create purchase order"""
    po_id = str(uuid4())
    po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{po_id[:8]}"

    query = """
        INSERT INTO purchase_orders (id, po_number, vendor_id, items,
                                   total_amount, status)
        VALUES ($1, $2, $3, $4, $5, 'draft')
        RETURNING id, po_number
    """

    result = await db.fetchrow(
        query, po_id, po_number, order_data['vendor_id'],
        json.dumps(order_data.get('items', [])),
        order_data.get('total_amount', 0)
    )

    return dict(result)

@router.get("/requisitions")
async def list_requisitions(
    status: Optional[str] = None,
    department: Optional[str] = None,
    db=Depends(get_db)
):
    """List purchase requisitions"""
    query = """
        SELECT id, req_number, department, requested_by, total_amount,
               status, created_at
        FROM requisitions
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::text IS NULL OR department = $2)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, status, department)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/rfq")
async def create_rfq(
    rfq_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Create request for quotation"""
    rfq_id = str(uuid4())
    query = """
        INSERT INTO rfqs (id, title, description, items, deadline, status)
        VALUES ($1, $2, $3, $4, $5, 'open')
        RETURNING id
    """
    await db.execute(
        query, rfq_id, rfq_data['title'], rfq_data.get('description'),
        json.dumps(rfq_data.get('items', [])),
        rfq_data.get('deadline', datetime.now() + timedelta(days=7))
    )
    return {"id": rfq_id, "status": "created"}

@router.get("/spend-analysis")
async def spend_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db=Depends(get_db)
):
    """Analyze procurement spending"""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    query = """
        SELECT
            DATE_TRUNC('month', order_date) as month,
            COUNT(*) as order_count,
            SUM(total_amount) as total_spend,
            AVG(total_amount) as avg_order_value
        FROM purchase_orders
        WHERE order_date BETWEEN $1 AND $2
        AND status != 'cancelled'
        GROUP BY month
        ORDER BY month DESC
    """
    rows = await db.fetch(query, start_date, end_date)
    if not rows:
        return []

    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "monthly_data": [dict(row) for row in rows],
        "total_spend": sum(float(row['total_spend'] or 0) for row in rows),
        "total_orders": sum(row['order_count'] for row in rows)
    }
