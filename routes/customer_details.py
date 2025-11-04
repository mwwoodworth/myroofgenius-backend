"""
Customer Detail Endpoints
Comprehensive customer information including history, analytics, and relationships
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customers/{customer_id}", tags=["Customer Details"])

# ============================================================================
# CUSTOMER DETAILS
# ============================================================================

@router.get("/summary")
async def get_customer_summary(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive customer summary with all metrics"""
    try:
        # Get customer with aggregated data
        result = db.execute(
            text("""
                SELECT
                    c.*,
                    COUNT(DISTINCT j.id) as total_jobs,
                    COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.id END) as completed_jobs,
                    COUNT(DISTINCT CASE WHEN j.status = 'in_progress' THEN j.id END) as active_jobs,
                    COUNT(DISTINCT i.id) as total_invoices,
                    COUNT(DISTINCT CASE WHEN i.status = 'paid' THEN i.id END) as paid_invoices,
                    COALESCE(SUM(j.total_amount), 0) as lifetime_value,
                    COALESCE(AVG(j.total_amount), 0) as avg_job_value,
                    MAX(j.created_at) as last_job_date,
                    MIN(j.created_at) as first_job_date,
                    COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.total_amount ELSE 0 END), 0) as total_paid,
                    COALESCE(SUM(CASE WHEN i.status = 'pending' THEN i.total_amount ELSE 0 END), 0) as total_pending
                FROM customers c
                LEFT JOIN jobs j ON c.id = j.customer_id
                LEFT JOIN invoices i ON c.id = i.customer_id
                WHERE c.id = :customer_id
                GROUP BY c.id
            """),
            {"customer_id": customer_id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        summary = dict(result._mapping)
        summary["id"] = str(summary["id"])

        # Calculate additional metrics
        if summary["first_job_date"] and summary["last_job_date"]:
            days_active = (summary["last_job_date"] - summary["first_job_date"]).days
            summary["customer_lifetime_days"] = days_active

        # Get recent activity
        recent_activity = db.execute(
            text("""
                SELECT 'job' as type, id, title as description, created_at
                FROM jobs WHERE customer_id = :customer_id
                UNION ALL
                SELECT 'invoice' as type, id, invoice_number as description, created_at
                FROM invoices WHERE customer_id = :customer_id
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"customer_id": customer_id}
        ).fetchall()

        summary["recent_activity"] = [dict(row._mapping) for row in recent_activity]

        log_data_access(db, current_user["id"], "customers", "summary", 1)
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer summary")

@router.get("/jobs")
async def get_customer_jobs(
    customer_id: str,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all jobs for a customer"""
    try:
        # Build query
        query = """
            SELECT j.*,
                   COUNT(DISTINCT ji.id) as item_count,
                   STRING_AGG(DISTINCT e.first_name || ' ' || e.last_name, ', ') as assigned_employees
            FROM jobs j
            LEFT JOIN job_items ji ON j.id = ji.job_id
            LEFT JOIN employee_jobs ej ON j.id = ej.job_id
            LEFT JOIN employees e ON ej.employee_id = e.id
            WHERE j.customer_id = :customer_id
        """

        params = {"customer_id": customer_id}

        if status:
            query += " AND j.status = :status"
            params["status"] = status

        query += " GROUP BY j.id ORDER BY j.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(query), params)

        jobs = []
        for row in result:
            job = dict(row._mapping)
            job["id"] = str(job["id"])
            job["customer_id"] = str(job["customer_id"])
            jobs.append(job)

        # Get total count
        count_result = db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE customer_id = :customer_id"),
            {"customer_id": customer_id}
        ).scalar()

        log_data_access(db, current_user["id"], "jobs", "list_by_customer", len(jobs))

        return {
            "jobs": jobs,
            "total": count_result,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error fetching customer jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer jobs")

@router.get("/invoices")
async def get_customer_invoices(
    customer_id: str,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all invoices for a customer"""
    try:
        query = """
            SELECT i.*,
                   j.title as job_title,
                   j.id as job_id
            FROM invoices i
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.customer_id = :customer_id
        """

        params = {"customer_id": customer_id}

        if status:
            query += " AND i.status = :status"
            params["status"] = status

        query += " ORDER BY i.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(query), params)

        invoices = []
        for row in result:
            invoice = dict(row._mapping)
            invoice["id"] = str(invoice["id"])
            invoice["customer_id"] = str(invoice["customer_id"])
            if invoice.get("job_id"):
                invoice["job_id"] = str(invoice["job_id"])
            invoices.append(invoice)

        # Get total count
        count_result = db.execute(
            text("SELECT COUNT(*) FROM invoices WHERE customer_id = :customer_id"),
            {"customer_id": customer_id}
        ).scalar()

        log_data_access(db, current_user["id"], "invoices", "list_by_customer", len(invoices))

        return {
            "invoices": invoices,
            "total": count_result,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error fetching customer invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer invoices")

@router.get("/timeline")
async def get_customer_timeline(
    customer_id: str,
    days: int = Query(90, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer interaction timeline"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        result = db.execute(
            text("""
                SELECT * FROM (
                    SELECT 'created' as event_type, created_at as event_date,
                           'Customer created' as description, NULL as metadata
                    FROM customers WHERE id = :customer_id

                    UNION ALL

                    SELECT 'job_created' as event_type, created_at as event_date,
                           'Job: ' || title as description,
                           jsonb_build_object('job_id', id, 'status', status, 'amount', total_amount) as metadata
                    FROM jobs WHERE customer_id = :customer_id

                    UNION ALL

                    SELECT 'invoice_created' as event_type, created_at as event_date,
                           'Invoice: ' || invoice_number as description,
                           jsonb_build_object('invoice_id', id, 'status', status, 'amount', total_amount) as metadata
                    FROM invoices WHERE customer_id = :customer_id

                    UNION ALL

                    SELECT 'estimate_created' as event_type, created_at as event_date,
                           'Estimate: ' || estimate_number as description,
                           jsonb_build_object('estimate_id', id, 'status', status, 'amount', estimated_cost) as metadata
                    FROM estimates WHERE customer_id = :customer_id

                    UNION ALL

                    SELECT 'payment_received' as event_type, payment_date as event_date,
                           'Payment received: $' || amount as description,
                           jsonb_build_object('payment_id', id, 'amount', amount, 'method', payment_method) as metadata
                    FROM payments WHERE customer_id = :customer_id
                ) events
                WHERE event_date >= :cutoff_date
                ORDER BY event_date DESC
            """),
            {"customer_id": customer_id, "cutoff_date": cutoff_date}
        )

        timeline = []
        for row in result:
            event = dict(row._mapping)
            event["event_date"] = event["event_date"].isoformat() if event["event_date"] else None
            timeline.append(event)

        log_data_access(db, current_user["id"], "customers", "timeline", 1)

        return {
            "customer_id": customer_id,
            "timeline": timeline,
            "period_days": days,
            "event_count": len(timeline)
        }

    except Exception as e:
        logger.error(f"Error fetching customer timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer timeline")

@router.get("/analytics")
async def get_customer_analytics(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer analytics and trends"""
    try:
        # Revenue trend by month
        revenue_trend = db.execute(
            text("""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as job_count,
                    SUM(total_amount) as revenue
                FROM jobs
                WHERE customer_id = :customer_id
                AND created_at >= NOW() - INTERVAL '12 months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month
            """),
            {"customer_id": customer_id}
        ).fetchall()

        # Job completion rate
        completion_stats = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
                    AVG(CASE
                        WHEN status = 'completed' AND completed_at IS NOT NULL
                        THEN EXTRACT(day FROM (completed_at - created_at))
                    END) as avg_completion_days
                FROM jobs
                WHERE customer_id = :customer_id
            """),
            {"customer_id": customer_id}
        ).fetchone()

        # Payment behavior
        payment_stats = db.execute(
            text("""
                SELECT
                    AVG(EXTRACT(day FROM (paid_at - created_at))) as avg_payment_days,
                    COUNT(CASE WHEN status = 'overdue' THEN 1 END) as overdue_count,
                    SUM(CASE WHEN status = 'overdue' THEN total_amount ELSE 0 END) as overdue_amount
                FROM invoices
                WHERE customer_id = :customer_id
            """),
            {"customer_id": customer_id}
        ).fetchone()

        analytics = {
            "customer_id": customer_id,
            "revenue_trend": [
                {
                    "month": row.month.isoformat() if row.month else None,
                    "job_count": row.job_count,
                    "revenue": float(row.revenue) if row.revenue else 0
                }
                for row in revenue_trend
            ],
            "completion_stats": dict(completion_stats._mapping) if completion_stats else {},
            "payment_stats": dict(payment_stats._mapping) if payment_stats else {},
            "customer_health_score": _calculate_health_score(completion_stats, payment_stats)
        }

        log_data_access(db, current_user["id"], "customers", "analytics", 1)
        return analytics

    except Exception as e:
        logger.error(f"Error fetching customer analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer analytics")

@router.get("/communications")
async def get_customer_communications(
    customer_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer communication history"""
    try:
        result = db.execute(
            text("""
                SELECT
                    id,
                    communication_type,
                    subject,
                    content,
                    direction,
                    status,
                    created_at,
                    created_by
                FROM customer_communications
                WHERE customer_id = :customer_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"customer_id": customer_id, "limit": limit}
        )

        communications = []
        for row in result:
            comm = dict(row._mapping)
            comm["id"] = str(comm["id"])
            comm["created_at"] = comm["created_at"].isoformat() if comm["created_at"] else None
            communications.append(comm)

        return {
            "customer_id": customer_id,
            "communications": communications,
            "total": len(communications)
        }

    except Exception as e:
        logger.error(f"Error fetching customer communications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch communications")

# Helper function
def _calculate_health_score(completion_stats, payment_stats) -> int:
    """Calculate customer health score (0-100)"""
    score = 50  # Base score

    if completion_stats:
        # Add points for high completion rate
        if completion_stats.total_jobs > 0:
            completion_rate = completion_stats.completed / completion_stats.total_jobs
            score += int(completion_rate * 20)

        # Deduct for cancellations
        if completion_stats.cancelled > 0:
            score -= completion_stats.cancelled * 5

    if payment_stats:
        # Deduct for overdue payments
        if payment_stats.overdue_count:
            score -= payment_stats.overdue_count * 10

        # Add points for quick payment
        if payment_stats.avg_payment_days and payment_stats.avg_payment_days < 30:
            score += 10

    return max(0, min(100, score))