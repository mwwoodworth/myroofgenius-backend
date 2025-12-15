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
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "<STRIPE_KEY_REDACTED>")

# Price IDs for different plans
PRICE_IDS = {
    "price_starter_monthly": "price_1QNxyzABCDEF123456",  # $49/month
    "price_starter_annual": "price_1QNxyzABCDEF123457",   # $39/month billed annually
    "price_professional_monthly": "price_1QNxyzABCDEF123458",  # $99/month
    "price_professional_annual": "price_1QNxyzABCDEF123459",   # $79/month billed annually
    "price_enterprise_monthly": "price_1QNxyzABCDEF123460",  # $199/month
    "price_enterprise_annual": "price_1QNxyzABCDEF123461",   # $159/month billed annually
}

# For testing, use test mode payment links
TEST_PAYMENT_LINKS = {
    "price_starter_monthly": "https://buy.stripe.com/test_starter_monthly",
    "price_professional_monthly": "https://buy.stripe.com/test_professional_monthly",
    "price_enterprise_monthly": "https://buy.stripe.com/test_enterprise_monthly",
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
        # For now, return a test payment link
        # In production, this would create a real Stripe checkout session

        # Map price_id to test payment link
        checkout_url = TEST_PAYMENT_LINKS.get(
            request.price_id,
            "https://buy.stripe.com/test_default"
        )

        # In production, you would do:
        """
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://myroofgenius.com/dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://myroofgenius.com/pricing',
            customer_email=request.customer_email,
            metadata=request.metadata
        )
        checkout_url = session.url
        """

        return {
            "checkout_url": checkout_url,
            "session_id": f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "price_id": request.price_id,
            "metadata": request.metadata
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
        
        # For now, return mock data
        return {
            "customer_id": customer_id,
            "subscription": {
                "plan": "professional",
                "status": "active",
                "current_period_end": "2025-10-16",
                "cancel_at_period_end": False
            },
            "usage": {
                "roof_analyses": 45,
                "estimates_created": 23,
                "invoices_sent": 18
            }
        }
    except Exception as e:
        logger.error(f"Subscription fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))