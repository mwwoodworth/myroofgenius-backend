"""
Complete ERP Alias Router
Provides /api/v1/complete-erp/* routes that map to /api/v1/erp/* handlers

This router fixes the API contract mismatch between myroofgenius-app (which calls
/api/v1/complete-erp/*) and the backend (which serves /api/v1/erp/*).

Created: 2025-12-25
Purpose: Bridge the frontend-backend route mismatch
"""

from __future__ import annotations

import logging
from uuid import UUID
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/complete-erp", tags=["Complete ERP Alias"])

def _normalize_tenant_id(tenant_id: Optional[str]) -> Optional[str]:
    if not tenant_id:
        return None
    try:
        return str(UUID(str(tenant_id)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid tenant_id") from exc


def _with_tenant_context(current_user: Dict[str, Any], tenant_id: Optional[str]) -> Dict[str, Any]:
    normalized = _normalize_tenant_id(tenant_id)
    if not normalized:
        return current_user

    existing = current_user.get("tenant_id")
    if existing and str(existing) != normalized:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    return {**current_user, "tenant_id": normalized}


# ============================================================================
# CUSTOMERS
# ============================================================================

@router.get("/customers")
async def get_complete_erp_customers(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get customers (alias for /api/v1/erp/customers)."""
    from routes.erp_complete import get_erp_customers
    scoped_user = _with_tenant_context(current_user, tenant_id)
    return await get_erp_customers(
        request=request,
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        current_user=scoped_user,
    )


@router.get("/customers/{customer_id}")
async def get_complete_erp_customer(
    request: Request,
    customer_id: str,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single customer by ID."""
    scoped_user = _with_tenant_context(current_user, tenant_id)
    tid = scoped_user.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email, phone, company, status, address, city, state, zip_code, notes, created_at, updated_at "
                "FROM customers WHERE id = $1 AND tenant_id = $2",
                customer_id, tid,
            )
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer = dict(row)
        customer["id"] = str(customer["id"])
        return {"customer": customer, "status": "operational"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers")
async def create_complete_erp_customer(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a new customer."""
    tid = current_user.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        body = await request.json()
        import uuid
        customer_id = str(uuid.uuid4())
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO customers (id, tenant_id, name, email, phone, company, address, city, state, zip_code, notes, status, created_at, updated_at) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())",
                customer_id, tid,
                body.get("name", ""), body.get("email"), body.get("phone"),
                body.get("company"), body.get("address"), body.get("city"),
                body.get("state"), body.get("zip_code"), body.get("notes"),
                body.get("status", "active"),
            )
        return {"id": customer_id, "message": "Customer created", "status": "operational"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/customers/{customer_id}")
async def update_complete_erp_customer(
    request: Request,
    customer_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update a customer."""
    tid = current_user.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        body = await request.json()
        set_parts = []
        params = []
        idx = 1
        for field in ("name", "email", "phone", "company", "address", "city", "state", "zip_code", "notes", "status"):
            if field in body:
                set_parts.append(f"{field} = ${idx}")
                params.append(body[field])
                idx += 1
        if not set_parts:
            raise HTTPException(status_code=400, detail="No fields to update")
        set_parts.append(f"updated_at = NOW()")
        params.extend([customer_id, tid])
        query = f"UPDATE customers SET {', '.join(set_parts)} WHERE id = ${idx} AND tenant_id = ${idx + 1}"
        async with db_pool.acquire() as conn:
            result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"id": customer_id, "message": "Customer updated", "status": "operational"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/customers/{customer_id}")
async def delete_complete_erp_customer(
    request: Request,
    customer_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Delete a customer."""
    tid = current_user.get("tenant_id")
    if not tid:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM customers WHERE id = $1 AND tenant_id = $2",
                customer_id, tid,
            )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted", "status": "operational"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOBS
# ============================================================================

@router.get("/jobs")
async def get_complete_erp_jobs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get jobs (alias for /api/v1/erp/jobs)."""
    from routes.erp_complete import get_erp_jobs
    scoped_user = _with_tenant_context(current_user, tenant_id)
    return await get_erp_jobs(
        request=request,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        current_user=scoped_user,
    )


@router.get("/jobs/{job_id}")
async def get_complete_erp_job(
    request: Request,
    job_id: str,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single job by ID."""
    try:
        from routes.jobs import get_job as get_job_impl
        scoped_user = _with_tenant_context(current_user, tenant_id)
        return await get_job_impl(request=request, job_id=job_id, current_user=scoped_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs")
async def create_complete_erp_job(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a new job."""
    try:
        from routes.jobs import create_job as create_job_impl
        body = await request.json()
        return await create_job_impl(request=request, job=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}")
async def update_complete_erp_job(
    request: Request,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update a job."""
    try:
        from routes.jobs import update_job as update_job_impl
        body = await request.json()
        return await update_job_impl(request=request, job_id=job_id, job=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_complete_erp_job(
    request: Request,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Delete a job."""
    try:
        from routes.jobs import delete_job as delete_job_impl
        return await delete_job_impl(request=request, job_id=job_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOICES
# ============================================================================

@router.get("/invoices")
async def get_complete_erp_invoices(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get invoices (alias for /api/v1/erp/invoices)."""
    from routes.erp_complete import get_erp_invoices
    scoped_user = _with_tenant_context(current_user, tenant_id)
    return await get_erp_invoices(
        request=request,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        current_user=scoped_user,
    )


@router.get("/invoices/{invoice_id}")
async def get_complete_erp_invoice(
    request: Request,
    invoice_id: str,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single invoice by ID."""
    try:
        from routes.invoices import get_invoice as get_invoice_impl
        scoped_user = _with_tenant_context(current_user, tenant_id)
        return await get_invoice_impl(request=request, invoice_id=invoice_id, current_user=scoped_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices")
async def create_complete_erp_invoice(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a new invoice."""
    try:
        from routes.invoices import create_invoice as create_invoice_impl
        body = await request.json()
        return await create_invoice_impl(request=request, invoice=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invoices/{invoice_id}")
async def update_complete_erp_invoice(
    request: Request,
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update an invoice."""
    try:
        from routes.invoices import update_invoice as update_invoice_impl
        body = await request.json()
        return await update_invoice_impl(request=request, invoice_id=invoice_id, invoice=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invoices/{invoice_id}")
async def delete_complete_erp_invoice(
    request: Request,
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Delete an invoice."""
    try:
        from routes.invoices import delete_invoice as delete_invoice_impl
        return await delete_invoice_impl(request=request, invoice_id=invoice_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ESTIMATES
# ============================================================================

@router.get("/estimates")
async def get_complete_erp_estimates(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get estimates (alias for /api/v1/erp/estimates)."""
    from routes.erp_complete import get_erp_estimates
    scoped_user = _with_tenant_context(current_user, tenant_id)
    return await get_erp_estimates(
        request=request,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        current_user=scoped_user,
    )


@router.get("/estimates/{estimate_id}")
async def get_complete_erp_estimate(
    request: Request,
    estimate_id: str,
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single estimate by ID."""
    try:
        from routes.estimates import get_estimate as get_estimate_impl
        scoped_user = _with_tenant_context(current_user, tenant_id)
        return await get_estimate_impl(request=request, estimate_id=estimate_id, current_user=scoped_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting estimate {estimate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimates")
async def create_complete_erp_estimate(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a new estimate."""
    try:
        from routes.estimates import create_estimate as create_estimate_impl
        body = await request.json()
        return await create_estimate_impl(request=request, estimate=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/estimates/{estimate_id}")
async def update_complete_erp_estimate(
    request: Request,
    estimate_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update an estimate."""
    try:
        from routes.estimates import update_estimate as update_estimate_impl
        body = await request.json()
        return await update_estimate_impl(request=request, estimate_id=estimate_id, estimate=body, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating estimate {estimate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/estimates/{estimate_id}")
async def delete_complete_erp_estimate(
    request: Request,
    estimate_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Delete an estimate."""
    try:
        from routes.estimates import delete_estimate as delete_estimate_impl
        return await delete_estimate_impl(request=request, estimate_id=estimate_id, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting estimate {estimate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimates/{estimate_id}/ai-optimize")
async def optimize_complete_erp_estimate(
    request: Request,
    estimate_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """AI optimize an estimate."""
    try:
        # Call AI optimization endpoint if it exists
        from routes.estimates import optimize_estimate as optimize_estimate_impl
        return await optimize_estimate_impl(request=request, estimate_id=estimate_id, current_user=current_user)
    except ImportError:
        # AI optimization not available, return basic response
        return {"status": "optimization_not_available", "estimate_id": estimate_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing estimate {estimate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimates/{estimate_id}/convert-to-job")
async def convert_estimate_to_job(
    request: Request,
    estimate_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Convert estimate to job."""
    try:
        from routes.estimates import convert_to_job as convert_to_job_impl
        body = await request.json()
        return await convert_to_job_impl(request=request, estimate_id=estimate_id, data=body, current_user=current_user)
    except ImportError:
        # Conversion not available in estimates module
        return {"status": "conversion_not_available", "estimate_id": estimate_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting estimate {estimate_id} to job: {e}")
        raise HTTPException(status_code=500, detail=str(e))
