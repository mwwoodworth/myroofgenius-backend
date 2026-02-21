"""Lead scoring configuration and preview routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.request_safety import parse_uuid, require_tenant_id, sanitize_payload, sanitize_text
from core.supabase_auth import get_current_user
import re

router = APIRouter()


async def get_db(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class LeadScoringBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active", min_length=2, max_length=40)
    data: Dict[str, Any] = Field(default_factory=dict)


class LeadScoringCreate(LeadScoringBase):
    pass


class LeadScoringUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, min_length=2, max_length=40)
    data: Optional[Dict[str, Any]] = None


class LeadScoringResponse(LeadScoringBase):
    id: str
    created_at: datetime
    updated_at: datetime


class LeadScorePreviewRequest(BaseModel):
    rating: Optional[str] = Field(default=None, max_length=20)
    company_size: Optional[str] = Field(default=None, max_length=50)
    annual_revenue: Optional[float] = Field(default=None, ge=0)
    lead_source: Optional[str] = Field(default=None, max_length=50)
    lead_status: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    mobile: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=120)
    state: Optional[str] = Field(default=None, max_length=120)
    country: Optional[str] = Field(default=None, max_length=120)


def calculate_lead_score(lead: Dict[str, Any]) -> int:
    score = 0

    rating = (lead.get("rating") or "").lower()
    if rating == "hot":
        score += 30
    elif rating == "warm":
        score += 20
    elif rating == "cold":
        score += 10

    company_size = (lead.get("company_size") or "").lower()
    if "enterprise" in company_size or "1000+" in company_size:
        score += 25
    elif "mid" in company_size or "100-999" in company_size:
        score += 15
    elif "small" in company_size or "10-99" in company_size:
        score += 10

    revenue = lead.get("annual_revenue", 0) or 0
    if revenue >= 10000000:
        score += 25
    elif revenue >= 1000000:
        score += 15
    elif revenue >= 100000:
        score += 10

    source = (lead.get("lead_source") or "").lower()
    if source in {"referral", "partner"}:
        score += 20
    elif source in {"website", "event"}:
        score += 15
    elif source in {"email", "social_media"}:
        score += 10
    elif source in {"cold_outreach", "advertisement"}:
        score += 5

    status = (lead.get("lead_status") or "").lower()
    if status in {"qualified", "proposal", "negotiation"}:
        score += 20
    elif status in {"qualifying", "contacted"}:
        score += 10
    elif status == "new":
        score += 5

    if lead.get("email"):
        score += 5
    if lead.get("phone") or lead.get("mobile"):
        score += 5
    if lead.get("website"):
        score += 3
    if all([lead.get("city"), lead.get("state"), lead.get("country")]):
        score += 7

    return min(score, 100)


@router.post("/", response_model=LeadScoringResponse)
async def create_lead_scoring(
    item: LeadScoringCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)

    row = await conn.fetchrow(
        """
        INSERT INTO lead_scoring (tenant_id, name, description, status, data)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
        """,
        tenant_id,
        sanitize_text(item.name, max_length=200),
        sanitize_text(item.description, max_length=1000),
        sanitize_text(item.status, max_length=40),
        sanitize_payload(item.data),
    )

    return {
        **item.model_dump(),
        "id": str(row["id"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/", response_model=List[LeadScoringResponse])
async def list_lead_scoring(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)

    query = "SELECT * FROM lead_scoring WHERE tenant_id = $1"
    params: List[Any] = [tenant_id]

    if status:
        params.append(sanitize_text(status, max_length=40))
        query += f" AND status = ${len(params)}"

    params.extend([limit, skip])
    query += f" ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row["id"]),
            "data": row["data"] if row["data"] else {},
        }
        for row in rows
    ]


@router.get("/{item_id}", response_model=LeadScoringResponse)
async def get_lead_scoring(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "SELECT * FROM lead_scoring WHERE tenant_id = $1 AND id = $2",
        tenant_id,
        item_uuid,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lead scoring not found")

    return {
        **dict(row),
        "id": str(row["id"]),
        "data": row["data"] if row["data"] else {},
    }


@router.put("/{item_id}")
async def update_lead_scoring(
    item_id: str,
    updates: LeadScoringUpdate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    if "name" in update_data:
        update_data["name"] = sanitize_text(update_data["name"], max_length=200)
    if "description" in update_data:
        update_data["description"] = sanitize_text(update_data["description"], max_length=1000)
    if "status" in update_data:
        update_data["status"] = sanitize_text(update_data["status"], max_length=40)
    if "data" in update_data:
        update_data["data"] = sanitize_payload(update_data["data"] or {})

    params: List[Any] = [tenant_id]
    set_clauses: List[str] = []
    for field, value in update_data.items():
        params.append(value)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
            raise HTTPException(status_code=400, detail=f"Invalid field name: {field}")
        set_clauses.append(f"{field} = ${len(params)}")

    params.append(item_uuid)
    row = await conn.fetchrow(
        f"""
        UPDATE lead_scoring
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE tenant_id = $1 AND id = ${len(params)}
        RETURNING id
        """,
        *params,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Lead scoring not found")

    return {"message": "Lead scoring updated", "id": str(row["id"])}


@router.delete("/{item_id}")
async def delete_lead_scoring(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "DELETE FROM lead_scoring WHERE tenant_id = $1 AND id = $2 RETURNING id",
        tenant_id,
        item_uuid,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lead scoring not found")

    return {"message": "Lead scoring deleted", "id": str(row["id"])}


@router.get("/stats/summary")
async def get_lead_scoring_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    tenant_id = require_tenant_id(current_user)

    result = await conn.fetchrow(
        """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM lead_scoring
        WHERE tenant_id = $1
        """,
        tenant_id,
    )
    return dict(result)


@router.post("/calculate")
async def calculate_score_preview(
    payload: LeadScorePreviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    require_tenant_id(current_user)
    score = calculate_lead_score(payload.model_dump())
    return {"score": score}
