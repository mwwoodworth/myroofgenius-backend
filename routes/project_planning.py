"""
Project planning Module
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
class ProjectPlanningBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = {}

class ProjectPlanningCreate(ProjectPlanningBase):
    pass

class ProjectPlanningResponse(ProjectPlanningBase):
    id: str
    created_at: datetime
    updated_at: datetime

# CRUD Endpoints
@router.post("/", response_model=ProjectPlanningResponse)
async def create_project_planning(
    item: ProjectPlanningCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new project planning record"""
    query = """
        INSERT INTO project_planning (name, description, status, metadata)
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

@router.get("/", response_model=List[ProjectPlanningResponse])
async def list_project_planning(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all project planning records"""
    query = """
        SELECT * FROM project_planning
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

@router.get("/{item_id}", response_model=ProjectPlanningResponse)
async def get_project_planning(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific project planning record"""
    query = "SELECT * FROM project_planning WHERE id = $1"

    row = await conn.fetchrow(query, uuid.UUID(item_id))
    if not row:
        raise HTTPException(status_code=404, detail="Project planning not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "metadata": json.loads(row['metadata']) if row['metadata'] else {}
    }

@router.put("/{item_id}")
async def update_project_planning(
    item_id: str,
    updates: Dict[str, Any],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update project planning record"""
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
        UPDATE project_planning
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING id
    """
    params.append(uuid.UUID(item_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Project planning not found")

    return {"message": "Project planning updated", "id": str(result['id'])}

@router.delete("/{item_id}")
async def delete_project_planning(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Delete project planning record"""
    query = "DELETE FROM project_planning WHERE id = $1 RETURNING id"

    result = await conn.fetchrow(query, uuid.UUID(item_id))
    if not result:
        raise HTTPException(status_code=404, detail="Project planning not found")

    return {"message": "Project planning deleted", "id": str(result['id'])}

# Additional specialized endpoints
@router.get("/stats/summary")
async def get_project_planning_stats(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get project planning statistics"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM project_planning
    """

    result = await conn.fetchrow(query)

    return dict(result)

@router.post("/bulk")
async def bulk_create_project_planning(
    items: List[ProjectPlanningCreate],
    conn: asyncpg.Connection = Depends(get_db)
):
    """Bulk create project planning records"""
    created = []

    for item in items:
        query = """
            INSERT INTO project_planning (name, description, status, metadata)
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

    return {"message": f"Created {len(created)} project planning records", "ids": created}
