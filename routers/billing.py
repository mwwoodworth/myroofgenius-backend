
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import stripe
import json
import os
from pydantic import BaseModel

router = APIRouter()

# Stripe configuration - Use live key if available, otherwise API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY_LIVE") or os.getenv("STRIPE_API_KEY_TEST", "<STRIPE_KEY_REDACTED>")

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
async def create_checkout_session(request: CheckoutSessionRequest):
    """Create a Stripe checkout session"""
    try:
        # Check if we have a real Stripe key
        if stripe.api_key and not stripe.api_key.startswith("<STRIPE_KEY_REDACTED>"):
            # Create real Stripe checkout session
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
        else:
            # Return mock session for testing
            return {
                "checkout_url": f"{request.success_url}?session_id=mock_session_123",
                "session_id": "mock_session_123"
            }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription-status")
async def get_subscription_status(db: Session = Depends(get_db)):
    """Get subscription status for current user"""
    try:
        # Return mock data for now
        return {
            "status": "active",
            "plan": "professional",
            "current_period_end": datetime.now().isoformat(),
            "cancel_at_period_end": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(subscription_id: str):
    """Cancel a subscription"""
    try:
        return {"message": "Subscription cancelled", "subscription_id": subscription_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payment-methods")
async def get_payment_methods():
    """Get payment methods for current user"""
    return {
        "payment_methods": [
            {
                "id": "pm_123",
                "type": "card",
                "last4": "4242",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025
            }
        ]
    }

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    # Just acknowledge for now
    return {"received": True}
