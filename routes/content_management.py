"""
Content management Module - Auto-generated
Part of complete ERP implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

from core.supabase_auth import get_current_user

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Models
class ContentManagementBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class ContentManagementCreate(ContentManagementBase):
    pass

class ContentManagementResponse(ContentManagementBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=ContentManagementResponse)
async def create_content_management(
    item: ContentManagementCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new content management record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        INSERT INTO content_management (tenant_id, name, description, status, data)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query, tenant_id, item.name, item.description, item.status,
        json.dumps(item.data) if item.data else None
    )

    return {
        **item.dict(),
        "id": str(result['id']),
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[ContentManagementResponse])
async def list_content_management(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List content management records"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM content_management WHERE tenant_id = $1"
    params = [tenant_id]
    param_count = 1

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

@router.get("/{item_id}", response_model=ContentManagementResponse)
async def get_content_management(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific content management record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM content_management WHERE id = $1 AND tenant_id = $2"

    row = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Content management not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_content_management(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update content management record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    set_clauses = []
    params = []
    for i, (field, value) in enumerate(updates.items(), 1):
        set_clauses.append(f"{field} = ${i}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    params.append(tenant_id)
    query = f"""
        UPDATE content_management
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Content management not found")

    return {"message": "Content management updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_content_management(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete content management record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "DELETE FROM content_management WHERE id = $1 AND tenant_id = $2 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Content management not found")

    return {"message": "Content management deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_content_management_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get content management statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM content_management
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)
    return dict(result)
