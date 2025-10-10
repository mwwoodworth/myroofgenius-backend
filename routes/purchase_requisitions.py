"""
Purchase requisitions Module - Auto-generated
Part of complete ERP implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
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

# Models
class PurchaseRequisitionsBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class PurchaseRequisitionsCreate(PurchaseRequisitionsBase):
    pass

class PurchaseRequisitionsResponse(PurchaseRequisitionsBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=PurchaseRequisitionsResponse)
async def create_purchase_requisitions(
    item: PurchaseRequisitionsCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new purchase requisitions record"""
    query = """
        INSERT INTO purchase_requisitions (name, description, status, data)
        VALUES ($1, $2, $3, $4)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query, item.name, item.description, item.status,
        json.dumps(item.data) if item.data else None
    )

    return {
        **item.dict(),
        "id": str(result['id']),
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[PurchaseRequisitionsResponse])
async def list_purchase_requisitions(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List purchase requisitions records"""
    query = "SELECT * FROM purchase_requisitions WHERE 1=1"
    params = []
    param_count = 0

    if status:
        param_count += 1
        query += f" AND status = ${param_count}"
        params.append(status)

    query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
    params.extend([limit, skip])

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "data": json.loads(row['data']) if row['data'] else {}
        }
        for row in rows
    ]

@router.get("/{item_id}", response_model=PurchaseRequisitionsResponse)
async def get_purchase_requisitions(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific purchase requisitions record"""
    query = "SELECT * FROM purchase_requisitions WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Purchase requisitions not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_purchase_requisitions(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update purchase requisitions record"""
    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    set_clauses = []
    params = []
    for i, (field, value) in enumerate(updates.items(), 1):
        set_clauses.append(f"{field} = ${i}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    query = f"""
        UPDATE purchase_requisitions
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Purchase requisitions not found")

    return {"message": "Purchase requisitions updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_purchase_requisitions(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete purchase requisitions record"""
    query = "DELETE FROM purchase_requisitions WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Purchase requisitions not found")

    return {"message": "Purchase requisitions deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_purchase_requisitions_stats(conn: asyncpg.Connection = Depends(get_db)):
    """Get purchase requisitions statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM purchase_requisitions
    """

    result = await conn.fetchrow(query)
    return dict(result)
