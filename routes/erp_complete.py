"""
ERP Compatibility Endpoints (/api/v1/erp/*)

This module provides the subset of endpoints used by the Weathercraft ERP UI.
Implementation note: these are thin wrappers around the tenant-isolated CRUD
routers (customers/jobs/estimates/invoices/inventory) to keep behavior and schema
consistent across the API surface.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.supabase_auth import get_authenticated_user

# NOTE: STORE import removed 2025-12-18 - fake data fallback is dangerous
# System should fail with 503 error, not return fake/mock data that misleads users

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/erp", tags=["ERP"])


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _should_fallback(exc: HTTPException) -> bool:
    return exc.status_code in {500, 503}


@router.get("/customers")
async def get_erp_customers(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get ERP customers (tenant-scoped)."""
    try:
        from routes.customers import list_customers as list_customers_impl

        resp = await list_customers_impl(
            request=request,
            limit=limit,
            offset=skip,
            status=status,
            search=search,
            current_user=current_user,
        )
        customers = resp.get("data") or []
        total = resp.get("total", len(customers))

        return {"customers": customers, "total": total, "skip": skip, "limit": limit, "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            logger.error("ERP customers query failed with 5xx - returning 503")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
        raise


@router.get("/jobs")
async def get_erp_jobs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get ERP jobs (tenant-scoped)."""
    try:
        from routes.jobs import list_jobs as list_jobs_impl

        resp = await list_jobs_impl(
            request=request,
            limit=limit,
            offset=skip,
            status=status,
            customer_id=customer_id,
            assigned_to=assigned_to,
            current_user=current_user,
        )
        data = resp.get("data") or []
        total = resp.get("total", len(data))

        jobs: List[Dict[str, Any]] = []
        for row in data:
            job: Dict[str, Any] = dict(row)
            jobs.append(
                {
                    "id": str(job.get("id")),
                    "job_number": job.get("job_number"),
                    "name": job.get("title") or job.get("name"),
                    "status": job.get("status"),
                    "customer_id": str(job.get("customer_id")) if job.get("customer_id") else None,
                    "start_date": _iso(job.get("scheduled_date") or job.get("scheduled_start")),
                    "end_date": _iso(job.get("completed_date") or job.get("scheduled_end")),
                    "created_at": _iso(job.get("created_at")),
                    "updated_at": _iso(job.get("updated_at")),
                }
            )

        return {"jobs": jobs, "total": total, "skip": skip, "limit": limit, "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            logger.error("ERP jobs query failed with 5xx - returning 503")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
        raise


@router.get("/estimates")
async def get_erp_estimates(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get ERP estimates (tenant-scoped)."""
    try:
        from routes.estimates import list_estimates as list_estimates_impl

        resp = await list_estimates_impl(
            request=request,
            limit=min(limit, 100),
            offset=skip,
            status=status,
            customer_id=customer_id,
            job_id=job_id,
            current_user=current_user,
        )

        payload = resp.get("data") or {}
        estimates = payload.get("estimates") or []
        total = payload.get("total", len(estimates))

        mapped: List[Dict[str, Any]] = []
        for row in estimates:
            est: Dict[str, Any] = dict(row)
            mapped.append(
                {
                    "id": str(est.get("id")),
                    "estimate_number": est.get("estimate_number"),
                    "customer_id": str(est.get("customer_id")) if est.get("customer_id") else None,
                    "status": est.get("status"),
                    "total_amount": est.get("total_amount") or est.get("total") or 0,
                    "created_at": _iso(est.get("created_at")),
                    "updated_at": _iso(est.get("updated_at")),
                }
            )

        return {"estimates": mapped, "total": total, "skip": skip, "limit": limit, "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            logger.error("ERP estimates query failed with 5xx - returning 503")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
        raise


@router.get("/invoices")
async def get_erp_invoices(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get ERP invoices (tenant-scoped)."""
    try:
        from routes.invoices import list_invoices as list_invoices_impl

        resp = await list_invoices_impl(
            request=request,
            limit=min(limit, 100),
            offset=skip,
            status=status,
            customer_id=customer_id,
            job_id=job_id,
            current_user=current_user,
        )
        invoices = resp.get("data") or []
        total = resp.get("total", len(invoices))

        mapped: List[Dict[str, Any]] = []
        for row in invoices:
            inv: Dict[str, Any] = dict(row)
            mapped.append(
                {
                    "id": str(inv.get("id")),
                    "invoice_number": inv.get("invoice_number"),
                    "customer_id": str(inv.get("customer_id")) if inv.get("customer_id") else None,
                    "status": inv.get("status"),
                    "total_amount": inv.get("total_amount") or inv.get("amount") or 0,
                    "due_date": _iso(inv.get("due_date")),
                    "created_at": _iso(inv.get("created_at")),
                    "updated_at": _iso(inv.get("updated_at")),
                }
            )

        return {"invoices": mapped, "total": total, "skip": skip, "limit": limit, "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            logger.error("ERP invoices query failed with 5xx - returning 503")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
        raise


@router.get("/dashboard")
@router.get("/dashboard/stats")
async def get_erp_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get ERP dashboard metrics."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        # No fake data fallback - fail properly so users know there's an issue
        logger.error("ERP dashboard: db_pool not available - returning 503")
        raise HTTPException(status_code=503, detail="Database connection not available")

    query = """
        SELECT
            (SELECT COUNT(*) FROM jobs WHERE tenant_id = $1) AS total_jobs,
            (SELECT COUNT(*) FROM estimates WHERE tenant_id = $1) AS total_estimates,
            (SELECT COUNT(*) FROM invoices WHERE tenant_id = $1) AS total_invoices,
            (SELECT COUNT(*) FROM customers WHERE tenant_id = $1) AS total_customers,
            (SELECT COUNT(*) FROM jobs WHERE tenant_id = $1 AND status IN ('in_progress', 'scheduled')) AS active_jobs,
            (SELECT COUNT(*) FROM invoices WHERE tenant_id = $1 AND status IN ('pending', 'overdue')) AS pending_invoices,
            (SELECT COALESCE(SUM(CASE WHEN created_at >= date_trunc('month', CURRENT_DATE) THEN total_amount ELSE 0 END), 0)
             FROM invoices WHERE tenant_id = $1 AND status = 'paid') AS revenue_mtd,
            (SELECT COALESCE(SUM(CASE WHEN created_at >= date_trunc('year', CURRENT_DATE) THEN total_amount ELSE 0 END), 0)
             FROM invoices WHERE tenant_id = $1 AND status = 'paid') AS revenue_ytd
    """

    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id)
        metrics = dict(row) if row else {}
        for key in ("revenue_mtd", "revenue_ytd"):
            if metrics.get(key) is not None:
                metrics[key] = float(metrics[key])
        return {"metrics": metrics, "status": "operational"}
    except Exception as exc:
        logger.error("ERP dashboard query failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc


@router.get("/inventory")
async def get_erp_inventory(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get inventory items (tenant-scoped)."""
    try:
        from routes.inventory import list_inventory_items as list_inventory_items_impl

        resp = await list_inventory_items_impl(
            request=request,
            limit=min(limit, 200),
            offset=skip,
            category=None,
            location_id=None,
            current_user=current_user,
        )
        items = resp.get("data") or []
        total = resp.get("total", len(items))

        inventory = []
        for item in items:
            inv: Dict[str, Any] = dict(item)
            inventory.append(
                {
                    "id": str(inv.get("id")),
                    "name": inv.get("item_name") or inv.get("name"),
                    "sku": inv.get("sku"),
                    "quantity": inv.get("quantity_on_hand") or inv.get("quantity") or 0,
                    "unit": inv.get("uom") or inv.get("unit") or inv.get("unit_of_measure"),
                    "reorder_point": inv.get("reorder_point"),
                    "unit_cost": float(inv.get("unit_cost") or 0),
                }
            )

        return {"inventory": inventory, "total": total, "skip": skip, "limit": limit, "status": "operational"}
    except HTTPException as exc:
        if _should_fallback(exc):
            logger.error("ERP inventory query failed with 5xx - returning 503")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
        raise


@router.get("/schedule")
async def get_erp_schedule(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Get scheduled jobs and events."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        # No fake data fallback - fail properly
        logger.error("ERP schedule: db_pool not available - returning 503")
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT j.id, j.job_number, j.title, j.scheduled_date,
                       c.name AS customer_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                WHERE j.tenant_id = $1
                  AND j.scheduled_date >= CURRENT_DATE
                ORDER BY j.scheduled_date ASC
                LIMIT 20
                """,
                tenant_id,
            )
    except Exception as exc:
        logger.error("ERP schedule query failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    schedule: List[Dict[str, Any]] = []
    for row in rows:
        job = dict(row)
        schedule.append(
            {
                "id": str(job.get("id")),
                "type": "job",
                "title": f"Job #{job.get('job_number')}: {job.get('title')}",
                "customer": job.get("customer_name"),
                "date": _iso(job.get("scheduled_date")),
            }
        )

    return {"schedule": schedule, "total": len(schedule), "status": "operational"}
