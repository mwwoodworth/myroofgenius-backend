"""Lead management with tenant isolation, lifecycle tracking, and scoring."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from core.request_safety import parse_uuid, require_tenant_id, sanitize_payload, sanitize_text
from core.supabase_auth import get_authenticated_user
import re

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_db(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CONVERTED = "converted"
    LOST = "lost"
    NURTURING = "nurturing"
    UNQUALIFIED = "unqualified"


class LeadSource(str, Enum):
    WEBSITE = "website"
    EMAIL = "email"
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    PARTNER = "partner"
    EVENT = "event"
    COLD_OUTREACH = "cold_outreach"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"


class LeadRating(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"
    FOLLOWUP = "followup"
    NOTE = "note"
    TASK = "task"


class LeadBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    mobile: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=100)
    company_size: Optional[str] = Field(default=None, max_length=50)
    annual_revenue: Optional[float] = Field(default=None, ge=0)
    lead_source: LeadSource
    lead_status: LeadStatus = LeadStatus.NEW
    rating: Optional[LeadRating] = None
    assigned_to: Optional[str] = None
    territory_id: Optional[str] = None
    address_line1: Optional[str] = Field(default=None, max_length=500)
    address_line2: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=200)
    state: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    mobile: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=100)
    company_size: Optional[str] = Field(default=None, max_length=50)
    annual_revenue: Optional[float] = Field(default=None, ge=0)
    lead_source: Optional[LeadSource] = None
    lead_status: Optional[LeadStatus] = None
    rating: Optional[LeadRating] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class LeadResponse(LeadBase):
    id: str
    lead_number: str
    lead_score: int
    last_contacted_at: Optional[datetime] = None
    converted_to_customer: bool = False
    converted_customer_id: Optional[str] = None
    converted_at: Optional[datetime] = None
    converted_by: Optional[str] = None
    lost_reason: Optional[str] = None
    lost_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class LeadActivity(BaseModel):
    activity_type: ActivityType
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    outcome: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    assigned_to: Optional[str] = None


class LeadActivityResponse(LeadActivity):
    id: str
    lead_id: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None


class LeadConversion(BaseModel):
    customer_id: str
    notes: Optional[str] = None


class LeadQualification(BaseModel):
    budget: Optional[float] = Field(default=None, ge=0)
    authority: Optional[bool] = None
    need: Optional[str] = None
    timeline: Optional[str] = None
    score_adjustment: Optional[int] = Field(default=None, ge=-100, le=100)


def _serialize_lead(row: asyncpg.Record) -> Dict[str, Any]:
    payload = dict(row)
    payload["id"] = str(row["id"])
    if payload.get("territory_id"):
        payload["territory_id"] = str(payload["territory_id"])
    if payload.get("converted_customer_id"):
        payload["converted_customer_id"] = str(payload["converted_customer_id"])
    return payload


async def _ensure_lifecycle_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_lifecycle_events (
            id UUID PRIMARY KEY,
            tenant_id VARCHAR(255) NOT NULL,
            lead_id UUID NOT NULL,
            event_type VARCHAR(120) NOT NULL,
            event_payload JSONB,
            created_by VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_lead_lifecycle_events_tenant_lead
        ON lead_lifecycle_events(tenant_id, lead_id, created_at DESC)
        """
    )


async def _record_lifecycle_event(
    conn: asyncpg.Connection,
    *,
    tenant_id: str,
    lead_id: uuid.UUID,
    event_type: str,
    created_by: Optional[str],
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    await _ensure_lifecycle_table(conn)
    await conn.execute(
        """
        INSERT INTO lead_lifecycle_events (
            id, tenant_id, lead_id, event_type, event_payload, created_by, created_at
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, NOW())
        """,
        uuid.uuid4(),
        tenant_id,
        lead_id,
        sanitize_text(event_type, max_length=120),
        json.dumps(sanitize_payload(payload or {})),
        sanitize_text(created_by, max_length=255) if created_by else None,
    )


async def generate_lead_number(conn: asyncpg.Connection, tenant_id: str) -> str:
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM leads WHERE tenant_id = $1",
        tenant_id,
    )
    return f"LEAD-{(count or 0) + 1:05d}"


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


