"""
Milestone tracking Module
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

from core.supabase_auth import get_authenticated_user
import re

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
class MilestoneTrackingBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class MilestoneTrackingCreate(MilestoneTrackingBase):
    pass

class MilestoneTrackingResponse(MilestoneTrackingBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=MilestoneTrackingResponse)
async def create_milestone_tracking(
    item: MilestoneTrackingCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new milestone tracking record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    query = """
        INSERT INTO milestone_tracking (tenant_id, name, description, status, metadata)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        tenant_id,
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

@router.get("/", response_model=List[MilestoneTrackingResponse])
async def list_milestone_tracking(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all milestone tracking records"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    query = """
        SELECT * FROM milestone_tracking
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """

    rows = await conn.fetch(query, tenant_id, limit, skip)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "metadata": json.loads(row['metadata']) if row['metadata'] else {}
        }
        for row in rows
    ]

@router.get("/{item_id}", response_model=MilestoneTrackingResponse)
async def get_milestone_tracking(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get specific milestone tracking record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    query = "SELECT * FROM milestone_tracking WHERE id = $1 AND tenant_id = $2"

    row = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Milestone tracking not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_milestone_tracking(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update milestone tracking record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    # Build dynamic update query
    set_clauses = []
    params = []
    param_count = 0

    for field, value in updates.items():
        param_count += 1
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
            raise HTTPException(status_code=400, detail=f"Invalid field name: {field}")
        set_clauses.append(f"{field} = ${param_count}")
        params.append(value)

    param_count += 1
    params.append(uuid.UUID(item_id))
    param_count += 1
    params.append(tenant_id)
    query = f"""
        UPDATE milestone_tracking
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count - 1} AND tenant_id = ${param_count}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Milestone tracking not found")

    return {"message": "Milestone tracking updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_milestone_tracking(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Delete milestone tracking record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    query = "DELETE FROM milestone_tracking WHERE id = $1 AND tenant_id = $2 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Milestone tracking not found")

    return {"message": "Milestone tracking deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_milestone_tracking_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get milestone tracking statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM milestone_tracking
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)

    return dict(result)

@router.post("/bulk")
async def bulk_create_milestone_tracking(
    items: List[MilestoneTrackingCreate],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Bulk create milestone tracking records"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    created = []

    for item in items:
        query = """
            INSERT INTO milestone_tracking (tenant_id, name, description, status, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """

        result = await conn.fetchrow(
            query,
            tenant_id,
            item.name,
            item.description,
            item.status,
            json.dumps(item.metadata) if item.metadata else None
        )

        created.append(str(result['id']))

    return {"message": f"Created {len(created)} milestone tracking records", "ids": created}
