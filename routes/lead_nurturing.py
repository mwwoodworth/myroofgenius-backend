"""
Lead Nurturing Module - Task 74
Automated lead nurturing workflows
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
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
