"""
Extended leave management Module
Auto-generated implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
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
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Base model
class LeaveManagementExtendedBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class LeaveManagementExtendedCreate(LeaveManagementExtendedBase):
    pass

class LeaveManagementExtendedResponse(LeaveManagementExtendedBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=LeaveManagementExtendedResponse)
async def create_leave_management_extended(
    item: LeaveManagementExtendedCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new extended leave management record"""
    query = """
        INSERT INTO leave_management_extended (name, description, status, metadata)
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

@router.get("/", response_model=List[LeaveManagementExtendedResponse])
async def list_leave_management_extended(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all extended leave management records"""
    query = """
        SELECT * FROM leave_management_extended
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

@router.get("/{item_id}", response_model=LeaveManagementExtendedResponse)
async def get_leave_management_extended(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific extended leave management record"""
    query = "SELECT * FROM leave_management_extended WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Extended leave management not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_leave_management_extended(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update extended leave management record"""
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
        UPDATE leave_management_extended
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING id
    """
    params.append(uuid.UUID(item_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Extended leave management not found")

    return {"message": "Extended leave management updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_leave_management_extended(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete extended leave management record"""
    query = "DELETE FROM leave_management_extended WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Extended leave management not found")

    return {"message": "Extended leave management deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_leave_management_extended_stats(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get extended leave management statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM leave_management_extended
    """

    result = await conn.fetchrow(query)

    return dict(result)

@router.post("/bulk")
async def bulk_create_leave_management_extended(
    items: List[LeaveManagementExtendedCreate],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Bulk create extended leave management records"""
    created = []

    for item in items:
        query = """
            INSERT INTO leave_management_extended (name, description, status, metadata)
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

    return {"message": f"Created {len(created)} extended leave management records", "ids": created}
