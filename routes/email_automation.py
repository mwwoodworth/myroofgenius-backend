"""Email automation routes with template management and bounce handling."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from core.request_safety import parse_uuid, require_tenant_id, sanitize_payload, sanitize_text
from core.supabase_auth import get_authenticated_user
from services.email_engine import email_engine

router = APIRouter()


async def get_db(request: Request):
    """Yield an asyncpg connection from the shared pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class EmailAutomationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active", min_length=2, max_length=40)
    data: Dict[str, Any] = Field(default_factory=dict)


class EmailAutomationCreate(EmailAutomationBase):
    pass


class EmailAutomationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, min_length=2, max_length=40)
    data: Optional[Dict[str, Any]] = None


class EmailAutomationResponse(EmailAutomationBase):
    id: str
    created_at: datetime
    updated_at: datetime


class TemplateUpsertRequest(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=255)
    subject_template: str = Field(..., min_length=1, max_length=500)
    html_template: str = Field(..., min_length=1)
    text_template: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TemplateSendRequest(BaseModel):
    recipient_email: EmailStr
    template_name: str = Field(..., min_length=1, max_length=255)
    context: Optional[Dict[str, Any]] = None


class BounceEventRequest(BaseModel):
    recipient_email: EmailStr
    reason: Optional[str] = Field(default=None, max_length=1000)
    provider_event_id: Optional[str] = Field(default=None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


@router.post("/", response_model=EmailAutomationResponse)
async def create_email_automation(
    item: EmailAutomationCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    row = await conn.fetchrow(
        """
        INSERT INTO email_automation (tenant_id, name, description, status, data)
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


@router.get("/", response_model=List[EmailAutomationResponse])
async def list_email_automation(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    query = "SELECT * FROM email_automation WHERE tenant_id = $1"
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


@router.get("/{item_id}", response_model=EmailAutomationResponse)
async def get_email_automation(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "SELECT * FROM email_automation WHERE id = $1 AND tenant_id = $2",
        item_uuid,
        tenant_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Email automation not found")

    return {
        **dict(row),
        "id": str(row["id"]),
        "data": row["data"] if row["data"] else {},
    }


@router.put("/{item_id}")
async def update_email_automation(
    item_id: str,
    updates: EmailAutomationUpdate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
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

    set_clauses = []
    params: List[Any] = []
    for field, value in update_data.items():
        params.append(value)
        set_clauses.append(f"{field} = ${len(params)}")

    params.extend([item_uuid, tenant_id])
    row = await conn.fetchrow(
        f"""
        UPDATE email_automation
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params)-1} AND tenant_id = ${len(params)}
        RETURNING id
        """,
        *params,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Email automation not found")

    return {"message": "Email automation updated", "id": str(row["id"])}


@router.delete("/{item_id}")
async def delete_email_automation(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "DELETE FROM email_automation WHERE id = $1 AND tenant_id = $2 RETURNING id",
        item_uuid,
        tenant_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Email automation not found")

    return {"message": "Email automation deleted", "id": str(row["id"])}


@router.get("/stats/summary")
async def get_email_automation_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    result = await conn.fetchrow(
        """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM email_automation
        WHERE tenant_id = $1
        """,
        tenant_id,
    )
    return dict(result)


@router.post("/templates/upsert")
async def upsert_template(
    payload: TemplateUpsertRequest,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    result = await email_engine.upsert_template(
        conn,
        tenant_id=tenant_id,
        template_name=payload.template_name,
        subject_template=payload.subject_template,
        html_template=payload.html_template,
        text_template=payload.text_template,
        metadata=payload.metadata,
    )
    return result


@router.post("/send")
async def queue_templated_email(
    payload: TemplateSendRequest,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    return await email_engine.queue_send(
        conn,
        tenant_id=tenant_id,
        recipient_email=str(payload.recipient_email),
        template_name=payload.template_name,
        context=payload.context,
        provider="resend",
    )


@router.post("/events/bounce")
async def record_bounce(
    payload: BounceEventRequest,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    return await email_engine.record_bounce(
        conn,
        tenant_id=tenant_id,
        recipient_email=str(payload.recipient_email),
        reason=payload.reason,
        provider_event_id=payload.provider_event_id,
        metadata=payload.metadata,
    )
