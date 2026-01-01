"""
Calibration Tracking Module
Handles equipment calibration records.
SECURITY FIX: Added tenant isolation to prevent cross-tenant data access
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from core.supabase_auth import get_authenticated_user
import uuid
import json

router = APIRouter()

# Models
class CalibrationBase(BaseModel):
    name: str = Field(..., description="Name of the equipment/calibration")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = Field(default={}, description="Calibration data (dates, results, etc)")

    @validator('data')
    def validate_dates(cls, v):
        # Optional: Validate next_due_date format if present
        return v

class CalibrationCreate(CalibrationBase):
    pass

class CalibrationResponse(CalibrationBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Endpoints

@router.get("/", response_model=List[CalibrationResponse])
def list_calibrations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all calibrations - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM calibration_tracking
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"tenant_id": tenant_id, "limit": limit, "skip": skip}).fetchall()

        items = []
        for row in result:
            items.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "data": json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6]
            })
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CalibrationResponse)
def record_calibration(
    item: CalibrationCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Record a new calibration - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        new_id = uuid.uuid4()
        timestamp = datetime.now()

        db.execute(text("""
            INSERT INTO calibration_tracking (id, name, description, status, data, created_at, updated_at, tenant_id)
            VALUES (:id, :name, :description, :status, :data, :created_at, :updated_at, :tenant_id)
        """), {
            "id": new_id,
            "name": item.name,
            "description": item.description,
            "status": item.status,
            "data": json.dumps(item.data) if item.data else None,
            "created_at": timestamp,
            "updated_at": timestamp,
            "tenant_id": tenant_id
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

@router.get("/due", response_model=List[CalibrationResponse])
def get_due_calibrations(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get due calibrations (next_due_date <= today) - tenant isolated"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        today_str = date.today().isoformat()

        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM calibration_tracking
            WHERE status = 'active' AND tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchall()

        due_items = []
        for row in result:
            data = json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {}
            next_due = data.get('next_due_date')
            if next_due and next_due <= today_str:
                 due_items.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "status": row[3],
                    "data": data,
                    "created_at": row[5],
                    "updated_at": row[6]
                })

        return due_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
