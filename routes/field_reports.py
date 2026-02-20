"""
Field Reports Module - Real Implementation for Field Genius
Part of BrainOps Ecosystem - Absolute Perfection Initiative
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json
from core.supabase_auth import get_current_user

router = APIRouter()

# Database connection dependency
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        # Fallback to creating a pool if not available (e.g. testing)
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn

# Models
class FieldReportBase(BaseModel):
    type: str = Field(..., description="Type of report: photo, note, measurement, issue, upload")
    content: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    weather: Optional[Dict[str, Any]] = None
    media_urls: Optional[List[str]] = []
    status: str = "pending"

class FieldReportCreate(FieldReportBase):
    pass

class FieldReportResponse(FieldReportBase):
    id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=FieldReportResponse)
async def create_field_report(
    item: FieldReportCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new field report entry"""
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("sub") # Supabase user ID

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = """
        INSERT INTO field_reports (tenant_id, user_id, type, content, location, weather, media_urls, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id, created_at, updated_at
    """

    try:
        result = await conn.fetchrow(
            query, 
            tenant_id, 
            user_id,
            item.type, 
            item.content, 
            json.dumps(item.location) if item.location else None,
            json.dumps(item.weather) if item.weather else None,
            item.media_urls,
            item.status
        )
    except asyncpg.check_violation_error as e:
         raise HTTPException(status_code=400, detail=f"Invalid data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return {
        **item.dict(),
        "id": str(result['id']),
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/", response_model=List[FieldReportResponse])
async def list_field_reports(
    type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List field reports with pagination"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    query = "SELECT * FROM field_reports WHERE tenant_id = $1"
    params = [tenant_id]
    param_count = 1

    if type:
        param_count += 1
        query += f" AND type = ${param_count}"
        params.append(type)

    query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
    params.extend([limit, skip])

    rows = await conn.fetch(query, *params)

    return [
        {
            "id": str(row['id']),
            "tenant_id": str(row['tenant_id']),
            "user_id": str(row['user_id']),
            "type": row['type'],
            "content": row['content'],
            "location": json.loads(row['location']) if row['location'] else None,
            "weather": json.loads(row['weather']) if row['weather'] else None,
            "media_urls": row['media_urls'] or [],
            "status": row['status'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
        for row in rows
    ]
