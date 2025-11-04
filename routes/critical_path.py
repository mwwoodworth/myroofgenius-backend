"""
Critical path analysis Module
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
        password="Brain0ps2O2S",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Base model
class CriticalPathBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class CriticalPathCreate(CriticalPathBase):
    pass

class CriticalPathResponse(CriticalPathBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=CriticalPathResponse)
async def create_critical_path(
    item: CriticalPathCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new critical path analysis record"""
    query = """
        INSERT INTO critical_path (name, description, status, metadata)
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

@router.get("/", response_model=List[CriticalPathResponse])
async def list_critical_path(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all critical path analysis records"""
    query = """
        SELECT * FROM critical_path
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

@router.get("/{item_id}", response_model=CriticalPathResponse)
async def get_critical_path(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific critical path analysis record"""
    query = "SELECT * FROM critical_path WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Critical path analysis not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_critical_path(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update critical path analysis record"""
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
        UPDATE critical_path
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING id
    """
    params.append(uuid.UUID(item_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Critical path analysis not found")

    return {"message": "Critical path analysis updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_critical_path(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete critical path analysis record"""
    query = "DELETE FROM critical_path WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Critical path analysis not found")

    return {"message": "Critical path analysis deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_critical_path_stats(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get critical path analysis statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM critical_path
    """

    result = await conn.fetchrow(query)

    return dict(result)

@router.post("/bulk")
async def bulk_create_critical_path(
    items: List[CriticalPathCreate],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Bulk create critical path analysis records"""
    created = []

    for item in items:
        query = """
            INSERT INTO critical_path (name, description, status, metadata)
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

    return {"message": f"Created {len(created)} critical path analysis records", "ids": created}
