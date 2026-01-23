# Revenue API Routes
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["revenue"])

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LeadCapture(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = "direct"

@router.post("/capture-lead")
def capture_lead(
    lead: LeadCapture,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Capture a new lead"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO leads (email, name, source, tenant_id)
                VALUES (:email, :name, :source, :tenant_id)
                ON CONFLICT (email, tenant_id) DO UPDATE
                SET updated_at = NOW()
                RETURNING id
                """
            ),
            {
                "email": lead.email,
                "name": lead.name,
                "source": lead.source,
                "tenant_id": tenant_id,
            },
        )
        db.commit()
        lead_id = result.scalar()
        return {"success": True, "lead_id": str(lead_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
def get_revenue_dashboard(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get revenue dashboard data"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        customers_total = db.execute(
            text("SELECT COUNT(*) FROM customers WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        ).scalar() or 0
        new_customers = (
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM customers
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )

        paid_invoices = (
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM invoices
                    WHERE (status = 'paid' OR payment_status = 'paid')
                    AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )
        total_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                    FROM invoices
                    WHERE (status = 'paid' OR payment_status = 'paid')
                    AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )

        last_month_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                    FROM invoices
                    WHERE (status = 'paid' OR payment_status = 'paid')
                      AND created_at >= CURRENT_DATE - INTERVAL '60 days'
                      AND created_at < CURRENT_DATE - INTERVAL '30 days'
                      AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )

        current_month_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                    FROM invoices
                    WHERE (status = 'paid' OR payment_status = 'paid')
                      AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                      AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )

        growth_rate = 0.0
        if last_month_revenue > 0:
            growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100

        # Prefer precomputed metrics if present.
        revenue_metrics = None
        try:
            revenue_metrics = db.execute(
                text(
                    """
                    SELECT mrr, arr, churn_rate, ltv, cac
                    FROM revenue_metrics
                    WHERE tenant_id = :tenant_id
                    ORDER BY metric_date DESC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id}
            ).first()
        except Exception:
            revenue_metrics = None

        # Subscription metrics are schema-dependent; compute what we can without hardcoded plan pricing.
        active_subscriptions = None
        try:
            active_subscriptions = db.execute(
                text("SELECT COUNT(*) FROM subscriptions WHERE status = 'active' AND tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            ).scalar()
        except Exception:
            active_subscriptions = None

        mrr = float(revenue_metrics.mrr) if revenue_metrics and revenue_metrics.mrr is not None else None
        arr = float(revenue_metrics.arr) if revenue_metrics and revenue_metrics.arr is not None else None
        churn_rate = (
            float(revenue_metrics.churn_rate)
            if revenue_metrics and revenue_metrics.churn_rate is not None
            else None
        )
        ltv = float(revenue_metrics.ltv) if revenue_metrics and revenue_metrics.ltv is not None else None
        cac = float(revenue_metrics.cac) if revenue_metrics and revenue_metrics.cac is not None else None

        return {
            "mrr": mrr,
            "arr": arr,
            "customers": customers_total,
            "new_customers": new_customers,
            "active_subscriptions": active_subscriptions,
            "total_revenue": total_revenue,
            "paid_invoices": paid_invoices,
            "growth": round(growth_rate, 2),
            "churn_rate": churn_rate,
            "ltv": ltv,
            "cac": cac,
        }
    except Exception as e:
        logger.error(f"Error getting revenue dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load revenue dashboard")

@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get revenue metrics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        total_leads = db.execute(
            text("SELECT COUNT(*) FROM leads WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        ).scalar() or 0
        leads_today = (
            db.execute(
                text("SELECT COUNT(*) FROM leads WHERE created_at >= CURRENT_DATE AND tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            ).scalar() or 0
        )

        customers = None
        try:
            customers = (
                db.execute(
                    text("SELECT COUNT(*) FROM subscriptions WHERE status = 'active' AND tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar()
                or 0
            )
        except Exception:
            customers = None

        mrr = None
        try:
            mrr_row = db.execute(
                text(
                    """
                    SELECT mrr
                    FROM revenue_metrics
                    WHERE tenant_id = :tenant_id
                    ORDER BY metric_date DESC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id}
            ).first()
            if mrr_row and mrr_row.mrr is not None:
                mrr = float(mrr_row.mrr)
        except Exception:
            mrr = None

        return {
            "total_leads": total_leads,
            "leads_today": leads_today,
            "customers": customers,
            "mrr": mrr,
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_revenue_stats(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get comprehensive revenue statistics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        current_revenue = db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(COALESCE(total_amount, 0)), 0) as revenue,
                    COUNT(*) as transaction_count
                FROM invoices
                WHERE (status = 'paid' OR payment_status = 'paid')
                AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                AND tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id}
        ).first()

        last_month_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0) as revenue
                    FROM invoices
                    WHERE (status = 'paid' OR payment_status = 'paid')
                    AND created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                    AND created_at < DATE_TRUNC('month', CURRENT_DATE)
                    AND tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id}
            ).scalar()
            or 0
        )

        customer_stats = db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_customers,
                    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as customers_this_week
                FROM customers
                WHERE tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id}
        ).first()

        job_stats = db.execute(
            text(
                """
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_jobs
                FROM jobs
                WHERE tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id}
        ).first()

        growth_rate = 0.0
        current_month_value = float(current_revenue[0]) if current_revenue else 0.0
        if last_month_revenue > 0:
            growth_rate = ((current_month_value - last_month_revenue) / last_month_revenue) * 100

        revenue_metrics = None
        try:
            revenue_metrics = db.execute(
                text(
                    """
                    SELECT mrr, arr
                    FROM revenue_metrics
                    WHERE tenant_id = :tenant_id
                    ORDER BY metric_date DESC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_id}
            ).first()
        except Exception:
            revenue_metrics = None

        mrr = float(revenue_metrics.mrr) if revenue_metrics and revenue_metrics.mrr is not None else None
        arr = float(revenue_metrics.arr) if revenue_metrics and revenue_metrics.arr is not None else None

        return {
            "revenue": {
                "current_month": current_month_value,
                "last_month": last_month_revenue,
                "growth_rate": round(growth_rate, 2),
                "transaction_count": current_revenue[1] if current_revenue else 0,
            },
            "subscriptions": {
                "mrr": mrr,
                "arr": arr,
            },
            "customers": {
                "total": customer_stats[0] if customer_stats else 0,
                "new_30d": customer_stats[1] if customer_stats else 0,
                "new_7d": customer_stats[2] if customer_stats else 0,
            },
            "jobs": {
                "total": job_stats[0] if job_stats else 0,
                "completed": job_stats[1] if job_stats else 0,
                "active": job_stats[2] if job_stats else 0,
            },
        }
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to load revenue stats")

# Add to main.py:
# app.include_router(router)
