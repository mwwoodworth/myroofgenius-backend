"""
Asset Registry Module
Handles CRUD operations for assets.
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
    db: Session = Depends(get_db)
):
    """List all assets"""
    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM asset_registry
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip}).fetchall()

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AssetResponse)
def create_asset(
    item: AssetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset"""
    try:
        new_id = uuid.uuid4()
        timestamp = datetime.now()
        
        db.execute(text("""
            INSERT INTO asset_registry (id, name, description, status, data, created_at, updated_at)
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

@router.get("/{id}", response_model=AssetResponse)
def get_asset(
    id: str,
    db: Session = Depends(get_db)
):
    """Get a single asset by ID"""
    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM asset_registry
            WHERE id = :id
        """), {"id": id}).fetchone()

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
    db: Session = Depends(get_db)
):
    """Update an asset"""
    try:
        # Check if exists
        exists = db.execute(text("SELECT id FROM asset_registry WHERE id = :id"), {"id": id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Asset not found")

        updates = []
        params = {"id": id, "updated_at": datetime.now()}

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
        
        query = f"UPDATE asset_registry SET {', '.join(updates)} WHERE id = :id"
        db.execute(text(query), params)
        db.commit()

        # Fetch updated
        return get_asset(id, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
def delete_asset(
    id: str,
    db: Session = Depends(get_db)
):
    """Delete an asset"""
    try:
        result = db.execute(text("DELETE FROM asset_registry WHERE id = :id RETURNING id"), {"id": id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Asset not found")
        db.commit()
        return {"message": "Asset deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
