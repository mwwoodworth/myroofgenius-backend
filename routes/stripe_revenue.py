"""
Complete Stripe Revenue Pipeline
Handles real money processing, subscriptions, and revenue tracking
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import stripe
import os
import json
import logging
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Text, Date, text
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import httpx

from database import SessionLocal, engine
from core.supabase_auth import get_current_user

router = APIRouter(tags=["Stripe Revenue"])
logger = logging.getLogger(__name__)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# SendGrid configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "no-reply@myroofgenius.com")

# Local Base
Base = declarative_base()

# ============================================================================
# MODELS
# ============================================================================

class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, unique=True, nullable=False)
    customer_email = Column(String, nullable=False)
    price_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    meta_data = Column("metadata", JSON, default={})
    tenant_id = Column(UUID(as_uuid=True), nullable=True) # Nullable for legacy/webhook handling if missing
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    customer_id = Column(String, nullable=False) # Stripe Customer ID
    customer_email = Column(String, nullable=False)
    price_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    trial_end = Column(DateTime, nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    meta_data = Column("metadata", JSON, default={})
    cancellation_reason = Column(String, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RevenueTracking(Base):
    __tablename__ = "revenue_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, default=datetime.utcnow().date)
    source = Column(String, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    customer_email = Column(String, nullable=True)
    stripe_payment_id = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure tables exist
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

# ============================================================================
# SCHEMAS
# ============================================================================

class CheckoutRequest(BaseModel):
    price_id: str
    customer_email: str
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, Any]] = {}

class SubscriptionRequest(BaseModel):
    customer_email: str
    price_id: str
    trial_days: Optional[int] = 14
    metadata: Optional[Dict[str, Any]] = {}

# ============================================================================
# HELPERS
# ============================================================================

async def send_email(to_email: str, subject: str, html_content: str):
    """Send email via SendGrid"""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid not configured; skipping email send to %s", to_email)
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": SENDGRID_FROM_EMAIL, "name": "MyRoofGenius"},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_content}]
                },
                timeout=10.0
            )
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

# ============================================================================
# ROUTES
# ============================================================================

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Create Stripe checkout session for one-time purchase
    """
    try:
        tenant_id = current_user.get("tenant_id")
        
        # Create or get customer
        customers = stripe.Customer.list(email=request.customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=request.customer_email,
                metadata={**request.metadata, "tenant_id": tenant_id}
            )
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                **request.metadata,
                "customer_email": request.customer_email,
                "tenant_id": tenant_id
            }
        )
        
        # Store in database
        new_session = CheckoutSession(
            session_id=session.id,
            customer_email=request.customer_email,
            price_id=request.price_id,
            status='pending',
            meta_data=request.metadata,
            tenant_id=uuid.UUID(tenant_id) if tenant_id else None
        )
        db.add(new_session)
        db.commit()
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-subscription")
async def create_subscription(
    request: SubscriptionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Create recurring subscription with trial period
    """
    try:
        tenant_id = current_user.get("tenant_id")

        # Create or get customer
        customers = stripe.Customer.list(email=request.customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=request.customer_email,
                metadata={**request.metadata, "tenant_id": tenant_id}
            )
        
        # Create subscription with trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': request.price_id}],
            trial_period_days=request.trial_days,
            metadata={
                **request.metadata,
                "customer_email": request.customer_email,
                "tenant_id": tenant_id
            },
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent']
        )
        
        # Store subscription
        new_sub = Subscription(
            stripe_subscription_id=subscription.id,
            customer_id=customer.id,
            customer_email=request.customer_email,
            price_id=request.price_id,
            status=subscription.status,
            trial_end=datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
            meta_data=request.metadata,
            tenant_id=uuid.UUID(tenant_id) if tenant_id else None
        )
        db.add(new_sub)
        db.commit()
        
        # Send welcome email
        background_tasks.add_task(
            send_email,
            request.customer_email,
            "Welcome to MyRoofGenius Pro!",
            f"""
            <h2>Welcome to MyRoofGenius!</h2>
            <p>Your {request.trial_days}-day free trial has started.</p>
            <p>You now have access to:</p>
            <ul>
                <li>Unlimited AI-powered estimates</li>
                <li>Photo analysis and measurements</li>
                <li>Competitor pricing analysis</li>
                <li>Customer management tools</li>
                <li>Priority support</li>
            </ul>
            <p>No credit card required during trial!</p>
            <a href="https://myroofgenius.com/dashboard">Go to Dashboard</a>
            """
        )
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "trial_end": subscription.trial_end,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Handle Stripe webhooks for payment events
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        tenant_id = metadata.get('tenant_id')

        # Update database
        db_session = db.query(CheckoutSession).filter(CheckoutSession.session_id == session.id).first()
        if db_session:
            db_session.status = 'completed'
            db_session.completed_at = datetime.utcnow()
            
            # Track revenue
            revenue = RevenueTracking(
                source='checkout',
                amount_cents=session.amount_total,
                customer_email=session.customer_email,
                stripe_payment_id=session.payment_intent,
                tenant_id=uuid.UUID(tenant_id) if tenant_id else db_session.tenant_id
            )
            db.add(revenue)
            db.commit()
        
        # Send confirmation email
        background_tasks.add_task(
            send_email,
            session.customer_email,
            "Payment Confirmed - MyRoofGenius",
            f"""
            <h2>Payment Received!</h2>
            <p>Thank you for your purchase of ${session.amount_total / 100:.2f}</p>
            <p>Your account has been activated.</p>
            <a href="https://myroofgenius.com/dashboard">Access Your Dashboard</a>
            """
        )
    
    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        
        # Update subscription status
        db_sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription.id).first()
        if db_sub:
            db_sub.status = subscription.status
            db_sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            db_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            db.commit()
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.subscription
        
        # Fetch subscription to get tenant_id if possible
        db_sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription_id).first()
        tenant_id = db_sub.tenant_id if db_sub else None

        # Track recurring revenue
        revenue = RevenueTracking(
            source='subscription',
            amount_cents=invoice.amount_paid,
            customer_email=invoice.customer_email,
            stripe_payment_id=invoice.payment_intent,
            subscription_id=subscription_id,
            tenant_id=tenant_id
        )
        db.add(revenue)
        db.commit()
    
    return {"received": True}

@router.get("/dashboard-metrics")
async def get_revenue_metrics(
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Real-time revenue dashboard metrics
    """
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Tenant assignment required")
        
        # Ensure UUID type consistency
        tenant_uuid = uuid.UUID(tenant_id)

        # Stripe revenue in prod is recorded in `subscriptions` (tenant-scoped).
        today_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(amount, 0)), 0)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                      AND last_payment_at::date = CURRENT_DATE
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        month_revenue = float(
            db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(COALESCE(amount, 0)), 0)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status IN ('active', 'trialing')
                      AND last_payment_at >= DATE_TRUNC('month', NOW())
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        active_subs = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM subscriptions
                    WHERE tenant_id = :tenant_id
                      AND COALESCE(is_test, FALSE) = FALSE
                      AND status = 'active'
                    """
                ),
                {"tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        # Conversion rate is tenant-scoped from our own checkout session tracking.
        cutoff = datetime.utcnow() - timedelta(days=30)
        total_sessions = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM checkout_sessions
                    WHERE created_at >= :cutoff
                      AND tenant_id = :tenant_id
                    """
                ),
                {"cutoff": cutoff, "tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )
        completed_sessions = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM checkout_sessions
                    WHERE created_at >= :cutoff
                      AND status = 'completed'
                      AND tenant_id = :tenant_id
                    """
                ),
                {"cutoff": cutoff, "tenant_id": tenant_uuid},
            ).scalar()
            or 0
        )

        conversion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0.0

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
            "today_revenue": round(today_revenue, 2),
            "month_revenue": round(month_revenue, 2),
            "active_subscriptions": active_subs,
            "conversion_rate": round(conversion_rate, 2),
            "mrr": round(mrr, 2),
            "mrr_source": "subscriptions",
            "targets": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(
    subscription_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Handle subscription cancellation with retention attempt
    """
    try:
        tenant_id = current_user.get("tenant_id")
        
        # Verify ownership
        db_sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id,
            Subscription.tenant_id == uuid.UUID(tenant_id) if tenant_id else None
        ).first()
        
        if not db_sub:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Offer discount before canceling (Simple logic: always offer if not applied)
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        if not subscription.discount:
            # Create 50% off coupon for retention
            coupon_id = f"retention_50off_3mo"
            try:
                stripe.Coupon.retrieve(coupon_id)
            except stripe.error.InvalidRequestError:
                stripe.Coupon.create(
                    percent_off=50,
                    duration='repeating',
                    duration_in_months=3,
                    id=coupon_id
                )
            
            # Apply to subscription
            stripe.Subscription.modify(
                subscription_id,
                coupon=coupon_id
            )
            
            return {
                "message": "We've applied 50% off for 3 months! Please reconsider.",
                "discount_applied": True,
                "new_price": subscription.items.data[0].price.unit_amount / 200  # 50% off
            }
        
        # If already discounted or user persists, cancel
        stripe.Subscription.delete(subscription_id)
        
        db_sub.status = 'canceled'
        db_sub.canceled_at = datetime.utcnow()
        db_sub.cancellation_reason = reason
        db.commit()
        
        return {"message": "Subscription canceled", "status": "canceled"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
