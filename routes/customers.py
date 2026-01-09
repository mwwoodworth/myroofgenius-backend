"""
Customers API Routes
Manages customer records and operations
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from uuid import UUID, uuid4

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

def _parse_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc


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
            SELECT
                id,
                name,
                email,
                phone,
                company_name AS company,
                COALESCE(service_address, billing_address, address_line1, billing_address, service_address) AS address,
                COALESCE(service_city, billing_city, city) AS city,
                COALESCE(service_state, billing_state, state) AS state,
                COALESCE(service_zip, billing_zip, zip) AS zip_code,
                status,
                created_at
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
                f" AND (name ILIKE ${placeholder} OR email ILIKE ${placeholder} OR company_name ILIKE ${placeholder})"
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
                count_query += f" AND (name ILIKE ${cp} OR email ILIKE ${cp} OR company_name ILIKE ${cp})"
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

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error listing customers: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list customers")


@router.post("")
@router.post("/")  # Handle both with and without trailing slash
async def create_customer(
    request: Request,
    customer: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a customer for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")

        name = (customer.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Customer name is required")

        email = (customer.get("email") or None) or None
        phone = (customer.get("phone") or customer.get("mobile") or None) or None

        company_name = customer.get("company_name") or customer.get("company") or None

        address = customer.get("address") or customer.get("service_address") or customer.get("billing_address") or None
        city = customer.get("city") or customer.get("service_city") or customer.get("billing_city") or None
        state = customer.get("state") or customer.get("service_state") or customer.get("billing_state") or None
        zip_code = customer.get("zip") or customer.get("zip_code") or customer.get("service_zip") or customer.get("billing_zip") or None

        status = (customer.get("status") or "active").strip() or "active"

        customer_id = uuid4()

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                org_id = await conn.fetchval(
                    "SELECT org_id FROM customers WHERE tenant_id = $1 LIMIT 1",
                    tenant_id,
                )
                if not org_id:
                    org_id = UUID("00000000-0000-0000-0000-000000000001")

                row = await conn.fetchrow(
                    """
                    INSERT INTO customers (
                        id,
                        tenant_id,
                        org_id,
                        name,
                        email,
                        phone,
                        company_name,
                        service_address,
                        service_city,
                        service_state,
                        service_zip,
                        address_line1,
                        city,
                        state,
                        zip,
                        status,
                        is_active,
                        created_at,
                        updated_at
                    ) VALUES (
                        $1, $2, $3,
                        $4, $5, $6, $7,
                        $8, $9, $10, $11,
                        $8, $9, $10, $11,
                        $12,
                        TRUE,
                        NOW(), NOW()
                    )
                    RETURNING id::text AS id
                    """,
                    customer_id,
                    tenant_id,
                    org_id,
                    name,
                    email,
                    phone,
                    company_name,
                    address,
                    city,
                    state,
                    zip_code,
                    status,
                )

        return {"success": True, "data": {"id": row["id"] if row else str(customer_id)}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating customer: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create customer")


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    request: Request,
    customer: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update a customer for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        customer_uuid = _parse_uuid(customer_id, "customer_id")

        allowed: Dict[str, Any] = {}

        if "name" in customer:
            allowed["name"] = (customer.get("name") or "").strip() or None
        if "email" in customer:
            allowed["email"] = (customer.get("email") or None) or None
        if "phone" in customer or "mobile" in customer:
            allowed["phone"] = (customer.get("phone") or customer.get("mobile") or None) or None

        if "company" in customer or "company_name" in customer:
            allowed["company_name"] = customer.get("company_name") or customer.get("company") or None

        if "address" in customer or "service_address" in customer:
            allowed["service_address"] = customer.get("service_address") or customer.get("address") or None
            allowed["address_line1"] = allowed["service_address"]
        if "city" in customer or "service_city" in customer:
            allowed["service_city"] = customer.get("service_city") or customer.get("city") or None
            allowed["city"] = allowed["service_city"]
        if "state" in customer or "service_state" in customer:
            allowed["service_state"] = customer.get("service_state") or customer.get("state") or None
            allowed["state"] = allowed["service_state"]
        if "zip" in customer or "zip_code" in customer or "service_zip" in customer:
            allowed["service_zip"] = customer.get("service_zip") or customer.get("zip") or customer.get("zip_code") or None
            allowed["zip"] = allowed["service_zip"]

        if "status" in customer:
            allowed["status"] = (customer.get("status") or "").strip() or None
        if "is_active" in customer:
            allowed["is_active"] = bool(customer.get("is_active"))

        # Remove None values to avoid blanking fields unintentionally.
        update_fields = {k: v for k, v in allowed.items() if v is not None}
        if not update_fields:
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        set_clauses = []
        values: list[Any] = []
        idx = 1
        for key, value in update_fields.items():
            set_clauses.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1
        set_clauses.append("updated_at = NOW()")

        values.extend([customer_uuid, tenant_id])

        query = f"""
            UPDATE customers
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND tenant_id = ${idx + 1}
            RETURNING id::text AS id
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True, "data": {"id": row["id"]}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating customer: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update customer")


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Soft-delete a customer for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        customer_uuid = _parse_uuid(customer_id, "customer_id")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE customers
                SET status = 'inactive',
                    is_active = FALSE,
                    updated_at = NOW()
                WHERE id = $1 AND tenant_id = $2
                RETURNING id::text AS id
                """,
                customer_uuid,
                tenant_id,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting customer: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete customer")

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
