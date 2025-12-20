"""
Overtime tracking Module
Auto-generated implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Base model
class OvertimeTrackingBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class OvertimeTrackingCreate(OvertimeTrackingBase):
    pass

class OvertimeTrackingResponse(OvertimeTrackingBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=OvertimeTrackingResponse)
async def create_overtime_tracking(
    item: OvertimeTrackingCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new overtime tracking record"""
    query = """
        INSERT INTO overtime_tracking (name, description, status, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        item.name,
        item.description,
        item.status,
        json.dumps(item.metadata) if item.metadata else None
    )

    return {
        **item.dict(),
        "id": str(result['id']),
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[OvertimeTrackingResponse])
async def list_overtime_tracking(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all overtime tracking records"""
    query = """
        SELECT * FROM overtime_tracking
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
    """

    rows = await conn.fetch(query, limit, skip)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "metadata": json.loads(row['metadata']) if row['metadata'] else {}
        }
        for row in rows
    ]

@router.get("/{item_id}", response_model=OvertimeTrackingResponse)
async def get_overtime_tracking(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific overtime tracking record"""
    query = "SELECT * FROM overtime_tracking WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Overtime tracking not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_overtime_tracking(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update overtime tracking record"""
    # Build dynamic update query
    set_clauses = []
    params = []
    param_count = 0

    for field, value in updates.items():
        param_count += 1
        set_clauses.append(f"{field} = ${param_count}")
        params.append(value)

    param_count += 1
    query = f"""
        UPDATE overtime_tracking
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING id
    """
    params.append(uuid.UUID(item_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Overtime tracking not found")

    return {"message": "Overtime tracking updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_overtime_tracking(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete overtime tracking record"""
    query = "DELETE FROM overtime_tracking WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Overtime tracking not found")

    return {"message": "Overtime tracking deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_overtime_tracking_stats(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get overtime tracking statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM overtime_tracking
    """

    result = await conn.fetchrow(query)

    return dict(result)

@router.post("/bulk")
async def bulk_create_overtime_tracking(
    items: List[OvertimeTrackingCreate],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Bulk create overtime tracking records"""
    created = []

    for item in items:
        query = """
            INSERT INTO overtime_tracking (name, description, status, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """

        result = await conn.fetchrow(
            query,
            item.name,
            item.description,
            item.status,
            json.dumps(item.metadata) if item.metadata else None
        )

        created.append(str(result['id']))

    return {"message": f"Created {len(created)} overtime tracking records", "ids": created}
