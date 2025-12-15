# Revenue API Routes
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
import sys

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# Import database session
try:
    from main import SessionLocal
except ImportError:
    # Fallback to creating our own session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(tags=["revenue"])

class LeadCapture(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = "direct"

@router.post("/capture-lead")
async def capture_lead(lead: LeadCapture):
    """Capture a new lead"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("""
                INSERT INTO leads (email, name, source)
                VALUES (:email, :name, :source)
                ON CONFLICT (email) DO UPDATE
                SET updated_at = NOW()
                RETURNING id
            """), {
                "email": lead.email,
                "name": lead.name,
                "source": lead.source
            })
            db.commit()
            lead_id = result.scalar()
            return {"success": True, "lead_id": str(lead_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_revenue_dashboard():
    """Get revenue dashboard data"""
    try:
        with SessionLocal() as db:
            # Get revenue metrics
            metrics = db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM customers) as total_customers,
                    (SELECT COUNT(*) FROM customers WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as new_customers,
                    (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,
                    (SELECT COALESCE(SUM(amount), 0) FROM subscriptions WHERE status = 'active') as mrr,
                    (SELECT COUNT(*) FROM invoices WHERE status = 'paid' OR payment_status = 'paid') as paid_invoices,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status = 'paid' OR payment_status = 'paid') as total_revenue
            """)).first()
            
            # Calculate ARR and growth
            mrr = float(metrics[3] or 0)
            arr = mrr * 12
            
            # Get growth rate (simplified - compare to last month)
            last_month_revenue = db.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM invoices
                WHERE (status = 'paid' OR payment_status = 'paid')
                AND created_at >= CURRENT_DATE - INTERVAL '60 days'
                AND created_at < CURRENT_DATE - INTERVAL '30 days'
            """)).scalar() or 0

            current_month_revenue = db.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM invoices
                WHERE (status = 'paid' OR payment_status = 'paid')
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)).scalar() or 0
            
            growth_rate = 0
            if last_month_revenue > 0:
                growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
            
            return {
                "mrr": mrr,
                "arr": arr,
                "customers": metrics[0] or 0,
                "new_customers": metrics[1] or 0,
                "active_subscriptions": metrics[2] or 0,
                "total_revenue": float(metrics[5] or 0),
                "paid_invoices": metrics[4] or 0,
                "growth": round(growth_rate, 2),
                "churn_rate": 2.5,  # Placeholder
                "ltv": mrr * 24 if mrr > 0 else 0,  # 24 month LTV estimate
                "cac": 150,  # Placeholder
                "revenue_by_product": {
                    "Professional": mrr * 0.4,
                    "Business": mrr * 0.35,
                    "Enterprise": mrr * 0.25
                }
            }
    except Exception as e:
        logger.error(f"Error getting revenue dashboard: {e}")
        # Return placeholder data on error
        return {
            "mrr": 0,
            "arr": 0,
            "customers": 0,
            "new_customers": 0,
            "active_subscriptions": 0,
            "total_revenue": 0,
            "paid_invoices": 0,
            "growth": 0,
            "churn_rate": 0,
            "ltv": 0,
            "cac": 0,
            "revenue_by_product": {}
        }

@router.get("/metrics")
async def get_metrics():
    """Get revenue metrics"""
    try:
        with SessionLocal() as db:
            metrics = db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM leads) as total_leads,
                    (SELECT COUNT(*) FROM leads WHERE created_at >= CURRENT_DATE) as leads_today,
                    (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as customers,
                    (SELECT COALESCE(SUM(amount), 0) FROM subscriptions WHERE status = 'active') as mrr
            """)).first()

            return {
                "total_leads": metrics[0] or 0,
                "leads_today": metrics[1] or 0,
                "customers": metrics[2] or 0,
                "mrr": float(metrics[3] or 0)
            }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_revenue_stats():
    """Get comprehensive revenue statistics"""
    try:
        with SessionLocal() as db:
            # Get current month revenue
            current_revenue = db.execute(text("""
                SELECT
                    COALESCE(SUM(total_amount), 0) as revenue,
                    COUNT(*) as transaction_count
                FROM invoices
                WHERE (status = 'paid' OR payment_status = 'paid')
                AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """)).first()

            # Get last month revenue for comparison
            last_month_revenue = db.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0) as revenue
                FROM invoices
                WHERE (status = 'paid' OR payment_status = 'paid')
                AND created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                AND created_at < DATE_TRUNC('month', CURRENT_DATE)
            """)).scalar() or 0

            # Get subscription metrics
            subscription_stats = db.execute(text("""
                SELECT
                    COUNT(*) as active_subscriptions,
                    COALESCE(SUM(amount), 0) as mrr,
                    COALESCE(AVG(amount), 0) as avg_subscription_value
                FROM subscriptions
                WHERE status = 'active'
            """)).first()

            # Get customer stats
            customer_stats = db.execute(text("""
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_customers,
                    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as customers_this_week
                FROM customers
            """)).first()

            # Get job stats
            job_stats = db.execute(text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_jobs,
                    COALESCE(AVG(CASE WHEN status = 'completed' THEN total_cost END), 0) as avg_job_value
                FROM jobs
            """)).first()

            # Calculate growth rate
            growth_rate = 0
            if last_month_revenue > 0:
                growth_rate = ((float(current_revenue[0]) - float(last_month_revenue)) / float(last_month_revenue)) * 100

            # Calculate ARR and other metrics
            mrr = float(subscription_stats[1]) if subscription_stats else 0
            arr = mrr * 12

            return {
                "revenue": {
                    "current_month": float(current_revenue[0]) if current_revenue else 0,
                    "last_month": float(last_month_revenue),
                    "growth_rate": round(growth_rate, 2),
                    "transaction_count": current_revenue[1] if current_revenue else 0
                },
                "subscriptions": {
                    "active": subscription_stats[0] if subscription_stats else 0,
                    "mrr": mrr,
                    "arr": arr,
                    "avg_value": float(subscription_stats[2]) if subscription_stats else 0
                },
                "customers": {
                    "total": customer_stats[0] if customer_stats else 0,
                    "new_30d": customer_stats[1] if customer_stats else 0,
                    "new_7d": customer_stats[2] if customer_stats else 0
                },
                "jobs": {
                    "total": job_stats[0] if job_stats else 0,
                    "completed": job_stats[1] if job_stats else 0,
                    "active": job_stats[2] if job_stats else 0,
                    "avg_value": float(job_stats[3]) if job_stats else 0
                },
                "summary": {
                    "total_revenue": float(current_revenue[0]) if current_revenue else 0,
                    "mrr": mrr,
                    "arr": arr,
                    "customer_count": customer_stats[0] if customer_stats else 0,
                    "growth_percentage": round(growth_rate, 2)
                }
            }
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}")
        # Return structured error response
        return {
            "revenue": {"current_month": 0, "last_month": 0, "growth_rate": 0, "transaction_count": 0},
            "subscriptions": {"active": 0, "mrr": 0, "arr": 0, "avg_value": 0},
            "customers": {"total": 0, "new_30d": 0, "new_7d": 0},
            "jobs": {"total": 0, "completed": 0, "active": 0, "avg_value": 0},
            "summary": {"total_revenue": 0, "mrr": 0, "arr": 0, "customer_count": 0, "growth_percentage": 0},
            "error": str(e)
        }

# Add to main.py:
# app.include_router(router)
