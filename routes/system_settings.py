"""
System Settings Module
Handles system-wide settings management.
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
class SettingBase(BaseModel):
    name: str = Field(..., description="Key/Name of the setting")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class SettingUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class SettingResponse(SettingBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Endpoints

@router.get("/", response_model=List[SettingResponse])
def list_settings(
    db: Session = Depends(get_db)
):
    """Get all settings"""
    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM system_settings
            ORDER BY name ASC
        """)).fetchall()

        settings = []
        for row in result:
            settings.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "data": json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6]
            })
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    item: SettingUpdate,
    db: Session = Depends(get_db)
):
    """Update setting by key (name)"""
    try:
        # Check if exists by name (key)
        existing = db.execute(text("SELECT id FROM system_settings WHERE name = :name"), {"name": key}).fetchone()
        
        # If not found, maybe create it? Or 404? 
        # Usually settings are pre-defined, but let's allow creation if it doesn't exist?
        # The prompt says 'update setting'. I'll return 404 if not found to be safe, or upsert.
        # Let's do strict update for now as per 'PUT'.
        
        if not existing:
             raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

        id = existing[0]

        updates = []
        params = {"id": id, "updated_at": datetime.now()}

        if item.description is not None:
            updates.append("description = :description")
            params["description"] = item.description
        if item.status is not None:
            updates.append("status = :status")
            params["status"] = item.status
        if item.data is not None:
            updates.append("data = :data")
            params["data"] = json.dumps(item.data)

        if not updates:
             # Just return current state if nothing to update
             pass
        else:
            updates.append("updated_at = :updated_at")
            query = f"UPDATE system_settings SET {', '.join(updates)} WHERE id = :id"
            db.execute(text(query), params)
            db.commit()

        # Fetch updated
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM system_settings
            WHERE id = :id
        """), {"id": id}).fetchone()

        return {
            "id": str(result[0]),
            "name": result[1],
            "description": result[2],
            "status": result[3],
            "data": json.loads(result[4]) if isinstance(result[4], str) else result[4] if result[4] else {},
            "created_at": result[5],
            "updated_at": result[6]
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
