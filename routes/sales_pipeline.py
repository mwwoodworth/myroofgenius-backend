"""
Sales Pipeline Module - Task 63
Complete sales pipeline management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
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
class PipelineCreate(BaseModel):
    pipeline_name: str
    pipeline_type: str = "standard"
    description: Optional[str] = None
    stages: List[str] = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
    stage_probabilities: Optional[Dict[str, int]] = {}
    stage_durations: Optional[Dict[str, int]] = {}
    is_default: bool = False

class PipelineResponse(BaseModel):
    id: str
    pipeline_name: str
    pipeline_type: str
    description: Optional[str]
    stages: List[str]
    stage_probabilities: Dict[str, int]
    stage_durations: Dict[str, int]
    conversion_rates: Dict[str, float]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline: PipelineCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new sales pipeline"""
    query = """
        INSERT INTO sales_pipelines (
            pipeline_name, pipeline_type, description, stages,
            stage_probabilities, stage_durations, is_default
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        pipeline.pipeline_name,
        pipeline.pipeline_type,
        pipeline.description,
        json.dumps(pipeline.stages),
        json.dumps(pipeline.stage_probabilities),
        json.dumps(pipeline.stage_durations),
        pipeline.is_default
    )

    return format_pipeline_response(result)

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    is_active: Optional[bool] = True,
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all sales pipelines"""
    query = "SELECT * FROM sales_pipelines WHERE is_active = $1"
    rows = await conn.fetch(query, is_active)
    return [format_pipeline_response(row) for row in rows]

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific pipeline"""
    query = "SELECT * FROM sales_pipelines WHERE id = $1"
    row = await conn.fetchrow(query, uuid.UUID(pipeline_id))
    if not row:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return format_pipeline_response(row)

def format_pipeline_response(row: dict) -> dict:
    """Format pipeline response"""
    return {
        **dict(row),
        "id": str(row['id']),
        "stages": json.loads(row['stages'] or '[]'),
        "stage_probabilities": json.loads(row['stage_probabilities'] or '{}'),
        "stage_durations": json.loads(row['stage_durations'] or '{}'),
        "conversion_rates": json.loads(row['conversion_rates'] or '{}')
    }
