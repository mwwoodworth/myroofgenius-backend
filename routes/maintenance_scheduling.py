"""
Maintenance scheduling Module - Auto-generated
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
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Models
class MaintenanceSchedulingBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class MaintenanceSchedulingCreate(MaintenanceSchedulingBase):
    pass

class MaintenanceSchedulingResponse(MaintenanceSchedulingBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=MaintenanceSchedulingResponse)
async def create_maintenance_scheduling(
    item: MaintenanceSchedulingCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new maintenance scheduling record"""
    query = """
        INSERT INTO maintenance_scheduling (name, description, status, data)
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

@router.get("/", response_model=List[MaintenanceSchedulingResponse])
async def list_maintenance_scheduling(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List maintenance scheduling records"""
    query = "SELECT * FROM maintenance_scheduling WHERE 1=1"
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

@router.get("/{item_id}", response_model=MaintenanceSchedulingResponse)
async def get_maintenance_scheduling(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific maintenance scheduling record"""
    query = "SELECT * FROM maintenance_scheduling WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Maintenance scheduling not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "data": json.loads(row['data']) if row['data'] else {}
    }

@router.put("/{item_id}")
async def update_maintenance_scheduling(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update maintenance scheduling record"""
    if 'data' in updates:
        updates['data'] = json.dumps(updates['data'])

    set_clauses = []
    params = []
    for i, (field, value) in enumerate(updates.items(), 1):
        set_clauses.append(f"{field} = ${i}")
        params.append(value)

    params.append(uuid.UUID(item_id))
    query = f"""
        UPDATE maintenance_scheduling
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params)}
        RETURNING id
    """

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Maintenance scheduling not found")

    return {"message": "Maintenance scheduling updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_maintenance_scheduling(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete maintenance scheduling record"""
    query = "DELETE FROM maintenance_scheduling WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Maintenance scheduling not found")

    return {"message": "Maintenance scheduling deleted", "id": str(result['id'])}

@router.get("/stats/summary")
async def get_maintenance_scheduling_stats(conn: asyncpg.Connection = Depends(get_db)):
    """Get maintenance scheduling statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM maintenance_scheduling
    """

    result = await conn.fetchrow(query)
    return dict(result)
