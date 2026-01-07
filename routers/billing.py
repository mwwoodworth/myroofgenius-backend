
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import stripe
import json
import os
from pydantic import BaseModel
import logging
from core.supabase_auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Stripe configuration - Use live key if available, otherwise test key
# NOTE: Do NOT use placeholder/redacted values - let it fail properly if not configured
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY_LIVE") or os.getenv("STRIPE_API_KEY_TEST")

def _require_stripe_key() -> None:
    if not stripe.api_key:
        logger.error("Stripe API key is not configured.")
        raise HTTPException(status_code=503, detail="Stripe is not configured")

def _require_admin(current_user: Dict[str, Any]) -> None:
    role = (
        current_user.get("role")
        or current_user.get("user_metadata", {}).get("role")
        or current_user.get("app_metadata", {}).get("role")
    )
    if role not in {"admin", "owner", "service"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
    customer_email: Optional[str] = None

class SubscriptionRequest(BaseModel):
    customer_id: str
    price_id: str

def get_db():
    """Database dependency"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a Stripe checkout session"""
    try:
        _require_stripe_key()
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email,
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription-status")
async def get_subscription_status(
    subscription_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get subscription status for current user"""
    try:
        _require_admin(current_user)
        _require_stripe_key()
        subscription = stripe.Subscription.retrieve(subscription_id)
        plan = subscription.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        return {
            "status": subscription.get("status"),
            "plan": plan,
            "current_period_end": datetime.utcfromtimestamp(subscription.get("current_period_end")).isoformat()
            if subscription.get("current_period_end")
            else None,
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(
    subscription_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel a subscription"""
    try:
        _require_admin(current_user)
        _require_stripe_key()
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return {"message": "Subscription cancellation scheduled", "subscription_id": subscription.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payment-methods")
async def get_payment_methods(
    stripe_customer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get payment methods for current user"""
    _require_admin(current_user)
    _require_stripe_key()
    try:
        methods = stripe.PaymentMethod.list(customer=stripe_customer_id, type="card")
        return {"payment_methods": methods.data}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks with signature verification"""
    import logging
    logger = logging.getLogger(__name__)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if not sig_header:
        logger.warning("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Handle specific event types
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    logger.info(f"Received Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        # Handle successful checkout
        logger.info(f"Checkout completed: {data.get('id')}")
    elif event_type == "invoice.payment_failed":
        # Handle failed payment
        logger.warning(f"Payment failed for invoice: {data.get('id')}")
    elif event_type == "customer.subscription.deleted":
        # Handle subscription cancellation
        logger.info(f"Subscription cancelled: {data.get('id')}")
    elif event_type == "charge.refunded":
        # Handle refund
        logger.info(f"Charge refunded: {data.get('id')}")

    return {"received": True, "type": event_type}
