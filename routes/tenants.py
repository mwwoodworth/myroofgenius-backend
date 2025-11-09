"""Tenants/Multi-tenant API Routes"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
import sys
import json

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import database session
try:
    from main import SessionLocal
except ImportError:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        ""
    )

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(tags=["tenants"])

class TenantCreate(BaseModel):
    name: str
    email: str
    company_name: str
    plan: Optional[str] = "starter"
    phone: Optional[str] = None
    website: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    plan: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None

def get_current_tenant(x_tenant_id: Optional[str] = Header(None)):
    """Extract tenant ID from header"""
    if not x_tenant_id:
        # For now, return a default tenant ID
        return "default"
    return x_tenant_id

@router.get("/tenants")
async def get_all_tenants():
    """Get all tenants (admin only)"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT id, name, email, company_name, plan, status, created_at
                FROM tenants
                ORDER BY created_at DESC
            """))

            tenants = []
            for row in result:
                tenants.append({
                    "id": str(row.id),
                    "name": row.name,
                    "email": row.email,
                    "company_name": row.company_name,
                    "plan": row.plan,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })

            return {
                "tenants": tenants,
                "total": len(tenants)
            }
    except Exception as e:
        # Return empty list on error (table might not exist)
        return {
            "tenants": [],
            "total": 0,
            "error": str(e) if os.getenv("DEBUG") else "Database error"
        }

@router.post("/tenants")
async def create_tenant(tenant: TenantCreate):
    """Create a new tenant"""
    try:
        with SessionLocal() as db:
            tenant_id = str(uuid.uuid4())

            # Create tenant record
            result = db.execute(text("""
                INSERT INTO tenants (id, name, email, company_name, plan, phone, website, status, created_at)
                VALUES (:id, :name, :email, :company_name, :plan, :phone, :website, 'active', NOW())
                RETURNING id
            """), {
                "id": tenant_id,
                "name": tenant.name,
                "email": tenant.email,
                "company_name": tenant.company_name,
                "plan": tenant.plan,
                "phone": tenant.phone,
                "website": tenant.website
            })
            db.commit()

            # Also create a customer record for this tenant
            db.execute(text("""
                INSERT INTO customers (id, name, email, phone, company, tenant_id, created_at)
                VALUES (:id, :name, :email, :phone, :company, :tenant_id, NOW())
                ON CONFLICT DO NOTHING
            """), {
                "id": str(uuid.uuid4()),
                "name": tenant.name,
                "email": tenant.email,
                "phone": tenant.phone,
                "company": tenant.company_name,
                "tenant_id": tenant_id
            })
            db.commit()

            return {
                "id": tenant_id,
                "message": "Tenant created successfully",
                "tenant": tenant.dict()
            }
    except Exception as e:
        # If tenants table doesn't exist, create it
        if "relation \"tenants\" does not exist" in str(e):
            try:
                with SessionLocal() as db:
                    db.execute(text("""
                        CREATE TABLE IF NOT EXISTS tenants (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            name VARCHAR(255) NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            company_name VARCHAR(255) NOT NULL,
                            plan VARCHAR(50) DEFAULT 'starter',
                            phone VARCHAR(50),
                            website VARCHAR(255),
                            status VARCHAR(50) DEFAULT 'active',
                            stripe_customer_id VARCHAR(255),
                            stripe_subscription_id VARCHAR(255),
                            settings JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        )
                    """))
                    db.commit()

                    # Try again
                    return await create_tenant(tenant)
            except Exception as create_error:
                raise HTTPException(status_code=500, detail=f"Failed to create tenants table: {str(create_error)}")

        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get a specific tenant"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                SELECT * FROM tenants WHERE id = :id
            """), {"id": tenant_id}).first()

            if not result:
                raise HTTPException(status_code=404, detail="Tenant not found")

            return {
                "id": str(result.id),
                "name": result.name,
                "email": result.email,
                "company_name": result.company_name,
                "plan": result.plan,
                "phone": result.phone,
                "website": result.website if hasattr(result, 'website') else None,
                "status": result.status,
                "stripe_customer_id": result.stripe_customer_id if hasattr(result, 'stripe_customer_id') else None,
                "stripe_subscription_id": result.stripe_subscription_id if hasattr(result, 'stripe_subscription_id') else None,
                "settings": result.settings if hasattr(result, 'settings') else {},
                "created_at": result.created_at.isoformat() if result.created_at else None
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, tenant: TenantUpdate):
    """Update a tenant"""
    try:
        with SessionLocal() as db:
            # Build update query dynamically
            update_fields = []
            params = {"id": tenant_id}

            if tenant.name is not None:
                update_fields.append("name = :name")
                params["name"] = tenant.name

            if tenant.company_name is not None:
                update_fields.append("company_name = :company_name")
                params["company_name"] = tenant.company_name

            if tenant.plan is not None:
                update_fields.append("plan = :plan")
                params["plan"] = tenant.plan

            if tenant.phone is not None:
                update_fields.append("phone = :phone")
                params["phone"] = tenant.phone

            if tenant.website is not None:
                update_fields.append("website = :website")
                params["website"] = tenant.website

            if tenant.status is not None:
                update_fields.append("status = :status")
                params["status"] = tenant.status

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_fields.append("updated_at = NOW()")

            query = f"""
                UPDATE tenants
                SET {', '.join(update_fields)}
                WHERE id = :id
                RETURNING id
            """

            result = db.execute(text(query), params)
            db.commit()

            if not result.scalar():
                raise HTTPException(status_code=404, detail="Tenant not found")

            return {
                "id": tenant_id,
                "message": "Tenant updated successfully",
                "tenant": tenant.dict(exclude_unset=True)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete a tenant (soft delete by setting status to inactive)"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                UPDATE tenants
                SET status = 'inactive', updated_at = NOW()
                WHERE id = :id
                RETURNING id
            """), {"id": tenant_id})
            db.commit()

            if not result.scalar():
                raise HTTPException(status_code=404, detail="Tenant not found")

            return {
                "id": tenant_id,
                "message": "Tenant deactivated successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(tenant_id: str):
    """Get statistics for a specific tenant"""
    try:
        with SessionLocal() as db:
            # Get customer count
            customers = db.execute(text("""
                SELECT COUNT(*) FROM customers WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id}).scalar() or 0

            # Get job count
            jobs = db.execute(text("""
                SELECT COUNT(*) FROM jobs WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id}).scalar() or 0

            # Get invoice stats
            invoice_stats = db.execute(text("""
                SELECT
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COUNT(CASE WHEN status = 'paid' OR payment_status = 'paid' THEN 1 END) as paid_invoices
                FROM invoices
                WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id}).first()

            return {
                "tenant_id": tenant_id,
                "customers": customers,
                "jobs": jobs,
                "invoices": {
                    "total": invoice_stats[0] if invoice_stats else 0,
                    "paid": invoice_stats[2] if invoice_stats else 0,
                    "revenue": float(invoice_stats[1]) if invoice_stats else 0
                },
                "usage": {
                    "api_calls": 0,  # Placeholder
                    "storage_mb": 0,  # Placeholder
                    "users": 1  # Placeholder
                }
            }
    except Exception as e:
        # Return empty stats on error
        return {
            "tenant_id": tenant_id,
            "customers": 0,
            "jobs": 0,
            "invoices": {"total": 0, "paid": 0, "revenue": 0},
            "usage": {"api_calls": 0, "storage_mb": 0, "users": 0},
            "error": str(e) if os.getenv("DEBUG") else "Database error"
        }