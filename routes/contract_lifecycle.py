"""
Task 103: Contract Lifecycle
Contract creation, negotiation, and management
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

@router.get("/")
async def list_contracts(
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    db=Depends(get_db)
):
    """List all contracts"""
    query = """
        SELECT id, contract_number, title, contract_type, status,
               start_date, end_date, total_value
        FROM contracts
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::text IS NULL OR contract_type = $2)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, status, contract_type)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/")
async def create_contract(
    contract_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Create new contract"""
    contract_id = str(uuid4())
    contract_number = f"CTR-{datetime.now().strftime('%Y%m%d')}-{contract_id[:8]}"

    query = """
        INSERT INTO contracts (id, contract_number, title, contract_type,
                             parties, terms, start_date, end_date, total_value)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, contract_number
    """

    result = await db.fetchrow(
        query, contract_id, contract_number, contract_data['title'],
        contract_data.get('contract_type', 'service'),
        json.dumps(contract_data.get('parties', [])),
        json.dumps(contract_data.get('terms', {})),
        contract_data.get('start_date', date.today()),
        contract_data.get('end_date'),
        contract_data.get('total_value', 0)
    )

    return dict(result)

@router.get("/expiring")
async def get_expiring_contracts(
    days: int = Query(30, description="Days until expiration"),
    db=Depends(get_db)
):
    """Get contracts expiring soon"""
    expiry_date = date.today() + timedelta(days=days)

    query = """
        SELECT id, contract_number, title, end_date,
               EXTRACT(DAY FROM end_date - CURRENT_DATE) as days_remaining
        FROM contracts
        WHERE end_date <= $1
        AND end_date >= CURRENT_DATE
        AND status = 'active'
        ORDER BY end_date
    """
    rows = await db.fetch(query, expiry_date)
    if not rows:
        return []

    return {
        "expiring_within": f"{days} days",
        "count": len(rows),
        "contracts": [dict(row) for row in rows]
    }

@router.post("/{contract_id}/renew")
async def renew_contract(
    contract_id: str,
    renewal_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Renew a contract"""
    # Get existing contract
    contract = await db.fetchrow(
        "SELECT * FROM contracts WHERE id = $1", contract_id
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Create renewal
    renewal_id = str(uuid4())
    query = """
        INSERT INTO contract_renewals (id, original_contract_id,
                                      new_start_date, new_end_date,
                                      renewal_terms)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
    """

    await db.execute(
        query, renewal_id, contract_id,
        renewal_data['new_start_date'],
        renewal_data['new_end_date'],
        json.dumps(renewal_data.get('renewal_terms', {}))
    )

    return {"renewal_id": renewal_id, "status": "renewed"}
