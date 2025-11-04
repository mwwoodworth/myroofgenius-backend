"""
Dashboard Statistics API
Provides aggregated ERP metrics for Weathercraft and BrainOps dashboards.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

import asyncpg

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


async def get_db_pool(request: Request) -> Optional[asyncpg.Pool]:
    """Retrieve the shared asyncpg pool from application state."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        logger.warning("Dashboard stats requested but database pool is unavailable")
    return pool


def _to_float(value: Optional[Any]) -> float:
    """Convert numeric or decimal values to float safely."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _empty_stats() -> Dict[str, Any]:
    """Return baseline stats payload with zeroed metrics."""
    return {
        "revenue": {"total": 0.0, "pending": 0.0, "overdue": 0, "formatted": "$0"},
        "customers": {"total": 0, "new_this_month": 0},
        "jobs": {"total": 0, "active": 0, "completed": 0},
        "invoices": {"total": 0, "pending": 0, "overdue": 0, "pending_amount": 0.0},
        "estimates": {"total": 0, "pending": 0},
        "employees": {"total": 0, "active": 0},
        "equipment": {"total": 0, "utilization": 0},
        "inventory": {"total_items": 0, "total_value": 0.0},
        "leads": {
            "total": 0,
            "active": 0,
            "estimates": 0,
            "service_tickets": 0,
            "open_service_requests": 0,
        },
    }


@router.get("/stats")
async def get_dashboard_stats(
    request: Request,
    tenant_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """
    Return aggregated dashboard statistics for the authenticated tenant.

    Mirrors the metrics used by the Weathercraft ERP dashboard while operating
    directly against the production database.
    """
    resolved_tenant = tenant_id or current_user.get("tenant_id")
    if not resolved_tenant:
        raise HTTPException(status_code=400, detail="Tenant context is required")

    requester_tenant = current_user.get("tenant_id")
    requester_role = (current_user.get("role") or "").lower()
    if (
        tenant_id
        and tenant_id != requester_tenant
        and requester_role not in {"service", "system", "admin"}
    ):
        raise HTTPException(status_code=403, detail="Forbidden for tenant scope")

    pool = await get_db_pool(request)
    now = datetime.now(timezone.utc)

    if pool is None:
        logger.warning("Dashboard stats falling back to offline placeholder data")
        return {
            "success": True,
            "tenant_id": resolved_tenant,
            "stats": _empty_stats(),
            "generated_at": now.isoformat(),
            "offline": True,
        }

    try:
        async with pool.acquire() as conn:
            customers = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE created_at >= date_trunc('month', NOW())
                    ) AS new_this_month
                FROM customers
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            jobs = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE status IN ('in_progress', 'scheduled')
                    ) AS active,
                    COUNT(*) FILTER (
                        WHERE status = 'completed'
                    ) AS completed
                FROM jobs
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            invoices = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE COALESCE(LOWER(payment_status), '') <> 'paid'
                    ) AS pending,
                    COUNT(*) FILTER (
                        WHERE COALESCE(LOWER(payment_status), '') <> 'paid'
                          AND due_date IS NOT NULL
                          AND due_date < NOW()
                    ) AS overdue,
                    COALESCE(SUM(
                        CASE
                            WHEN LOWER(payment_status) = 'paid'
                                THEN COALESCE(total_amount, amount, 0)
                            ELSE 0
                        END
                    ), 0) AS total_revenue,
                    COALESCE(SUM(
                        CASE
                            WHEN COALESCE(LOWER(payment_status), '') <> 'paid'
                                THEN COALESCE(total_amount, amount, 0)
                            ELSE 0
                        END
                    ), 0) AS pending_amount
                FROM invoices
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            estimates = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'pending') AS pending
                FROM estimates
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            employees = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE employment_status = 'active'
                    ) AS active
                FROM employees
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            equipment = await conn.fetchrow(
                """
                SELECT COUNT(*) AS total
                FROM equipment
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            inventory = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total_items,
                    COALESCE(SUM(
                        COALESCE(cost, unit_price, 0)::numeric
                        * COALESCE(quantity, 0)::numeric
                    ), 0) AS total_value
                FROM inventory_items
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            leads = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE COALESCE(status, 'active') <> 'lost'
                    ) AS active,
                    COUNT(*) FILTER (WHERE source = 'estimate') AS estimates,
                    COUNT(*) FILTER (WHERE source = 'service_ticket') AS service_tickets
                FROM leads
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

            service_tickets = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (
                        WHERE COALESCE(stage, '') NOT IN ('completed', 'cancelled', 'void')
                    ) AS open_requests
                FROM service_tickets
                WHERE tenant_id = $1
                """,
                resolved_tenant,
            )

        total_equipment = equipment["total"] or 0
        active_employees = employees["active"] or 0
        utilization = (
            round(min(active_employees, total_equipment) / total_equipment * 100)
            if total_equipment
            else 0
        )

        total_revenue = _to_float(invoices["total_revenue"])
        formatted_revenue = f"${total_revenue:,.0f}"

        stats = {
            "revenue": {
                "total": total_revenue,
                "pending": _to_float(invoices["pending_amount"]),
                "overdue": invoices["overdue"] or 0,
                "formatted": formatted_revenue,
            },
            "customers": {
                "total": customers["total"] or 0,
                "new_this_month": customers["new_this_month"] or 0,
            },
            "jobs": {
                "total": jobs["total"] or 0,
                "active": jobs["active"] or 0,
                "completed": jobs["completed"] or 0,
            },
            "invoices": {
                "total": invoices["total"] or 0,
                "pending": invoices["pending"] or 0,
                "overdue": invoices["overdue"] or 0,
                "pending_amount": _to_float(invoices["pending_amount"]),
            },
            "estimates": {
                "total": estimates["total"] or 0,
                "pending": estimates["pending"] or 0,
            },
            "employees": {
                "total": employees["total"] or 0,
                "active": active_employees,
            },
            "equipment": {
                "total": total_equipment,
                "utilization": utilization,
            },
            "inventory": {
                "total_items": inventory["total_items"] or 0,
                "total_value": _to_float(inventory["total_value"]),
            },
            "leads": {
                "total": leads["total"] or 0,
                "active": leads["active"] or 0,
                "estimates": leads["estimates"] or 0,
                "service_tickets": leads["service_tickets"] or 0,
                "open_service_requests": service_tickets["open_requests"] or 0,
            },
        }

        return {
            "success": True,
            "tenant_id": resolved_tenant,
            "stats": stats,
            "generated_at": now.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to compute dashboard stats: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to compute dashboard stats") from exc

