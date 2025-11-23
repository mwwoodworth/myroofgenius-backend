"""
Customers API Routes
Manages customer records and operations
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

class Customer(BaseModel):
    """Customer model"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None

@router.get("")
@router.get("/")
async def list_customers(
    request: Request,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all customers for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT id, name, email, phone, company, address, city, state,
                   zip_code, status, created_at
            FROM customers
            WHERE tenant_id = $1
        """

        params = [tenant_id]
        param_count = 0

        if status:
            param_count += 1
            query += f" AND status = ${param_count + 1}"
            params.append(status)

        if search:
            param_count += 1
            placeholder = param_count + 1
            query += (
                f" AND (name ILIKE ${placeholder} OR email ILIKE ${placeholder} OR company ILIKE ${placeholder})"
            )
            params.append(f"%{search}%")

        query += " ORDER BY created_at DESC LIMIT ${} OFFSET ${}".format(param_count + 2, param_count + 3)
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            customers = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM customers WHERE tenant_id = $1"
            count_params = [tenant_id]
            cp = 1

            if status:
                cp += 1
                count_query += f" AND status = ${cp}"
                count_params.append(status)

            if search:
                cp += 1
                count_query += f" AND (name ILIKE ${cp} OR email ILIKE ${cp} OR company ILIKE ${cp})"
                count_params.append(f"%{search}%")

            total = await conn.fetchval(count_query, *count_params) if count_params else await conn.fetchval(count_query)

        # Convert to list of dicts
        result = [dict(customer) for customer in customers]

        return {
            "success": True,
            "data": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list customers")

@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get customer details for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            customer = await conn.fetchrow("""
                SELECT id, name, email, phone,
                       address, city, state, tenant_id,
                       status, created_at
                FROM customers
                WHERE id = $1 AND tenant_id = $2
            """, customer_id, tenant_id)

            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Get related counts
            job_count = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs WHERE customer_id = $1 AND tenant_id = $2
            """, customer_id, tenant_id)

            invoice_count = await conn.fetchval("""
                SELECT COUNT(*) FROM invoices WHERE customer_id = $1 AND tenant_id = $2
            """, customer_id, tenant_id)

            total_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(total_amount), 0) FROM invoices
                WHERE customer_id = $1 AND tenant_id = $2 AND status = 'paid'
            """, customer_id, tenant_id)

        customer_dict = dict(customer)
        customer_dict['job_count'] = job_count
        customer_dict['invoice_count'] = invoice_count
        customer_dict['total_revenue'] = float(total_revenue)

        return {
            "success": True,
            "data": customer_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to get customer")

@router.get("/stats/summary")
async def get_customer_stats(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get customer statistics"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '30 days') as new_this_month,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as new_this_week
                FROM customers
                WHERE tenant_id = $1
            """, tenant_id)

            # Get top customers by revenue
            top_customers = await conn.fetch("""
                SELECT c.id, c.name, COALESCE(SUM(i.total_amount), 0) as total_revenue
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id AND i.status = 'paid' AND i.tenant_id = $1
                WHERE c.tenant_id = $1
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
                LIMIT 5
            """, tenant_id)

        return {
            "success": True,
            "data": {
                "total_customers": stats['total_customers'],
                "by_status": {
                    "active": stats['active'],
                    "inactive": stats['inactive']
                },
                "growth": {
                    "new_this_month": stats['new_this_month'],
                    "new_this_week": stats['new_this_week']
                },
                "top_customers": [
                    {
                        "id": str(c['id']),
                        "name": c['name'],
                        "total_revenue": float(c['total_revenue'])
                    }
                    for c in top_customers
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error getting customer stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get customer statistics")
