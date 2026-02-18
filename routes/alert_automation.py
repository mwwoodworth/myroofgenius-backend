"""
Alert automation Module - Auto-generated
Part of complete ERP implementation
SECURITY FIX: Added tenant isolation to prevent cross-tenant data access
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

from core.brain_store import build_brain_key, dispatch_brain_store
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


# Models
class AlertAutomationBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class AlertAutomationCreate(AlertAutomationBase):
    pass

class AlertAutomationResponse(AlertAutomationBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=AlertAutomationResponse)
async def create_alert_automation(
    item: AlertAutomationCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new alert automation record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        INSERT INTO alert_automation (name, description, status, data, tenant_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query, item.name, item.description, item.status,
        json.dumps(item.data) if item.data else None,
        tenant_id
    )
    alert_id = str(result["id"])

    dispatch_brain_store(
        key=build_brain_key(
            scope="alert_automation",
            action="created",
            tenant_id=str(tenant_id),
        ),
        value={
            "alert_id": alert_id,
            "name": item.name,
            "status": item.status,
            "has_data": bool(item.data),
        },
        category="alerts",
        priority="medium",
    )

    return {
        **item.dict(),
        "id": alert_id,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[AlertAutomationResponse])
async def list_alert_automation(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List alert automation records - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = "SELECT * FROM alert_automation WHERE tenant_id = $1"
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

@router.get("/{item_id}", response_model=AlertAutomationResponse)
async def get_alert_automation(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get specific alert automation record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = "SELECT * FROM alert_automation WHERE id = $1 AND tenant_id = $2"

    row = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Alert automation not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_alert_automation(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update alert automation record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    # Remove tenant_id from updates to prevent cross-tenant moves
    updates.pop('tenant_id', None)

    set_clauses = []
    params = []
    for i, (field, value) in enumerate(updates.items(), 1):
        set_clauses.append(f"{field} = ${i}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    params.append(tenant_id)
    query = f"""
        UPDATE alert_automation
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Alert automation not found")

    dispatch_brain_store(
        key=build_brain_key(
            scope="alert_automation",
            action="updated",
            tenant_id=str(tenant_id),
        ),
        value={
            "alert_id": str(result["id"]),
            "updated_fields": sorted(updates.keys()),
        },
        category="alerts",
        priority="medium",
    )

    return {"message": "Alert automation updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_alert_automation(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Delete alert automation record - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = "DELETE FROM alert_automation WHERE id = $1 AND tenant_id = $2 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert automation not found")

    dispatch_brain_store(
        key=build_brain_key(
            scope="alert_automation",
            action="deleted",
            tenant_id=str(tenant_id),
        ),
        value={
            "alert_id": str(result["id"]),
        },
        category="alerts",
        priority="high",
    )

    return {"message": "Alert automation deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_alert_automation_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get alert automation statistics - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM alert_automation
        WHERE tenant_id = $1
    """

    result = await conn.fetchrow(query, tenant_id)
    summary = dict(result)

    dispatch_brain_store(
        key=build_brain_key(
            scope="alert_automation",
            action="stats_accessed",
            tenant_id=str(tenant_id),
        ),
        value=summary,
        category="analytics",
        priority="low",
    )

    return summary
