"""
Enhanced Stripe Automation Routes with Error Handling
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import stripe
import os
import json
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
import logging

router = APIRouter(
    tags=["Stripe Automation"]
)

logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def _get_db_engine():
    from database import engine as db_engine

    if db_engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db_engine

@router.get("/health")
async def stripe_health():
    """Stripe automation health check"""
    return {
        "status": "configured" if STRIPE_SECRET_KEY else "not_configured",
        "stripe_configured": bool(STRIPE_SECRET_KEY),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/config")
async def get_stripe_config():
    """Get Stripe configuration for frontend"""
    # Primary key - try STRIPE_PUBLISHABLE_KEY first
    publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
    # Valid Stripe publishable keys are 100+ chars - placeholder values are short
    # If it's invalid/placeholder, use NEXT_PUBLIC_ version from env group
    if not publishable_key or len(publishable_key) < 50 or "placeholder" in publishable_key.lower():
        publishable_key = os.getenv("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY")
    logger.info(f"Stripe publishable_key resolved: {publishable_key[:20] if publishable_key else 'None'}...")
    return {
        "publishable_key": publishable_key,
        "currency": "usd",
        "country": "US",
        "payment_methods": ["card"],
        "status": "active" if STRIPE_SECRET_KEY else "not_configured",
    }

@router.get("/analytics/revenue")
async def get_revenue_analytics():
    """Get revenue analytics with error handling"""
    try:
        engine = _get_db_engine()
        with engine.connect() as conn:
            # Try to get real data
            result = conn.execute(text("""
                SELECT 
                    COALESCE(SUM(mrr), 0) as mrr,
                    COALESCE(SUM(arr), 0) as arr,
                    COALESCE(SUM(total_revenue), 0) as total_revenue
                FROM stripe_revenue_metrics
                WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
            """))
            row = result.fetchone()
            
            if row and row.mrr:
                return {
                    "mrr": row.mrr / 100,  # Convert from cents
                    "arr": row.arr / 100,
                    "total_revenue": row.total_revenue / 100,
                    "period": "last_30_days",
                    "available": True,
                }
    except (ProgrammingError, Exception) as e:
        logger.warning("Stripe revenue analytics unavailable: %s", e)

    return {"mrr": None, "arr": None, "total_revenue": None, "period": "last_30_days", "available": False}

@router.get("/analytics/subscriptions")
async def get_subscription_analytics():
    """Get subscription analytics with error handling"""
    try:
        engine = _get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    subscription_tier,
                    active_count,
                    mrr,
                    churn_rate
                FROM stripe_subscription_analytics
                ORDER BY mrr DESC
            """))
            
            subscriptions = []
            for row in result:
                subscriptions.append({
                    "tier": row.subscription_tier,
                    "active_count": row.active_count,
                    "mrr": row.mrr / 100 if row.mrr else 0,
                    "churn_rate": float(row.churn_rate) if row.churn_rate else 0
                })
            
            if subscriptions:
                return {"subscriptions": subscriptions, "available": True}
    except (ProgrammingError, Exception) as e:
        logger.warning("Stripe subscription analytics unavailable: %s", e)

    return {"subscriptions": [], "available": False}

@router.get("/automation/rules")
async def get_automation_rules():
    """Get automation rules with error handling"""
    try:
        engine = _get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id, name, trigger_type, is_active, execution_count
                FROM automation_rules
                WHERE is_active = true
                ORDER BY execution_count DESC
                LIMIT 20
            """))
            
            rules = []
            for row in result:
                rules.append({
                    "id": str(row.id),
                    "name": row.name,
                    "trigger_type": row.trigger_type,
                    "is_active": row.is_active,
                    "execution_count": row.execution_count or 0
                })
            
            if rules:
                return {"rules": rules, "total": len(rules), "available": True}
    except (ProgrammingError, Exception) as e:
        logger.warning("Automation rules unavailable: %s", e)

    return {"rules": [], "total": 0, "available": False}

# Try primary webhook secret, fallback to alternative name if placeholder
_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
if not _webhook_secret or len(_webhook_secret) < 30 or "placeholder" in _webhook_secret.lower():
    _webhook_secret = os.getenv("BRAINOPS_STRIPE_WEBHOOK_SECRET")
STRIPE_WEBHOOK_SECRET = _webhook_secret

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks with signature verification"""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        # CRITICAL: Verify webhook signature to prevent forged requests
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("CRITICAL: STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")

        if not sig_header:
            logger.warning("Webhook received without signature header")
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Log the event
        logger.info(f"Stripe webhook verified and received: {event.type}")

        # Process different event types
        if event.type == "payment_intent.succeeded":
            logger.info("Payment succeeded")
        elif event.type == "customer.subscription.created":
            logger.info("New subscription created")
        elif event.type == "customer.subscription.updated":
            logger.info("Subscription updated")
        elif event.type == "customer.subscription.deleted":
            logger.info("Subscription cancelled")
        elif event.type == "invoice.paid":
            logger.info("Invoice paid")
        elif event.type == "invoice.payment_failed":
            logger.warning("Invoice payment failed")

        return {"success": True, "event_id": event.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Webhook error", exc_info=e)
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# Customer endpoints
@router.post("/customers/create")
async def create_customer(email: str, name: Optional[str] = None):
    """Create a Stripe customer"""
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return {"customer_id": customer.id, "email": email}
    except Exception as e:
        logger.exception("Stripe customer creation failed", exc_info=e)
        raise HTTPException(status_code=400, detail="Customer creation failed")

# Additional endpoints for completeness
@router.post("/checkout/create")
async def create_checkout_session(price: int, success_url: str, cancel_url: str):
    """Create a checkout session"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Service"},
                    "unit_amount": price
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        logger.exception("Checkout session creation failed", exc_info=e)
        raise HTTPException(status_code=400, detail="Checkout session creation failed")
