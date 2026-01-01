"""
Webhook Management Module
Handles CRUD operations for webhooks.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from core.supabase_auth import get_authenticated_user
import uuid
import json

router = APIRouter()

# Models
class WebhookBase(BaseModel):
    name: str = Field(..., description="Name of the webhook")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = Field(default={}, description="Webhook config (url, events, etc)")

class WebhookCreate(WebhookBase):
    pass

class WebhookResponse(WebhookBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Endpoints

@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all webhooks"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM webhook_management
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"tenant_id": tenant_id, "limit": limit, "skip": skip}).fetchall()

        webhooks = []
        for row in result:
            webhooks.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "data": json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6]
            })
        return webhooks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=WebhookResponse)
def create_webhook(
    item: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create a new webhook"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    try:
        new_id = uuid.uuid4()
        timestamp = datetime.now()

        db.execute(text("""
            INSERT INTO webhook_management (id, tenant_id, name, description, status, data, created_at, updated_at)
            VALUES (:id, :tenant_id, :name, :description, :status, :data, :created_at, :updated_at)
        """), {
            "id": new_id,
            "tenant_id": tenant_id,
            "name": item.name,
            "description": item.description,
            "status": item.status,
            "data": json.dumps(item.data) if item.data else None,
            "created_at": timestamp,
            "updated_at": timestamp
        })
        db.commit()

        return {
            **item.dict(),
            "id": str(new_id),
            "created_at": timestamp,
            "updated_at": timestamp
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
def delete_webhook(
    id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Remove a webhook"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    try:
        result = db.execute(text("DELETE FROM webhook_management WHERE id = :id AND tenant_id = :tenant_id RETURNING id"), {"id": id, "tenant_id": tenant_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        db.commit()
        return {"message": "Webhook deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
