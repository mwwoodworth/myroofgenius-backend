"""
Lead Nurturing Module - Task 74
Automated lead nurturing workflows
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
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


# Models
class NurtureWorkflowCreate(BaseModel):
    name: str
    trigger_event: str
    steps: List[Dict[str, Any]]
    target_segment: Optional[str] = None
    is_active: bool = True

# Endpoints
@router.post("/workflows", response_model=dict)
async def create_nurture_workflow(
    workflow: NurtureWorkflowCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create lead nurturing workflow"""
    query = """
        INSERT INTO nurture_workflows (
            name, trigger_event, steps, target_segment, is_active
        ) VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        workflow.name,
        workflow.trigger_event,
        json.dumps(workflow.steps),
        workflow.target_segment,
        workflow.is_active
    )

    return {**dict(result), "id": str(result['id'])}

@router.get("/workflows", response_model=List[dict])
async def list_nurture_workflows(
    is_active: bool = True,
    conn: asyncpg.Connection = Depends(get_db)
):
    """List nurturing workflows"""
    query = "SELECT * FROM nurture_workflows WHERE is_active = $1"
    rows = await conn.fetch(query, is_active)
    return [{**dict(row), "id": str(row['id'])} for row in rows]
