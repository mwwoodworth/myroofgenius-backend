"""
Stripe Checkout Integration for MyRoofGenius
Handles subscription creation and payment processing
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import stripe
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Optional price IDs for frontend discovery (no hardcoded fallbacks)
PRICE_IDS = {
    "starter_monthly": os.getenv("STRIPE_PRICE_STARTER_MONTHLY"),
    "starter_annual": os.getenv("STRIPE_PRICE_STARTER_ANNUAL"),
    "professional_monthly": os.getenv("STRIPE_PRICE_PROFESSIONAL_MONTHLY"),
    "professional_annual": os.getenv("STRIPE_PRICE_PROFESSIONAL_ANNUAL"),
    "enterprise_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY"),
    "enterprise_annual": os.getenv("STRIPE_PRICE_ENTERPRISE_ANNUAL"),
}

class CheckoutRequest(BaseModel):
    price_id: str
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class SubscriptionRequest(BaseModel):
    customer_id: str
    price_id: str

@router.post("/checkout/create")
async def create_checkout_session(request: CheckoutRequest):
    """Create a Stripe checkout session for subscription"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail="Stripe is not configured")

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        success_url = os.getenv(
            "STRIPE_SUCCESS_URL",
            f"{frontend_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
        )
        cancel_url = os.getenv("STRIPE_CANCEL_URL", f"{frontend_url}/pricing")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": request.price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.customer_email,
            metadata=request.metadata or {},
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "price_id": request.price_id,
            "metadata": request.metadata or {},
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Dict[str, Any]):
    """Handle Stripe webhook events"""
    try:
        event_type = request.get('type', '')

        if event_type == 'checkout.session.completed':
            # Handle successful checkout
            session = request.get('data', {}).get('object', {})
            customer_email = session.get('customer_email')
            subscription_id = session.get('subscription')

            
            logger.info(f"New subscription: {subscription_id} for {customer_email}")

        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription = request.get('data', {}).get('object', {})
            logger.info(f"Subscription cancelled: {subscription.get('id')}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        # Return 200 to prevent Stripe retries on error
        return {"status": "error", "message": str(e)}

@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price_monthly": 49,
                "price_annual": 39,
                "stripe_price_ids": {
                    "monthly": PRICE_IDS.get("starter_monthly"),
                    "annual": PRICE_IDS.get("starter_annual"),
                },
                "features": [
                    "25 AI roof analyses per month",
                    "Instant cost estimates",
                    "Professional reports",
                    "Material calculator",
                    "Weather assessments",
                    "Mobile app",
                    "Basic CRM (50 customers)",
                    "Email support"
                ]
            },
            {
                "id": "professional",
                "name": "Professional",
                "price_monthly": 99,
                "price_annual": 79,
                "popular": True,
                "stripe_price_ids": {
                    "monthly": PRICE_IDS.get("professional_monthly"),
                    "annual": PRICE_IDS.get("professional_annual"),
                },
                "features": [
                    "UNLIMITED AI roof analyses",
                    "Advanced damage detection",
                    "Instant quotes & invoicing",
                    "Full CRM with automation",
                    "Team collaboration (5 users)",
                    "Customer portal",
                    "Marketing automation",
                    "Priority support",
                    "Custom branded reports",
                    "Payment processing"
                ]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_monthly": 199,
                "price_annual": 159,
                "stripe_price_ids": {
                    "monthly": PRICE_IDS.get("enterprise_monthly"),
                    "annual": PRICE_IDS.get("enterprise_annual"),
                },
                "features": [
                    "Everything in Professional",
                    "Unlimited team members",
                    "White-label options",
                    "API access",
                    "Advanced analytics",
                    "Custom integrations",
                    "Dedicated account manager",
                    "24/7 phone support",
                    "Custom training",
                    "SLA guarantee"
                ]
            }
        ]
    }

@router.get("/subscription/{customer_id}")
async def get_subscription(customer_id: str):
    """Get customer subscription details"""
    try:
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail="Stripe is not configured")

        subscriptions = stripe.Subscription.list(customer=customer_id, status="all", limit=1)
        if not subscriptions.data:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription = subscriptions.data[0]
        current_period_end = None
        if getattr(subscription, "current_period_end", None):
            current_period_end = datetime.fromtimestamp(subscription.current_period_end).date().isoformat()

        return {
            "customer_id": customer_id,
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": bool(getattr(subscription, "cancel_at_period_end", False)),
                "current_period_end": current_period_end,
                "items": subscription.get("items", {}).get("data", []),
            },
        }
    except Exception as e:
        logger.error(f"Subscription fetch error: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")
