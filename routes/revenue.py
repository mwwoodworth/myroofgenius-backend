# Revenue API Routes
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime
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


def _safe_scalar(db: Session, query: str, params: Dict[str, Any], default: Any = 0) -> Any:
    try:
        value = db.execute(text(query), params).scalar()
        return value if value is not None else default
    except Exception:
        return default

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
        tenant_uuid = uuid.UUID(tenant_id)
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

        # Compute subscription KPIs directly from the canonical `subscriptions` table.
        # `revenue_metrics` is a global key/value table in prod and is not tenant-scoped.
        active_subscriptions = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        mrr = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN COALESCE(billing_cycle, 'monthly') ILIKE 'month%%' THEN COALESCE(amount, 0)
                        WHEN COALESCE(billing_cycle, '') ILIKE 'year%%'
                          OR COALESCE(billing_cycle, '') ILIKE 'ann%%'
                          THEN COALESCE(amount, 0) / 12.0
                        ELSE 0
                      END
                    ), 0)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )
        arr = round(mrr * 12, 2)

        canceled_30d = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND COALESCE(canceled_at, cancelled_at) >= NOW() - INTERVAL '30 days'
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )
        churn_rate = 0.0
        if active_subscriptions + canceled_30d > 0:
            churn_rate = round((canceled_30d / (active_subscriptions + canceled_30d)) * 100, 2)

        # These require attribution of spend + retention cohorts; keep nullable until implemented.
        ltv = None
        cac = None

        return {
            "mrr": round(mrr, 2),
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


@router.get("/pipeline")
def get_revenue_pipeline(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get high-level revenue pipeline metrics (lead -> customer conversion view)."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        total_leads = int(
            _safe_scalar(
                db,
                "SELECT COUNT(*) FROM leads WHERE tenant_id = :tenant_id",
                {"tenant_id": tenant_id},
                0,
            )
        )
        leads_30d = int(
            _safe_scalar(
                db,
                """
                SELECT COUNT(*)
                FROM leads
                WHERE tenant_id = :tenant_id
                  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """,
                {"tenant_id": tenant_id},
                0,
            )
        )
        new_customers_30d = int(
            _safe_scalar(
                db,
                """
                SELECT COUNT(*)
                FROM customers
                WHERE tenant_id = :tenant_id
                  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """,
                {"tenant_id": tenant_id},
                0,
            )
        )
        paid_revenue_30d = float(
            _safe_scalar(
                db,
                """
                SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                FROM invoices
                WHERE tenant_id = :tenant_id
                  AND (status = 'paid' OR payment_status = 'paid')
                  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """,
                {"tenant_id": tenant_id},
                0.0,
            )
        )

        conversion_rate_30d = 0.0
        if leads_30d > 0:
            conversion_rate_30d = round((new_customers_30d / leads_30d) * 100, 2)

        return {
            "tenant_id": tenant_id,
            "total_leads": total_leads,
            "leads_30d": leads_30d,
            "new_customers_30d": new_customers_30d,
            "conversion_rate_30d": conversion_rate_30d,
            "paid_revenue_30d": round(paid_revenue_30d, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Error getting revenue pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to load revenue pipeline")


@router.get("/status")
def get_revenue_status(
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Lightweight revenue subsystem status endpoint for operational checks."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        dashboard = get_revenue_dashboard(db=db, current_user=current_user)
        pipeline = get_revenue_pipeline(db=db, current_user=current_user)
        return {
            "status": "operational",
            "tenant_id": tenant_id,
            "dashboard": {
                "mrr": dashboard.get("mrr"),
                "arr": dashboard.get("arr"),
                "active_subscriptions": dashboard.get("active_subscriptions"),
                "total_revenue": dashboard.get("total_revenue"),
            },
            "pipeline": {
                "total_leads": pipeline.get("total_leads"),
                "leads_30d": pipeline.get("leads_30d"),
                "conversion_rate_30d": pipeline.get("conversion_rate_30d"),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error(f"Error getting revenue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to load revenue status")

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

        tenant_uuid = uuid.UUID(tenant_id)

        customers = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        mrr = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN COALESCE(billing_cycle, 'monthly') ILIKE 'month%%' THEN COALESCE(amount, 0)
                        WHEN COALESCE(billing_cycle, '') ILIKE 'year%%'
                          OR COALESCE(billing_cycle, '') ILIKE 'ann%%'
                          THEN COALESCE(amount, 0) / 12.0
                        ELSE 0
                      END
                    ), 0)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        return {
            "total_leads": total_leads,
            "leads_today": leads_today,
            "customers": customers,
            "mrr": round(mrr, 2),
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
        tenant_uuid = uuid.UUID(tenant_id)
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

        mrr = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(
                      CASE
                        WHEN COALESCE(billing_cycle, 'monthly') ILIKE 'month%%' THEN COALESCE(amount, 0)
                        WHEN COALESCE(billing_cycle, '') ILIKE 'year%%'
                          OR COALESCE(billing_cycle, '') ILIKE 'ann%%'
                          THEN COALESCE(amount, 0) / 12.0
                        ELSE 0
                      END
                    ), 0)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )
        arr = round(mrr * 12, 2)

        return {
            "revenue": {
                "current_month": current_month_value,
                "last_month": last_month_revenue,
                "growth_rate": round(growth_rate, 2),
                "transaction_count": current_revenue[1] if current_revenue else 0,
            },
            "subscriptions": {
                "mrr": round(mrr, 2),
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
