"""
Revenue Automation API Endpoints
Complete implementation for AI-powered revenue generation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import os
from core.supabase_auth import get_current_user

# Create database session - MUST use environment variable, no fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/api/v1/revenue",
    tags=["revenue"],
    dependencies=[Depends(get_current_user)],
)
logger = logging.getLogger(__name__)

def _is_schema_missing_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "does not exist" in message
        or "undefined table" in message
        or "relation" in message and "does not exist" in message
    )

# ============= Models =============

class RevenueMetrics(BaseModel):
    today: float
    month: float
    year: float
    mrr: float
    arr: float
    subscriptions: int
    conversionRate: float
    aov: float
    ltv: float
    churn: float
    growth: float
    projected: float

class Transaction(BaseModel):
    id: str
    customer: str
    amount: float
    type: str
    status: str
    date: datetime

class ExperimentAssignment(BaseModel):
    visitor_id: str
    experiment_name: str
    variant_id: str

class ConversionEvent(BaseModel):
    visitor_id: str
    experiment_name: Optional[str]
    variant_id: Optional[str]
    conversion_type: str
    conversion_value: Optional[float]

class OptimizationEvent(BaseModel):
    visitor_id: str
    event_type: str
    event_data: Dict[str, Any]

class EmailSchedule(BaseModel):
    user_id: Optional[str]
    email: str
    sequence_type: str
    template: str
    subject: str
    scheduled_for: datetime
    personalization_data: Dict[str, Any]

class AIRecommendation(BaseModel):
    title: str
    description: str
    impact_score: float
    confidence_score: float
    estimated_revenue_impact: float
    auto_implement: bool = False

# ============= Revenue Metrics =============

@router.get("/metrics", response_model=RevenueMetrics)
async def get_revenue_metrics(db: Session = Depends(get_db)):
    """Get real-time revenue metrics"""
    try:
        payments_row = db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN status = 'completed' AND DATE(created_at) = CURRENT_DATE THEN amount ELSE 0 END), 0) as today,
                COALESCE(SUM(CASE WHEN status = 'completed' AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) THEN amount ELSE 0 END), 0) as month,
                COALESCE(SUM(CASE WHEN status = 'completed' AND DATE_TRUNC('year', created_at) = DATE_TRUNC('year', CURRENT_DATE) THEN amount ELSE 0 END), 0) as year,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_revenue,
                COUNT(*) FILTER (WHERE status = 'completed' AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)) as month_count,
                COUNT(DISTINCT CASE WHEN status = 'completed' THEN customer_id END) as unique_customers
            FROM payments
        """)).first()

        if not payments_row:
            raise HTTPException(status_code=500, detail="Payments query returned no rows.")

        prev_month_row = db.execute(text("""
            SELECT
                COALESCE(SUM(amount), 0) as prev_month
            FROM payments
            WHERE status = 'completed'
              AND created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
              AND created_at < DATE_TRUNC('month', CURRENT_DATE)
        """)).first()

        subs_row = db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status IN ('cancelled', 'expired')) as cancelled_total,
                COUNT(*) FILTER (WHERE cancelled_at >= CURRENT_DATE - INTERVAL '30 days') as cancelled_recent,
                COALESCE(SUM(
                    CASE
                        WHEN status = 'active' THEN
                            CASE
                                WHEN billing_cycle = 'yearly' THEN amount / 12
                                ELSE amount
                            END
                        ELSE 0
                    END
                ), 0) as mrr
            FROM subscriptions
        """)).first()

        leads_row = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'converted' OR converted_at IS NOT NULL) as converted
            FROM leads
        """)).first()

        today_revenue = float(payments_row.today or 0)
        month_revenue = float(payments_row.month or 0)
        year_revenue = float(payments_row.year or 0)
        total_revenue = float(payments_row.total_revenue or 0)
        month_count = int(payments_row.month_count or 0)
        unique_customers = int(payments_row.unique_customers or 0)

        active_subs = int(subs_row.active or 0) if subs_row else 0
        cancelled_total = int(subs_row.cancelled_total or 0) if subs_row else 0
        cancelled_recent = int(subs_row.cancelled_recent or 0) if subs_row else 0
        mrr = float(subs_row.mrr or 0) if subs_row else 0.0
        arr = mrr * 12

        total_leads = int(leads_row.total or 0) if leads_row else 0
        converted_leads = int(leads_row.converted or 0) if leads_row else 0
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0

        aov = (month_revenue / month_count) if month_count > 0 else 0.0
        ltv = (total_revenue / unique_customers) if unique_customers > 0 else 0.0

        total_subs = active_subs + cancelled_total
        churn_rate = (cancelled_recent / total_subs * 100) if total_subs > 0 else 0.0

        prev_month_revenue = float(prev_month_row.prev_month or 0) if prev_month_row else 0.0
        if prev_month_revenue > 0:
            growth_rate = ((month_revenue - prev_month_revenue) / prev_month_revenue) * 100
        else:
            if month_revenue > 0:
                logger.warning("Previous month revenue is zero; growth rate set to 0.")
            growth_rate = 0.0

        projected_annual = year_revenue * (1 + growth_rate / 100)

        return RevenueMetrics(
            today=today_revenue,
            month=month_revenue,
            year=year_revenue,
            mrr=mrr,
            arr=arr,
            subscriptions=active_subs,
            conversionRate=conversion_rate,
            aov=aov,
            ltv=ltv,
            churn=churn_rate,
            growth=growth_rate,
            projected=projected_annual
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to get revenue metrics: {e}")
        if _is_schema_missing_error(e):
            raise HTTPException(status_code=503, detail="Required revenue tables are missing.")
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics.")
    except Exception as e:
        logger.error(f"Failed to get revenue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics.")

@router.get("/transactions")
async def get_recent_transactions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent transactions"""
    try:
        # Try to get real transactions - parameterized query to prevent SQL injection
        result = db.execute(text("""
            SELECT
                id,
                customer_name as customer,
                amount,
                description as type,
                status,
                created_at as date
            FROM payments
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        
        if result:
            transactions = [
                Transaction(
                    id=str(row.id),
                    customer=row.customer,
                    amount=float(row.amount),
                    type=row.type,
                    status=row.status,
                    date=row.date
                )
                for row in result
            ]
            return {"transactions": transactions}
        logger.info("No transactions found for recent transactions query.")
        # No transactions found - return empty list
        return {"transactions": []}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transactions: {str(e)}")

# ============= A/B Testing & Optimization =============

@router.post("/experiments/assign")
async def assign_experiment(
    assignment: ExperimentAssignment,
    db: Session = Depends(get_db)
):
    """Assign visitor to A/B test variant"""
    try:
        # Store assignment in database
        db.execute("""
            INSERT INTO experiment_assignments (visitor_id, experiment_name, variant_id, assigned_at)
            VALUES (:visitor_id, :experiment_name, :variant_id, NOW())
            ON CONFLICT (visitor_id, experiment_name) DO UPDATE
            SET variant_id = :variant_id, assigned_at = NOW()
        """, {
            "visitor_id": assignment.visitor_id,
            "experiment_name": assignment.experiment_name,
            "variant_id": assignment.variant_id
        })
        db.commit()
        
        return {"success": True, "variant": assignment.variant_id}
    except Exception as e:
        logger.error("Failed to assign experiment: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to assign experiment")

@router.post("/conversions/track")
async def track_conversion(
    event: ConversionEvent,
    db: Session = Depends(get_db)
):
    """Track conversion event"""
    try:
        # Store conversion in database
        db.execute("""
            INSERT INTO conversions (
                visitor_id, experiment_name, variant_id, 
                conversion_type, conversion_value, converted_at
            )
            VALUES (
                :visitor_id, :experiment_name, :variant_id,
                :conversion_type, :conversion_value, NOW()
            )
        """, {
            "visitor_id": event.visitor_id,
            "experiment_name": event.experiment_name,
            "variant_id": event.variant_id,
            "conversion_type": event.conversion_type,
            "conversion_value": event.conversion_value
        })
        db.commit()
        
        return {"success": True, "message": "Conversion tracked"}
    except Exception as e:
        logger.error("Failed to track conversion: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to track conversion")

@router.post("/optimization/track")
async def track_optimization_event(
    event: OptimizationEvent,
    db: Session = Depends(get_db)
):
    """Track visitor behavior for optimization"""
    try:
        # Store event in database
        db.execute("""
            INSERT INTO optimization_events (visitor_id, event_type, event_data, created_at)
            VALUES (:visitor_id, :event_type, :event_data::jsonb, NOW())
        """, {
            "visitor_id": event.visitor_id,
            "event_type": event.event_type,
            "event_data": json.dumps(event.event_data)
        })
        db.commit()
        
        return {"success": True, "message": "Event tracked"}
    except Exception as e:
        logger.error("Failed to track optimization event: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to track optimization event")

# ============= Email Automation =============

@router.post("/emails/schedule")
async def schedule_email(
    email: EmailSchedule,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Schedule an automated email"""
    try:
        # Store in database
        result = db.execute("""
            INSERT INTO scheduled_emails (
                user_id, email, sequence_type, template, subject,
                scheduled_for, personalization_data, status
            )
            VALUES (
                :user_id, :email, :sequence_type, :template, :subject,
                :scheduled_for, :personalization_data::jsonb, 'pending'
            )
            RETURNING id
        """, {
            "user_id": email.user_id,
            "email": email.email,
            "sequence_type": email.sequence_type,
            "template": email.template,
            "subject": email.subject,
            "scheduled_for": email.scheduled_for,
            "personalization_data": json.dumps(email.personalization_data)
        })
        db.commit()
        
        email_id = result.fetchone()[0]
        
        # Schedule background task to send email
        background_tasks.add_task(send_email_when_due, email_id, email.scheduled_for)
        
        return {"success": True, "email_id": str(email_id)}
    except Exception as e:
        logger.error("Failed to schedule email: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to schedule email")

async def send_email_when_due(email_id: str, scheduled_for: datetime):
    """Background task to send email at scheduled time"""
    from services.notifications import send_email_message
    from main import SessionLocal

    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, email, subject, template, personalization_data
            FROM scheduled_emails
            WHERE id = :email_id
        """), {"email_id": email_id}).fetchone()

        if not result:
            logger.error("Scheduled email not found: %s", email_id)
            return

        if datetime.utcnow() < scheduled_for:
            logger.info("Scheduled email %s not due yet.", email_id)
            return

        template_result = db.execute(text("""
            SELECT subject, html_body, text_body
            FROM email_templates
            WHERE template_key = :template_key AND is_active = true
            LIMIT 1
        """), {"template_key": result.template}).fetchone()

        if not template_result:
            logger.error("Email template not found or inactive: %s", result.template)
            db.execute(text("""
                UPDATE scheduled_emails
                SET status = 'failed', error = :error, updated_at = NOW()
                WHERE id = :email_id
            """), {"email_id": email_id, "error": "Template not found or inactive"})
            db.commit()
            return

        personalization = json.loads(result.personalization_data or "{}")
        subject = _render_template(template_result.subject or result.subject, personalization)
        html_body = _render_template(template_result.html_body or "", personalization)
        text_body = _render_template(template_result.text_body or "", personalization)

        if not html_body and not text_body:
            raise RuntimeError("Email template missing body content")

        success = send_email_message(result.email, subject, html_body, text_body)
        status = "sent" if success else "failed"
        error = None if success else "Email delivery failed"

        db.execute(text("""
            UPDATE scheduled_emails
            SET status = :status, error = :error, sent_at = NOW(), updated_at = NOW()
            WHERE id = :email_id
        """), {"email_id": email_id, "status": status, "error": error})
        db.commit()
    except Exception as e:
        logger.error("Failed to send scheduled email %s: %s", email_id, e)
        db.rollback()
    finally:
        db.close()

