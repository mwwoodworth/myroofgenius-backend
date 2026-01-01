"""
Mobile reports Module - Auto-generated
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
class MobileReportsBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class MobileReportsCreate(MobileReportsBase):
    pass

class MobileReportsResponse(MobileReportsBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=MobileReportsResponse)
async def create_mobile_reports(
    item: MobileReportsCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new mobile reports record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        INSERT INTO mobile_reports (tenant_id, name, description, status, data)
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

@router.get("/", response_model=List[MobileReportsResponse])
async def list_mobile_reports(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List mobile reports records"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM mobile_reports WHERE tenant_id = $1"
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

@router.get("/{item_id}", response_model=MobileReportsResponse)
async def get_mobile_reports(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific mobile reports record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM mobile_reports WHERE tenant_id = $1 AND id = $2"

    row = await conn.fetchrow(query, tenant_id, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Mobile reports not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_mobile_reports(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update mobile reports record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    set_clauses = []
    params = [tenant_id]
    param_count = 1
    for field, value in updates.items():
        param_count += 1
        set_clauses.append(f"{field} = ${param_count}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    query = f"""
        UPDATE mobile_reports
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE tenant_id = $1 AND id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Mobile reports not found")

    return {"message": "Mobile reports updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_mobile_reports(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete mobile reports record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "DELETE FROM mobile_reports WHERE tenant_id = $1 AND id = $2 RETURNING id"

    result = await conn.fetchrow(query, tenant_id, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Mobile reports not found")

    return {"message": "Mobile reports deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_mobile_reports_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get mobile reports statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM mobile_reports
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)
    return dict(result)