async def _assign_lead_owner(
    conn: asyncpg.Connection,
    *,
    tenant_id: str,
    provided_assignee: Optional[str],
) -> Optional[str]:
    if provided_assignee:
        return sanitize_text(provided_assignee, max_length=255)

    # Best-effort auto-assignment with tenant filtering.
    assignee = await conn.fetchval(
        """
        SELECT assigned_to
        FROM leads
        WHERE tenant_id = $1
          AND assigned_to IS NOT NULL
        GROUP BY assigned_to
        ORDER BY COUNT(*) ASC
        LIMIT 1
        """,
        tenant_id,
    )
    return sanitize_text(str(assignee), max_length=255) if assignee else None


@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    try:
        lead_number = await generate_lead_number(conn, tenant_id)
        lead_data = sanitize_payload(lead.model_dump())
        lead_score = calculate_lead_score(lead_data)
        assigned_to = await _assign_lead_owner(
            conn,
            tenant_id=tenant_id,
            provided_assignee=lead_data.get("assigned_to"),
        )

        row = await conn.fetchrow(
            """
            INSERT INTO leads (
                lead_number, company_name, contact_name, email, phone, mobile,
                website, industry, company_size, annual_revenue, lead_source,
                lead_status, lead_score, rating, assigned_to, territory_id,
                address_line1, address_line2, city, state, postal_code, country,
                description, notes, tags, created_by, tenant_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
            ) RETURNING *
            """,
            lead_number,
            sanitize_text(lead_data.get("company_name"), max_length=200),
            sanitize_text(lead_data.get("contact_name"), max_length=200),
            sanitize_text(lead_data.get("email"), max_length=255),
            sanitize_text(lead_data.get("phone"), max_length=50),
            sanitize_text(lead_data.get("mobile"), max_length=50),
            sanitize_text(lead_data.get("website"), max_length=500),
            sanitize_text(lead_data.get("industry"), max_length=100),
            sanitize_text(lead_data.get("company_size"), max_length=50),
            lead_data.get("annual_revenue"),
            sanitize_text(lead_data.get("lead_source"), max_length=50),
            sanitize_text(lead_data.get("lead_status"), max_length=50),
            lead_score,
            sanitize_text(lead_data.get("rating"), max_length=20),
            assigned_to,
            parse_uuid(lead_data["territory_id"], field_name="territory_id")
            if lead_data.get("territory_id")
            else None,
            sanitize_text(lead_data.get("address_line1"), max_length=500),
            sanitize_text(lead_data.get("address_line2"), max_length=500),
            sanitize_text(lead_data.get("city"), max_length=200),
            sanitize_text(lead_data.get("state"), max_length=100),
            sanitize_text(lead_data.get("postal_code"), max_length=50),
            sanitize_text(lead_data.get("country"), max_length=100),
            sanitize_text(lead_data.get("description"), max_length=5000),
            sanitize_text(lead_data.get("notes"), max_length=5000),
            lead_data.get("tags", []),
            current_user.get("id"),
            tenant_id,
        )

        lead_id = row["id"]
        await _record_lifecycle_event(
            conn,
            tenant_id=tenant_id,
            lead_id=lead_id,
            event_type="lead_created",
            created_by=str(current_user.get("id") or ""),
            payload={"lead_score": lead_score, "assigned_to": assigned_to},
        )

        background_tasks.add_task(
            track_lead_activity,
            str(lead_id),
            "Lead created",
            str(current_user.get("id") or ""),
            tenant_id,
        )

        return _serialize_lead(row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create_lead failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    request: Request,
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    rating: Optional[LeadRating] = None,
    assigned_to: Optional[str] = None,
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    converted: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    try:
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenant_id]

        if status:
            params.append(status.value)
            conditions.append(f"lead_status = ${len(params)}")

        if source:
            params.append(source.value)
            conditions.append(f"lead_source = ${len(params)}")

        if rating:
            params.append(rating.value)
            conditions.append(f"rating = ${len(params)}")

        if assigned_to:
            params.append(sanitize_text(assigned_to, max_length=255))
            conditions.append(f"assigned_to = ${len(params)}")

        if min_score is not None:
            params.append(min_score)
            conditions.append(f"lead_score >= ${len(params)}")

        if converted is not None:
            params.append(converted)
            conditions.append(f"converted_to_customer = ${len(params)}")

        params.extend([limit, skip])
        query = f"""
            SELECT * FROM leads
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${len(params)-1} OFFSET ${len(params)}
        """

        rows = await conn.fetch(query, *params)
        return [_serialize_lead(row) for row in rows]
    except Exception as exc:
        logger.exception("list_leads failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    lead_uuid = parse_uuid(lead_id, field_name="lead_id")
    row = await conn.fetchrow(
        "SELECT * FROM leads WHERE id = $1 AND tenant_id = $2",
        lead_uuid,
        tenant_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    return _serialize_lead(row)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    updates: LeadUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")

    existing = await conn.fetchrow(
        "SELECT * FROM leads WHERE id = $1 AND tenant_id = $2",
        lead_uuid,
        tenant_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")
    existing_data = dict(existing)

    update_data = sanitize_payload(updates.model_dump(exclude_unset=True))
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    score_fields = {"rating", "company_size", "annual_revenue", "lead_source", "lead_status", "email", "phone", "mobile", "website", "city", "state", "country"}
    if any(field in update_data for field in score_fields):
        merged = {**existing_data, **update_data}
        update_data["lead_score"] = calculate_lead_score(merged)

    if "assigned_to" in update_data:
        update_data["assigned_to"] = await _assign_lead_owner(
            conn,
            tenant_id=tenant_id,
            provided_assignee=update_data.get("assigned_to"),
        )

    set_clauses: List[str] = []
    params: List[Any] = []
    for field, value in update_data.items():
        params.append(value)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
            raise HTTPException(status_code=400, detail=f"Invalid field name: {field}")
        set_clauses.append(f"{field} = ${len(params)}")

    params.extend([datetime.utcnow(), current_user.get("id"), lead_uuid, tenant_id])
    row = await conn.fetchrow(
        f"""
        UPDATE leads
        SET {', '.join(set_clauses)},
            updated_at = ${len(params)-3},
            updated_by = ${len(params)-2}
        WHERE id = ${len(params)-1} AND tenant_id = ${len(params)}
        RETURNING *
        """,
        *params,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_status = str(existing_data.get("lead_status") or "").lower()
    new_status = str(update_data.get("lead_status") or existing_data.get("lead_status") or "").lower()
    if new_status and new_status != old_status:
        await _record_lifecycle_event(
            conn,
            tenant_id=tenant_id,
            lead_id=lead_uuid,
            event_type="status_changed",
            created_by=str(current_user.get("id") or ""),
            payload={"from": old_status, "to": new_status},
        )
        background_tasks.add_task(
            track_lead_activity,
            lead_id,
            f"Status changed from {old_status} to {new_status}",
            str(current_user.get("id") or ""),
            tenant_id,
        )

    return _serialize_lead(row)


@router.post("/{lead_id}/convert", response_model=Dict[str, Any])
async def convert_lead_to_customer(
    lead_id: str,
    conversion: LeadConversion,
    background_tasks: BackgroundTasks,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")
    customer_uuid = parse_uuid(conversion.customer_id, field_name="customer_id")

    lead = await conn.fetchrow(
        "SELECT * FROM leads WHERE id = $1 AND tenant_id = $2",
        lead_uuid,
        tenant_id,
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.get("converted_to_customer"):
        raise HTTPException(status_code=400, detail="Lead already converted")

    row = await conn.fetchrow(
        """
        UPDATE leads
        SET converted_to_customer = TRUE,
            converted_customer_id = $1,
            converted_at = $2,
            converted_by = $3,
            lead_status = 'converted',
            updated_at = $2,
            updated_by = $3
        WHERE id = $4 AND tenant_id = $5
        RETURNING *
        """,
        customer_uuid,
        datetime.utcnow(),
        current_user.get("id"),
        lead_uuid,
        tenant_id,
    )

    await _record_lifecycle_event(
        conn,
        tenant_id=tenant_id,
        lead_id=lead_uuid,
        event_type="converted",
        created_by=str(current_user.get("id") or ""),
        payload={"customer_id": str(customer_uuid)},
    )

    background_tasks.add_task(
        track_lead_activity,
        lead_id,
        f"Lead converted to customer {conversion.customer_id}",
        str(current_user.get("id") or ""),
        tenant_id,
    )

    return {
        "message": "Lead successfully converted",
        "lead_id": str(row["id"]),
        "customer_id": conversion.customer_id,
        "converted_at": row["converted_at"].isoformat() if row["converted_at"] else None,
    }


@router.post("/{lead_id}/activities", response_model=LeadActivityResponse)
async def create_lead_activity(
    lead_id: str,
    activity: LeadActivity,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")

    lead_exists = await conn.fetchval(
        "SELECT EXISTS(SELECT 1 FROM leads WHERE id = $1 AND tenant_id = $2)",
        lead_uuid,
        tenant_id,
    )
    if not lead_exists:
        raise HTTPException(status_code=404, detail="Lead not found")

    row = await conn.fetchrow(
        """
        INSERT INTO lead_activities (
            lead_id, activity_type, subject, description, outcome,
            scheduled_at, duration_minutes, assigned_to, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """,
        lead_uuid,
        activity.activity_type.value,
        sanitize_text(activity.subject, max_length=500),
        sanitize_text(activity.description, max_length=5000),
        sanitize_text(activity.outcome, max_length=5000),
        activity.scheduled_at,
        activity.duration_minutes,
        sanitize_text(activity.assigned_to, max_length=255),
        current_user.get("id"),
    )

    if activity.activity_type in {ActivityType.CALL, ActivityType.EMAIL, ActivityType.MEETING}:
        await conn.execute(
            "UPDATE leads SET last_contacted_at = $1 WHERE id = $2 AND tenant_id = $3",
            datetime.utcnow(),
            lead_uuid,
            tenant_id,
        )

    await _record_lifecycle_event(
        conn,
        tenant_id=tenant_id,
        lead_id=lead_uuid,
        event_type="activity_logged",
        created_by=str(current_user.get("id") or ""),
        payload={"activity_type": activity.activity_type.value},
    )

    return {
        **dict(row),
        "id": str(row["id"]),
        "lead_id": str(row["lead_id"]),
    }


@router.get("/{lead_id}/activities", response_model=List[LeadActivityResponse])
async def get_lead_activities(
    lead_id: str,
    request: Request,
    activity_type: Optional[ActivityType] = None,
    limit: int = Query(50, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")

    lead_exists = await conn.fetchval(
        "SELECT EXISTS(SELECT 1 FROM leads WHERE id = $1 AND tenant_id = $2)",
        lead_uuid,
        tenant_id,
    )
    if not lead_exists:
        raise HTTPException(status_code=404, detail="Lead not found")

    params: List[Any] = [lead_uuid]
    where = ["lead_id = $1"]
    if activity_type:
        params.append(activity_type.value)
        where.append(f"activity_type = ${len(params)}")

    params.append(limit)

    rows = await conn.fetch(
        f"""
        SELECT *
        FROM lead_activities
        WHERE {' AND '.join(where)}
        ORDER BY created_at DESC
        LIMIT ${len(params)}
        """,
        *params,
    )

    return [
        {
            **dict(row),
            "id": str(row["id"]),
            "lead_id": str(row["lead_id"]),
        }
        for row in rows
    ]


@router.post("/{lead_id}/qualify", response_model=LeadResponse)
async def qualify_lead(
    lead_id: str,
    qualification: LeadQualification,
    background_tasks: BackgroundTasks,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")

    lead = await conn.fetchrow(
        "SELECT * FROM leads WHERE id = $1 AND tenant_id = $2",
        lead_uuid,
        tenant_id,
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    current_score = int(lead.get("lead_score") or 0)
    score_adjustment = 0

    if qualification.budget and qualification.budget >= 10000:
        score_adjustment += 15
    if qualification.authority:
        score_adjustment += 10
    if qualification.need:
        score_adjustment += 10
    if qualification.timeline:
        timeline = qualification.timeline.lower()
        if "immediate" in timeline:
            score_adjustment += 15
        elif "quarter" in timeline:
            score_adjustment += 10

    if qualification.score_adjustment:
        score_adjustment += qualification.score_adjustment

    new_score = max(0, min(current_score + score_adjustment, 100))

    raw_metadata = lead.get("metadata") if isinstance(lead.get("metadata"), dict) else {}
    if isinstance(lead.get("metadata"), str):
        try:
            raw_metadata = json.loads(lead.get("metadata") or "{}")
        except Exception:
            raw_metadata = {}

    raw_metadata["qualification"] = {
        "budget": qualification.budget,
        "authority": qualification.authority,
        "need": sanitize_text(qualification.need, max_length=1000),
        "timeline": sanitize_text(qualification.timeline, max_length=1000),
        "qualified_at": datetime.utcnow().isoformat(),
    }

    row = await conn.fetchrow(
        """
        UPDATE leads
        SET lead_status = 'qualified',
            lead_score = $1,
            metadata = $2,
            updated_at = $3,
            updated_by = $4
        WHERE id = $5 AND tenant_id = $6
        RETURNING *
        """,
        new_score,
        json.dumps(raw_metadata),
        datetime.utcnow(),
        current_user.get("id"),
        lead_uuid,
        tenant_id,
    )

    await _record_lifecycle_event(
        conn,
        tenant_id=tenant_id,
        lead_id=lead_uuid,
        event_type="qualified",
        created_by=str(current_user.get("id") or ""),
        payload={"score": new_score},
    )

    background_tasks.add_task(
        track_lead_activity,
        lead_id,
        f"Lead qualified with score {new_score}",
        str(current_user.get("id") or ""),
        tenant_id,
    )

    return _serialize_lead(row)


@router.get("/stats/summary")
async def get_lead_stats(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    assigned_to: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    try:
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenant_id]

        if date_from:
            params.append(date_from)
            conditions.append(f"created_at >= ${len(params)}")

        if date_to:
            params.append(date_to + timedelta(days=1))
            conditions.append(f"created_at < ${len(params)}")

        if assigned_to:
            params.append(sanitize_text(assigned_to, max_length=255))
            conditions.append(f"assigned_to = ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}"

        result = await conn.fetchrow(
            f"""
            SELECT
                COUNT(*) as total_leads,
                COUNT(CASE WHEN lead_status = 'new' THEN 1 END) as new_leads,
                COUNT(CASE WHEN lead_status = 'qualified' THEN 1 END) as qualified_leads,
                COUNT(CASE WHEN converted_to_customer THEN 1 END) as converted_leads,
                COUNT(CASE WHEN lead_status = 'lost' THEN 1 END) as lost_leads,
                AVG(lead_score) as avg_lead_score,
                COUNT(CASE WHEN rating = 'hot' THEN 1 END) as hot_leads,
                COUNT(CASE WHEN rating = 'warm' THEN 1 END) as warm_leads,
                COUNT(CASE WHEN rating = 'cold' THEN 1 END) as cold_leads
            FROM leads
            {where_clause}
            """,
            *params,
        )

        source_rows = await conn.fetch(
            f"""
            SELECT lead_source, COUNT(*) as count
            FROM leads
            {where_clause}
            GROUP BY lead_source
            """,
            *params,
        )

        total = int(result["total_leads"] or 0)
        converted_count = int(result["converted_leads"] or 0)

        return {
            **dict(result),
            "conversion_rate": (converted_count / total * 100) if total else 0,
            "source_distribution": {row["lead_source"]: row["count"] for row in source_rows},
        }
    except Exception as exc:
        logger.exception("get_lead_stats failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


async def track_lead_activity(
    lead_id: str,
    activity: str,
    user: str,
    tenant_id: Optional[str] = None,
):
    """Background task for lightweight activity timeline insertion."""
    try:
        lead_uuid = parse_uuid(lead_id, field_name="lead_id")
        from database import get_db_connection

        pool = await get_db_connection()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO lead_activities (
                    lead_id, activity_type, subject, created_by
                ) VALUES ($1, $2, $3, $4)
                """,
                lead_uuid,
                "note",
                sanitize_text(activity, max_length=500),
                sanitize_text(user, max_length=255),
            )

            if tenant_id:
                await _record_lifecycle_event(
                    conn,
                    tenant_id=tenant_id,
                    lead_id=lead_uuid,
                    event_type="activity_note",
                    created_by=user,
                    payload={"activity": activity},
                )
    except Exception as exc:
        logger.error("track_lead_activity failed: %s", exc)
