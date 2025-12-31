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
    db: Session = Depends(get_db)
):
    """List all webhooks"""
    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM webhook_management
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip}).fetchall()

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
    db: Session = Depends(get_db)
):
    """Create a new webhook"""
    try:
        new_id = uuid.uuid4()
        timestamp = datetime.now()
        
        db.execute(text("""
            INSERT INTO webhook_management (id, name, description, status, data, created_at, updated_at)
            VALUES (:id, :name, :description, :status, :data, :created_at, :updated_at)
        """), {
            "id": new_id,
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
    db: Session = Depends(get_db)
):
    """Remove a webhook"""
    try:
        result = db.execute(text("DELETE FROM webhook_management WHERE id = :id RETURNING id"), {"id": id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        db.commit()
        return {"message": "Webhook deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
