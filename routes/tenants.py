"""
Tenants/Multi-tenant API Routes - v163.0.26
Fixed to use asyncpg for proper async database operations
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import asyncpg
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tenants"])

# Database pool dependency - uses app state
async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state"""
    pool = getattr(request.app.state, 'db_pool', None)
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    return pool

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
        return "default"
    return x_tenant_id

@router.get("/stats/summary")
async def get_tenants_stats_summary(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get tenants statistics summary - optimized for performance"""
    try:
        async with pool.acquire() as conn:
            # Get tenant counts (fast query)
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_tenants,
                    COUNT(*) FILTER (WHERE status = 'active') as active_tenants,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive_tenants,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '30 days') as new_this_month,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as new_this_week
                FROM tenants
            """)

            # Get plan breakdown (subscription_tier in schema)
            plans = await conn.fetch("""
                SELECT COALESCE(subscription_tier, 'unknown') as plan, COUNT(*) as count
                FROM tenants
                WHERE status = 'active'
                GROUP BY subscription_tier
            """)

            # Get top tenants - simplified query without expensive JOINs
            top_tenants = await conn.fetch("""
                SELECT
                    id,
                    name,
                    company_name,
                    COALESCE(subscription_tier, 'starter') as plan
                FROM tenants
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT 5
            """)

        return {
            "success": True,
            "data": {
                "total_tenants": stats['total_tenants'] or 0,
                "by_status": {
                    "active": stats['active_tenants'] or 0,
                    "inactive": stats['inactive_tenants'] or 0
                },
                "growth": {
                    "new_this_month": stats['new_this_month'] or 0,
                    "new_this_week": stats['new_this_week'] or 0
                },
                "by_plan": {
                    (row['plan'] or 'unknown'): row['count'] for row in plans
                },
                "top_tenants": [
                    {
                        "id": str(t['id']),
                        "name": t['name'],
                        "company_name": t['company_name'],
                        "plan": t['plan']
                    }
                    for t in top_tenants
                ]
            }
        }
    except asyncpg.exceptions.QueryCanceledError as e:
        logger.error(f"Query timeout in tenant stats: {e}")
        raise HTTPException(status_code=504, detail="Query timeout - please try again")
    except Exception as e:
        logger.error(f"Error getting tenant stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tenant statistics: {str(e)}")

@router.get("")
@router.get("/")
async def get_all_tenants(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get all tenants (admin only)"""
    try:
        async with pool.acquire() as conn:
            result = await conn.fetch("""
                SELECT id, name, owner_email, company_name, subscription_tier, status, created_at
                FROM tenants
                ORDER BY created_at DESC
            """)

        tenants = [
            {
                "id": str(row['id']),
                "name": row['name'],
                "email": row['owner_email'],
                "company_name": row['company_name'],
                "plan": row['subscription_tier'],
                "status": row['status'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            }
            for row in result
        ]

        return {
            "tenants": tenants,
            "total": len(tenants)
        }
    except Exception as e:
        logger.error(f"Error getting tenants: {e}")
        return {
            "tenants": [],
            "total": 0,
            "error": str(e)
        }

@router.post("")
@router.post("/")
async def create_tenant(
    request: Request,
    tenant: TenantCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new tenant"""
    try:
        tenant_id = str(uuid.uuid4())

        async with pool.acquire() as conn:
            # Create tenant record (using actual schema columns)
            # Required: subdomain, schema_name, owner_email, company_name
            subdomain = tenant.email.split('@')[0].lower().replace('.', '-')[:50]
            schema_name = f"tenant_{subdomain}"
            await conn.execute("""
                INSERT INTO tenants (id, name, owner_email, company_name, subscription_tier, subdomain, schema_name, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', NOW())
            """, uuid.UUID(tenant_id), tenant.name, tenant.email, tenant.company_name,
                tenant.plan or 'professional', subdomain, schema_name)

            # Also create a customer record for this tenant
            customer_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO customers (id, name, email, phone, company, tenant_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT DO NOTHING
            """, uuid.UUID(customer_id), tenant.name, tenant.email, tenant.phone,
                tenant.company_name, uuid.UUID(tenant_id))

        return {
            "id": tenant_id,
            "message": "Tenant created successfully",
            "tenant": tenant.dict()
        }
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get a specific tenant"""
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT * FROM tenants WHERE id = $1
            """, uuid.UUID(tenant_id))

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {
            "id": str(result['id']),
            "name": result['name'],
            "email": result.get('owner_email'),
            "company_name": result['company_name'],
            "plan": result.get('subscription_tier'),
            "subdomain": result.get('subdomain'),
            "status": result.get('status'),
            "stripe_customer_id": result.get('stripe_customer_id'),
            "stripe_subscription_id": result.get('stripe_subscription_id'),
            "created_at": result['created_at'].isoformat() if result['created_at'] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    tenant: TenantUpdate,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update a tenant"""
    try:
        # Build update query dynamically
        update_fields = []
        params = []
        param_count = 0

        if tenant.name is not None:
            param_count += 1
            update_fields.append(f"name = ${param_count}")
            params.append(tenant.name)

        if tenant.company_name is not None:
            param_count += 1
            update_fields.append(f"company_name = ${param_count}")
            params.append(tenant.company_name)

        if tenant.plan is not None:
            param_count += 1
            update_fields.append(f"subscription_tier = ${param_count}")
            params.append(tenant.plan)

        if tenant.status is not None:
            param_count += 1
            update_fields.append(f"status = ${param_count}")
            params.append(tenant.status)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append("updated_at = NOW()")
        params.append(uuid.UUID(tenant_id))

        query = f"""
            UPDATE tenants
            SET {', '.join(update_fields)}
            WHERE id = ${len(params)}
            RETURNING id
        """

        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {
            "id": tenant_id,
            "message": "Tenant updated successfully",
            "tenant": tenant.dict(exclude_unset=True)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Delete a tenant (soft delete by setting status to inactive)"""
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                UPDATE tenants
                SET status = 'inactive', updated_at = NOW()
                WHERE id = $1
                RETURNING id
            """, uuid.UUID(tenant_id))

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {
            "id": tenant_id,
            "message": "Tenant deactivated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get statistics for a specific tenant"""
    try:
        async with pool.acquire() as conn:
            # Get customer count
            customers = await conn.fetchval("""
                SELECT COUNT(*) FROM customers WHERE tenant_id = $1
            """, uuid.UUID(tenant_id))

            # Get job count
            jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs WHERE tenant_id = $1
            """, uuid.UUID(tenant_id))

            # Get invoice stats
            invoice_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COUNT(*) FILTER (WHERE status = 'paid' OR payment_status = 'paid') as paid_invoices
                FROM invoices
                WHERE tenant_id = $1
            """, uuid.UUID(tenant_id))

        return {
            "tenant_id": tenant_id,
            "customers": customers or 0,
            "jobs": jobs or 0,
            "invoices": {
                "total": invoice_stats['total_invoices'] or 0,
                "paid": invoice_stats['paid_invoices'] or 0,
                "revenue": float(invoice_stats['total_revenue'] or 0)
            },
            "usage": {
                "api_calls": 0,
                "storage_mb": 0,
                "users": 1
            }
        }
    except Exception as e:
        logger.error(f"Error getting tenant stats: {e}")
        return {
            "tenant_id": tenant_id,
            "customers": 0,
            "jobs": 0,
            "invoices": {"total": 0, "paid": 0, "revenue": 0},
            "usage": {"api_calls": 0, "storage_mb": 0, "users": 0},
            "error": str(e)
        }
