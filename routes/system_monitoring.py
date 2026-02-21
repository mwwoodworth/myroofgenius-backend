"""
System monitoring Module - Auto-generated
Part of complete ERP implementation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json
from core.brain_store import build_brain_key, dispatch_brain_store, recall_context
from core.supabase_auth import get_current_user
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


# Models
class SystemMonitoringBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class SystemMonitoringCreate(SystemMonitoringBase):
    pass

class SystemMonitoringResponse(SystemMonitoringBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=SystemMonitoringResponse)
async def create_system_monitoring(
    item: SystemMonitoringCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new system monitoring record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        INSERT INTO system_monitoring (tenant_id, name, description, status, data)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query, tenant_id, item.name, item.description, item.status,
        json.dumps(item.data) if item.data else None
    )
    monitoring_id = str(result["id"])

    dispatch_brain_store(
        key=build_brain_key(
            scope="system_monitoring",
            action="created",
            tenant_id=str(tenant_id),
        ),
        value={
            "monitoring_id": monitoring_id,
            "name": item.name,
            "status": item.status,
            "has_data": bool(item.data),
        },
        category="system_state",
        priority="medium",
    )

    return {
        **item.dict(),
        "id": monitoring_id,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[SystemMonitoringResponse])
async def list_system_monitoring(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List system monitoring records"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM system_monitoring WHERE tenant_id = $1"
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

@router.get("/{item_id}", response_model=SystemMonitoringResponse)
async def get_system_monitoring(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific system monitoring record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM system_monitoring WHERE id = $1 AND tenant_id = $2"

    row = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="System monitoring not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_system_monitoring(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update system monitoring record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    set_clauses = []
    params = []
    for i, (field, value) in enumerate(updates.items(), 1):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
            raise HTTPException(status_code=400, detail=f"Invalid field name: {field}")
        set_clauses.append(f"{field} = ${i}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    params.append(tenant_id)
    query = f"""
        UPDATE system_monitoring
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="System monitoring not found")

    dispatch_brain_store(
        key=build_brain_key(
            scope="system_monitoring",
            action="updated",
            tenant_id=str(tenant_id),
        ),
        value={
            "monitoring_id": str(result["id"]),
            "updated_fields": sorted(updates.keys()),
        },
        category="system_state",
        priority="medium",
    )

    return {"message": "System monitoring updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_system_monitoring(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete system monitoring record"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "DELETE FROM system_monitoring WHERE id = $1 AND tenant_id = $2 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="System monitoring not found")

    dispatch_brain_store(
        key=build_brain_key(
            scope="system_monitoring",
            action="deleted",
            tenant_id=str(tenant_id),
        ),
        value={
            "monitoring_id": str(result["id"]),
        },
        category="system_state",
        priority="high",
    )

    return {"message": "System monitoring deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_system_monitoring_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get system monitoring statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM system_monitoring
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)
    summary = dict(result)
    monitoring_context = await recall_context(
        query=(
            f"system monitoring events tenant {tenant_id}; "
            f"active={summary.get('active', 0)}; recent={summary.get('recent', 0)}"
        ),
        limit=5,
    )

    dispatch_brain_store(
        key=build_brain_key(
            scope="system_monitoring",
            action="stats_accessed",
            tenant_id=str(tenant_id),
        ),
        value=summary,
        category="analytics",
        priority="low",
    )

    return {
        **summary,
        "metadata": {
            "brain_context": monitoring_context,
            "brain_context_count": len(monitoring_context),
        },
    }
