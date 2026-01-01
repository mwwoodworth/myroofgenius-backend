"""
Service Contracts Module
Handles service contract lifecycle.
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

from core.supabase_auth import get_authenticated_user

router = APIRouter()

# Models
class ContractBase(BaseModel):
    name: str = Field(..., description="Contract Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = Field(default={}, description="Contract details (terms, value, etc)")

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ContractResponse(ContractBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Endpoints

@router.get("/", response_model=List[ContractResponse])
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all contracts"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    try:
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM service_contracts
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"tenant_id": tenant_id, "limit": limit, "skip": skip}).fetchall()

        contracts = []
        for row in result:
            contracts.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "data": json.loads(row[4]) if isinstance(row[4], str) else row[4] if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6]
            })
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ContractResponse)
def create_contract(
    item: ContractCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create a new contract"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    try:
        new_id = uuid.uuid4()
        timestamp = datetime.now()

        db.execute(text("""
            INSERT INTO service_contracts (id, tenant_id, name, description, status, data, created_at, updated_at)
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

@router.put("/{id}", response_model=ContractResponse)
def update_contract(
    id: str,
    item: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update a contract"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    try:
        # Check if exists for this tenant
        exists = db.execute(text("SELECT id FROM service_contracts WHERE id = :id AND tenant_id = :tenant_id"), {"id": id, "tenant_id": tenant_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Contract not found")

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

        query = f"UPDATE service_contracts SET {', '.join(updates)} WHERE id = :id AND tenant_id = :tenant_id"
        db.execute(text(query), params)
        db.commit()

        # Fetch updated
        result = db.execute(text("""
            SELECT id, name, description, status, data, created_at, updated_at
            FROM service_contracts
            WHERE id = :id AND tenant_id = :tenant_id
        """), {"id": id, "tenant_id": tenant_id}).fetchone()

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

@router.delete("/{id}")
def delete_contract(
    id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Delete a contract"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID not found in user context")

    try:
        result = db.execute(text("DELETE FROM service_contracts WHERE id = :id AND tenant_id = :tenant_id RETURNING id"), {"id": id, "tenant_id": tenant_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Contract not found")
        db.commit()
        return {"message": "Contract deleted successfully", "id": id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
