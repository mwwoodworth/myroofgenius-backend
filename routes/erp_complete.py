from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from core.supabase_auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/v1/erp", tags=["ERP"])


@router.get("/customers")
async def get_erp_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ERP customers with real data from database"""
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM customers"))
        total = count_result.scalar()

        customers_result = db.execute(
            text(
                """
                SELECT
                    id, name, email, phone,
                    external_id, address, city, state, zip,
                    created_at, updated_at
                FROM customers
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """
            ),
            {"limit": limit, "skip": skip},
        )

        customers: List[Dict[str, Any]] = []
        for row in customers_result:
            customers.append(
                {
                    "id": str(row.id),
                    "name": row.name,
                    "email": row.email,
                    "phone": row.phone,
                    "external_id": row.external_id,
                    "address": row.address,
                    "city": row.city,
                    "state": row.state,
                    "zip_code": row.zip,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )

        return {
            "customers": customers,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/jobs")
async def get_erp_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ERP jobs with real data from database"""
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM jobs"))
        total = count_result.scalar()

        jobs_result = db.execute(
            text(
                """
                SELECT
                    id, job_number, name, status,
                    customer_id, start_date, end_date,
                    created_at, updated_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """
            ),
            {"limit": limit, "skip": skip},
        )

        jobs: List[Dict[str, Any]] = []
        for row in jobs_result:
            jobs.append(
                {
                    "id": str(row.id),
                    "job_number": row.job_number,
                    "name": row.name,
                    "status": row.status,
                    "customer_id": str(row.customer_id) if row.customer_id else None,
                    "start_date": row.start_date.isoformat() if row.start_date else None,
                    "end_date": row.end_date.isoformat() if row.end_date else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )

        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/estimates")
async def get_erp_estimates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ERP estimates with real data from database"""
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM estimates"))
        total = count_result.scalar()

        estimates_result = db.execute(
            text(
                """
                SELECT
                    id, estimate_number, customer_id,
                    status, total_amount, created_at, updated_at
                FROM estimates
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """
            ),
            {"limit": limit, "skip": skip},
        )

        estimates: List[Dict[str, Any]] = []
        for row in estimates_result:
            estimates.append(
                {
                    "id": str(row.id),
                    "estimate_number": row.estimate_number,
                    "customer_id": str(row.customer_id) if row.customer_id else None,
                    "status": row.status,
                    "total_amount": float(row.total_amount) if row.total_amount else 0,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )

        return {
            "estimates": estimates,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/invoices")
async def get_erp_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ERP invoices with real data from database"""
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM invoices"))
        total = count_result.scalar()

        invoices_result = db.execute(
            text(
                """
                SELECT
                    id, invoice_number, customer_id,
                    status, total_amount, due_date,
                    created_at, updated_at
                FROM invoices
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
                """
            ),
            {"limit": limit, "skip": skip},
        )

        invoices: List[Dict[str, Any]] = []
        for row in invoices_result:
            invoices.append(
                {
                    "id": str(row.id),
                    "invoice_number": row.invoice_number,
                    "customer_id": str(row.customer_id) if row.customer_id else None,
                    "status": row.status,
                    "total_amount": float(row.total_amount) if row.total_amount else 0,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )

        return {
            "invoices": invoices,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/dashboard")
async def get_erp_dashboard(
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ERP dashboard metrics with real data."""
    try:
        jobs_count = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
        estimates_count = db.execute(text("SELECT COUNT(*) FROM estimates")).scalar()
        invoices_count = db.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
        customers_count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()

        active_jobs = db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE status IN ('in_progress', 'scheduled')")
        ).scalar()

        pending_invoices = db.execute(
            text("SELECT COUNT(*) FROM invoices WHERE status IN ('pending', 'overdue')")
        ).scalar()

        revenue_result = db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN created_at >= date_trunc('month', CURRENT_DATE) THEN total_amount ELSE 0 END), 0) as mtd,
                    COALESCE(SUM(CASE WHEN created_at >= date_trunc('year', CURRENT_DATE) THEN total_amount ELSE 0 END), 0) as ytd
                FROM invoices
                WHERE status = 'paid'
                """
            )
        ).first()

        return {
            "metrics": {
                "total_jobs": jobs_count,
                "total_estimates": estimates_count,
                "total_invoices": invoices_count,
                "total_customers": customers_count,
                "active_jobs": active_jobs,
                "pending_invoices": pending_invoices,
                "revenue_mtd": float(revenue_result.mtd) if revenue_result else 0,
                "revenue_ytd": float(revenue_result.ytd) if revenue_result else 0,
            },
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/inventory")
async def get_erp_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get inventory items with real data."""
    try:
        table_check = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'inventory_items'
                )
                """
            )
        ).scalar()

        if not table_check:
            raise HTTPException(
                status_code=501,
                detail="Inventory module not configured (missing inventory_items table)",
            )

        count_result = db.execute(text("SELECT COUNT(*) FROM inventory_items"))
        total = count_result.scalar()

        inventory_result = db.execute(
            text(
                """
                SELECT
                    id, name, sku, quantity_on_hand, unit_of_measure,
                    reorder_point, reorder_quantity, unit_cost
                FROM inventory_items
                ORDER BY name
                LIMIT :limit OFFSET :skip
                """
            ),
            {"limit": limit, "skip": skip},
        )

        inventory: List[Dict[str, Any]] = []
        for row in inventory_result:
            inventory.append(
                {
                    "id": str(row.id),
                    "name": row.name,
                    "sku": row.sku,
                    "quantity": row.quantity_on_hand,
                    "unit": row.unit_of_measure,
                    "reorder_point": row.reorder_point,
                    "unit_cost": float(row.unit_cost) if row.unit_cost else 0,
                }
            )

        return {
            "inventory": inventory,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": "operational",
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e


@router.get("/schedule")
async def get_erp_schedule(
    _current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get scheduled jobs and events."""
    try:
        jobs_result = db.execute(
            text(
                """
                SELECT
                    j.id, j.job_number, j.name, j.start_date,
                    c.name as customer_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                WHERE j.start_date >= CURRENT_DATE
                ORDER BY j.start_date
                LIMIT 20
                """
            )
        )

        schedule: List[Dict[str, Any]] = []
        for row in jobs_result:
            schedule.append(
                {
                    "id": str(row.id),
                    "type": "job",
                    "title": f"Job #{row.job_number}: {row.name}",
                    "customer": row.customer_name,
                    "date": row.start_date.isoformat() if row.start_date else None,
                }
            )

        return {
            "schedule": schedule,
            "total": len(schedule),
            "status": "operational",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

