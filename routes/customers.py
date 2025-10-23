"""
Customers API Routes
Manages customer records and operations
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import json

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
    search: Optional[str] = None
):
    """List all customers (no auth required for basic listing)"""
    try:
        db_pool = request.app.state.db_pool

        query = """
            SELECT id, name, email, phone, company, address, city, state,
                   zip_code, status, created_at
            FROM customers
            WHERE 1=1
        """

        params = []
        param_count = 0

        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)

        if search:
            param_count += 1
            query += f" AND (name ILIKE ${param_count} OR email ILIKE ${param_count} OR company ILIKE ${param_count})"
            params.append(f"%{search}%")

        param_count += 1
        query += f" ORDER BY created_at DESC LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        async with db_pool.acquire() as conn:
            customers = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM customers WHERE 1=1"
            count_params = []
            cp = 0

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
    request: Request
):
    """Get customer details (no auth required for basic info)"""
    try:
        db_pool = request.app.state.db_pool

        async with db_pool.acquire() as conn:
            customer = await conn.fetchrow("""
                SELECT id, name, email, phone,
                       address, city, state,
                       status, created_at
                FROM customers
                WHERE id = $1
            """, customer_id)

            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Get related counts
            job_count = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs WHERE customer_id = $1
            """, customer_id)

            invoice_count = await conn.fetchval("""
                SELECT COUNT(*) FROM invoices WHERE customer_id = $1
            """, customer_id)

            total_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(total_amount), 0) FROM invoices
                WHERE customer_id = $1 AND status = 'paid'
            """, customer_id)

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
    request: Request
):
    """Get customer statistics"""
    try:
        db_pool = request.app.state.db_pool

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '30 days') as new_this_month,
                    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as new_this_week
                FROM customers
            """)

            # Get top customers by revenue
            top_customers = await conn.fetch("""
                SELECT c.id, c.name, COALESCE(SUM(i.total_amount), 0) as total_revenue
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id AND i.status = 'paid'
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
                LIMIT 5
            """)

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
