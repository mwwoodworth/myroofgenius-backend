"""
Password Policies Module
Managed password security rules and compliance using SQLAlchemy models.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

from database import get_db, engine
from core.supabase_auth import get_current_user

router = APIRouter()

# Local Base for internal models
Base = declarative_base()

# ============================================================================
# MODELS
# ============================================================================

class PasswordPolicy(Base):
    __tablename__ = "password_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="active")
    data = Column(JSON, default={})
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Ensure tables exist
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

# ============================================================================
# SCHEMAS
# ============================================================================

class PasswordPolicyBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class PasswordPolicyCreate(PasswordPolicyBase):
    pass

class PasswordPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PasswordPolicyResponse(PasswordPolicyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total: int
    active: int
    recent: int

# ============================================================================
# ROUTES
# ============================================================================

@router.post("/", response_model=PasswordPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_password_policy(
    policy: PasswordPolicyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new password policy"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_policy = PasswordPolicy(**policy.dict(), tenant_id=tenant_id)
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PasswordPolicyResponse])
async def list_password_policies(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List password policies"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        query = db.query(PasswordPolicy).filter(PasswordPolicy.tenant_id == tenant_id)
        if status:
            query = query.filter(PasswordPolicy.status == status)
        
        return query.order_by(PasswordPolicy.created_at.desc()).offset(skip).limit(limit).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{policy_id}", response_model=PasswordPolicyResponse)
async def get_password_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific password policy"""
    tenant_id = current_user.get("tenant_id")
    policy = db.query(PasswordPolicy).filter(PasswordPolicy.id == policy_id, PasswordPolicy.tenant_id == tenant_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Password policy not found")
    return policy

@router.put("/{policy_id}", response_model=PasswordPolicyResponse)
async def update_password_policy(
    policy_id: uuid.UUID,
    policy_update: PasswordPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update password policy"""
    tenant_id = current_user.get("tenant_id")
    policy = db.query(PasswordPolicy).filter(PasswordPolicy.id == policy_id, PasswordPolicy.tenant_id == tenant_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Password policy not found")
    
    for key, value in policy_update.dict(exclude_unset=True).items():
        setattr(policy, key, value)
    
    try:
        db.commit()
        db.refresh(policy)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return policy

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_password_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete password policy"""
    tenant_id = current_user.get("tenant_id")
    policy = db.query(PasswordPolicy).filter(PasswordPolicy.id == policy_id, PasswordPolicy.tenant_id == tenant_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Password policy not found")
    
    db.delete(policy)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary", response_model=StatsResponse)
async def get_password_policies_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get password policies statistics"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Tenant assignment required")
             
        total = db.query(PasswordPolicy).filter(PasswordPolicy.tenant_id == tenant_id).count()
        active = db.query(PasswordPolicy).filter(PasswordPolicy.tenant_id == tenant_id, PasswordPolicy.status == 'active').count()
        
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent = db.query(PasswordPolicy).filter(
            PasswordPolicy.tenant_id == tenant_id,
            PasswordPolicy.created_at > cutoff
        ).count()
        
        return {
            "total": total,
            "active": active,
            "recent": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
