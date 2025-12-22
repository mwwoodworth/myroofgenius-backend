"""
Campaign Management Module - Task 71
Complete marketing campaign management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import uuid
import json

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
class CampaignCreate(BaseModel):
    name: str
    campaign_type: str = Field(default="email", description="email, social, ppc, content, event")
    target_audience: Optional[str] = None
    budget: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    objectives: Optional[List[str]] = []
    channels: List[str] = ["email"]
    content: Optional[Dict[str, Any]] = {}
    status: str = "draft"

class CampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: str
    target_audience: Optional[str]
    budget: Optional[float]
    start_date: datetime
    end_date: Optional[datetime]
    objectives: List[str]
    channels: List[str]
    content: Dict[str, Any]
    status: str
    performance_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new marketing campaign"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    query = """
        INSERT INTO marketing_campaigns (
            name, campaign_type, target_audience, budget,
            start_date, end_date, objectives, channels,
            content, status, tenant_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        campaign.name,
        campaign.campaign_type,
        campaign.target_audience,
        campaign.budget,
        campaign.start_date,
        campaign.end_date,
        json.dumps(campaign.objectives),
        json.dumps(campaign.channels),
        json.dumps(campaign.content),
        campaign.status,
        tenant_id
    )

    return format_campaign_response(result)

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    request: Request,
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all marketing campaigns"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    params = [tenant_id]
    conditions = ["tenant_id = $1"]

    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    if campaign_type:
        params.append(campaign_type)
        conditions.append(f"campaign_type = ${len(params)}")

    where_clause = " WHERE " + " AND ".join(conditions)

    params.extend([limit, offset])
    query = f"""
        SELECT * FROM marketing_campaigns
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [format_campaign_response(row) for row in rows]

@router.post("/{campaign_id}/launch")
async def launch_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Launch a marketing campaign"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    # Update status
    query = """
        UPDATE marketing_campaigns
        SET status = 'active',
            start_date = NOW()
        WHERE id = $1 AND status = 'draft' AND tenant_id = $2
        RETURNING *
    """

    result = await conn.fetchrow(query, uuid.UUID(campaign_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found or already launched")

    # Schedule campaign tasks
    background_tasks.add_task(execute_campaign_tasks, campaign_id)

    return {"status": "launched", "campaign_id": campaign_id}

async def execute_campaign_tasks(campaign_id: str):
    """Execute campaign tasks in background"""
    # This would handle actual campaign execution
    
def format_campaign_response(row: dict) -> dict:
    """Format campaign response"""
    return {
        **dict(row),
        "id": str(row['id']),
        "objectives": json.loads(row.get('objectives', '[]')),
        "channels": json.loads(row.get('channels', '[]')),
        "content": json.loads(row.get('content', '{}')),
        "performance_metrics": json.loads(row.get('performance_metrics', '{}'))
    }
