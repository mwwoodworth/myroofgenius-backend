"""Webhook management routes with tenant-safe CRUD and validation."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.request_safety import parse_uuid, require_tenant_id, sanitize_payload, sanitize_text
from core.supabase_auth import get_authenticated_user
from database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class WebhookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active", min_length=2, max_length=40)
    endpoint_url: Optional[AnyHttpUrl] = None
    events: List[str] = Field(default_factory=list)
    secret: Optional[str] = Field(default=None, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookCreate(WebhookBase):
    pass


class WebhookResponse(WebhookBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


def _to_data_payload(item: WebhookBase) -> Dict[str, Any]:
    return sanitize_payload(
        {
            "endpoint_url": str(item.endpoint_url) if item.endpoint_url else None,
            "events": item.events,
            "secret": sanitize_text(item.secret, max_length=255),
            "metadata": item.metadata,
        }
    )


@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    try:
        rows = db.execute(
            text(
                """
                SELECT id, name, description, status, data, created_at, updated_at
                FROM webhook_management
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """
            ),
            {"tenant_id": tenant_id, "limit": limit, "skip": skip},
        ).fetchall()

        result: List[Dict[str, Any]] = []
        for row in rows:
            data = row[4] if row[4] else {}
            if isinstance(data, str):
                data = json.loads(data)
            result.append(
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "status": row[3],
                    "endpoint_url": data.get("endpoint_url"),
                    "events": data.get("events", []),
                    "secret": data.get("secret"),
                    "metadata": data.get("metadata", {}),
                    "created_at": row[5],
                    "updated_at": row[6],
                }
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("list_webhooks failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=WebhookResponse)
def create_webhook(
    item: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    try:
        new_id = uuid.uuid4()
        timestamp = datetime.utcnow()

        db.execute(
            text(
                """
                INSERT INTO webhook_management (
                    id, tenant_id, name, description, status, data, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :name, :description, :status, :data, :created_at, :updated_at
                )
                """
            ),
            {
                "id": new_id,
                "tenant_id": tenant_id,
                "name": sanitize_text(item.name, max_length=200),
                "description": sanitize_text(item.description, max_length=1000),
                "status": sanitize_text(item.status, max_length=40),
                "data": json.dumps(_to_data_payload(item)),
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )
        db.commit()

        return {
            "id": str(new_id),
            "name": item.name,
            "description": item.description,
            "status": item.status,
            "endpoint_url": str(item.endpoint_url) if item.endpoint_url else None,
            "events": item.events,
            "secret": item.secret,
            "metadata": item.metadata,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("create_webhook failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{id}")
def delete_webhook(
    id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    webhook_id = parse_uuid(id, field_name="webhook_id")

    try:
        row = db.execute(
            text(
                """
                DELETE FROM webhook_management
                WHERE id = :id AND tenant_id = :tenant_id
                RETURNING id
                """
            ),
            {"id": webhook_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Webhook not found")

        db.commit()
        return {"message": "Webhook deleted successfully", "id": id}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("delete_webhook failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")