@router.get("/emails/pending")
async def get_pending_emails(db: Session = Depends(get_db)):
    """Get pending scheduled emails"""
    try:
        result = db.execute("""
            SELECT * FROM scheduled_emails
            WHERE status = 'pending' AND scheduled_for <= NOW() + INTERVAL '1 hour'
            ORDER BY scheduled_for
            LIMIT 50
        """).fetchall()
        
        return {"emails": [dict(row) for row in result]}
    except Exception as e:
        logger.error("Failed to fetch pending emails: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch pending emails")

# ============= AI Recommendations =============

@router.get("/ai/recommendations")
async def get_ai_recommendations(db: Session = Depends(get_db)):
    """Get AI-generated optimization recommendations"""
    raise HTTPException(
        status_code=501,
        detail="AI recommendations are not implemented. Configure a real recommendation engine.",
    )

@router.post("/ai/recommendations/{id}/implement")
async def implement_recommendation(
    id: str,
    db: Session = Depends(get_db)
):
    """Implement an AI recommendation"""
    raise HTTPException(
        status_code=501,
        detail="Recommendation execution is not implemented. Implement workflow orchestration before use.",
    )

# ============= Dashboard Data =============

@router.get("/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get comprehensive dashboard data"""
    raise HTTPException(
        status_code=501,
        detail="Dashboard summary is not implemented. Build real funnel metrics before use.",
    )

# ============= Testing Endpoint =============

@router.get("/test")
async def test_revenue_system():
    """Test that revenue automation system is working"""
    raise HTTPException(
        status_code=501,
        detail="Use /api/v1/revenue/metrics for runtime checks. This endpoint is not implemented.",
    )


def _render_template(template: str, data: Dict[str, Any]) -> str:
    """Render simple {{key}} templates with provided data."""
    if not template:
        return ""
    rendered = template
    for key, value in data.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered
