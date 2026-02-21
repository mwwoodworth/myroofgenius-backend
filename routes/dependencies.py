"""
Task dependencies Module
Auto-generated implementation
SECURITY FIX: Added tenant isolation to prevent cross-tenant data access
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
class DependenciesBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class DependenciesCreate(DependenciesBase):
    pass

class DependenciesResponse(DependenciesBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=DependenciesResponse)
async def create_dependencies(
    item: DependenciesCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new task dependencies record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        INSERT INTO dependencies (name, description, status, metadata, tenant_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        item.name,
        item.description,
        item.status,
        json.dumps(item.metadata) if item.metadata else None,
        tenant_id
    )

    return {
        **item.dict(),
        "id": str(result['id']),
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[DependenciesResponse])
async def list_dependencies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all task dependencies records - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        SELECT * FROM dependencies
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

@router.get("/{item_id}", response_model=DependenciesResponse)
async def get_dependencies(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get specific task dependencies record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = "SELECT * FROM dependencies WHERE id = $1 AND tenant_id = $2"

    row = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task dependencies not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_dependencies(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update task dependencies record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    # Remove tenant_id from updates to prevent cross-tenant moves
    updates.pop('tenant_id', None)

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
        UPDATE dependencies
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count - 1} AND tenant_id = ${param_count}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Task dependencies not found")

    return {"message": "Task dependencies updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_dependencies(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Delete task dependencies record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = "DELETE FROM dependencies WHERE id = $1 AND tenant_id = $2 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task dependencies not found")

    return {"message": "Task dependencies deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_dependencies_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get task dependencies statistics - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM dependencies
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)

    return dict(result)

@router.post("/bulk")
async def bulk_create_dependencies(
    items: List[DependenciesCreate],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Bulk create task dependencies records - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    created = []

    for item in items:
        query = """
            INSERT INTO dependencies (name, description, status, metadata, tenant_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """

        result = await conn.fetchrow(
            query,
            item.name,
            item.description,
            item.status,
            json.dumps(item.metadata) if item.metadata else None,
            tenant_id
        )

        created.append(str(result['id']))

    return {"message": f"Created {len(created)} task dependencies records", "ids": created}
