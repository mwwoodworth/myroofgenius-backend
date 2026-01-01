"""
Asset Registry Module
Handles CRUD operations for assets.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
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
class AssetBase(BaseModel):
    name: str = Field(..., description="Name of the asset")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AssetResponse(AssetBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Endpoints

@router.get("/", response_model=List[AssetResponse])
def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all assets"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM asset_registry
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"tenant_id": tenant_id, "limit": limit, "skip": skip}).fetchall()

        assets = []
        for row in result:
            assets.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "data": json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6]
            })
        return assets
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AssetResponse)
def create_asset(
    item: AssetCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create a new asset"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        new_id = uuid.uuid4()
        timestamp = datetime.now()

        db.execute(text("""
            INSERT INTO asset_registry (id, tenant_id, name, description, status, data, created_at, updated_at)
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
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}", response_model=AssetResponse)
def get_asset(
    id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get a single asset by ID"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM asset_registry
            WHERE id = :id AND tenant_id = :tenant_id
        """), {"id": id, "tenant_id": tenant_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Asset not found")

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
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{id}", response_model=AssetResponse)
def update_asset(
    id: str,
    item: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update an asset"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Check if exists and belongs to tenant
        exists = db.execute(text("SELECT id FROM asset_registry WHERE id = :id AND tenant_id = :tenant_id"), {"id": id, "tenant_id": tenant_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Asset not found")

        updates = []
        params = {"id": id, "tenant_id": tenant_id, "updated_at": datetime.now()}

        if item.name is not None:
            updates.append("name = :name")
            params["name"] = item.name
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
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = :updated_at")

        query = f"UPDATE asset_registry SET {', '.join(updates)} WHERE id = :id AND tenant_id = :tenant_id"
        db.execute(text(query), params)
        db.commit()

        # Fetch updated
        return get_asset(id, db, current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
def delete_asset(
    id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Delete an asset"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = db.execute(text("DELETE FROM asset_registry WHERE id = :id AND tenant_id = :tenant_id RETURNING id"), {"id": id, "tenant_id": tenant_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Asset not found")
        db.commit()
        return {"message": "Asset deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
