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
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/complete-erp", tags=["Complete ERP Alias"])


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
    return await get_erp_customers(request, skip, limit, current_user)


@router.get("/customers/{customer_id}")
async def get_complete_erp_customer(
    request: Request,
    customer_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single customer by ID."""
    try:
        from routes.customers import get_customer as get_customer_impl
        return await get_customer_impl(request=request, customer_id=customer_id, current_user=current_user)
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
    try:
        from routes.customers import create_customer as create_customer_impl
        body = await request.json()
        return await create_customer_impl(request=request, customer=body, current_user=current_user)
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
    try:
        from routes.customers import update_customer as update_customer_impl
        body = await request.json()
        return await update_customer_impl(request=request, customer_id=customer_id, customer=body, current_user=current_user)
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
    try:
        from routes.customers import delete_customer as delete_customer_impl
        return await delete_customer_impl(request=request, customer_id=customer_id, current_user=current_user)
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
    return await get_erp_jobs(request, skip, limit, current_user)


@router.get("/jobs/{job_id}")
async def get_complete_erp_job(
    request: Request,
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single job by ID."""
    try:
        from routes.jobs import get_job as get_job_impl
        return await get_job_impl(request=request, job_id=job_id, current_user=current_user)
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
    return await get_erp_invoices(request, skip, limit, current_user)


@router.get("/invoices/{invoice_id}")
async def get_complete_erp_invoice(
    request: Request,
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single invoice by ID."""
    try:
        from routes.invoices import get_invoice as get_invoice_impl
        return await get_invoice_impl(request=request, invoice_id=invoice_id, current_user=current_user)
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
    return await get_erp_estimates(request, skip, limit, current_user)


@router.get("/estimates/{estimate_id}")
async def get_complete_erp_estimate(
    request: Request,
    estimate_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get single estimate by ID."""
    try:
        from routes.estimates import get_estimate as get_estimate_impl
        return await get_estimate_impl(request=request, estimate_id=estimate_id, current_user=current_user)
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
