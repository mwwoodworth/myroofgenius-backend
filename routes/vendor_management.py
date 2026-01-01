"""
Task 101: Vendor Management
Complete vendor lifecycle management system
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import asyncpg
import json
import asyncio
from decimal import Decimal
from core.supabase_auth import get_authenticated_user

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


@router.get("/")
async def list_vendors(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all vendors with filtering"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        SELECT id, vendor_name, vendor_type, status, rating,
               contact_info, created_at
        FROM vendors
        WHERE tenant_id = $1
        AND ($2::text IS NULL OR vendor_type = $2)
        AND ($3::text IS NULL OR status = $3)
        ORDER BY vendor_name
        LIMIT $4 OFFSET $5
    """
    rows = await db.fetch(query, UUID(tenant_id), category, status, limit, offset)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/")
async def create_vendor(
    vendor_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new vendor"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    vendor_id = str(uuid4())
    query = """
        INSERT INTO vendors (id, tenant_id, vendor_name, vendor_type, contact_info,
                           tax_id, payment_terms, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
        RETURNING id
    """
    await db.execute(
        query, vendor_id, UUID(tenant_id), vendor_data['vendor_name'],
        vendor_data.get('vendor_type', 'supplier'),
        json.dumps(vendor_data.get('contact_info', {})),
        vendor_data.get('tax_id'), vendor_data.get('payment_terms', 'net30')
    )
    return {"id": vendor_id, "status": "created"}

@router.get("/{vendor_id}")
async def get_vendor(
    vendor_id: str,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get vendor details"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM vendors WHERE id = $1 AND tenant_id = $2"
    row = await db.fetchrow(query, vendor_id, UUID(tenant_id))
    if not row:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return dict(row)

@router.get("/{vendor_id}/contracts")
async def get_vendor_contracts(
    vendor_id: str,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get vendor contracts"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    # First verify vendor belongs to tenant
    verify_query = "SELECT id FROM vendors WHERE id = $1 AND tenant_id = $2"
    vendor = await db.fetchrow(verify_query, vendor_id, UUID(tenant_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    query = """
        SELECT id, contract_number, contract_type, status,
               start_date, end_date, value
        FROM contracts
        WHERE vendor_id = $1 AND tenant_id = $2
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, vendor_id, UUID(tenant_id))
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/{vendor_id}/evaluate")
async def evaluate_vendor(
    vendor_id: str,
    evaluation: Dict[str, Any],
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Evaluate vendor performance"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    # Verify vendor belongs to tenant
    verify_query = "SELECT id FROM vendors WHERE id = $1 AND tenant_id = $2"
    vendor = await db.fetchrow(verify_query, vendor_id, UUID(tenant_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    eval_id = str(uuid4())
    query = """
        INSERT INTO vendor_evaluations (id, tenant_id, vendor_id, quality_score,
                                      delivery_score, price_score,
                                      service_score, overall_score)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
    """

    # Calculate overall score
    scores = [
        evaluation.get('quality_score', 0),
        evaluation.get('delivery_score', 0),
        evaluation.get('price_score', 0),
        evaluation.get('service_score', 0)
    ]
    overall = sum(scores) / len(scores)

    await db.execute(
        query, eval_id, UUID(tenant_id), vendor_id,
        evaluation.get('quality_score', 0),
        evaluation.get('delivery_score', 0),
        evaluation.get('price_score', 0),
        evaluation.get('service_score', 0),
        overall
    )

    return {"id": eval_id, "overall_score": overall}
