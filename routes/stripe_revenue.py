"""
Complete Stripe Revenue Pipeline
Handles real money processing, subscriptions, and revenue tracking
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import stripe
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import httpx

router = APIRouter(tags=["Stripe Revenue"])

# Stripe configuration - PERMANENT RESTRICTED KEY
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "<STRIPE_KEY_REDACTED>")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_REDACTED_placeholder")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = "matthew@brainstackstudio.com"

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

def get_db():
    engine = create_engine(DATABASE_URL)
    return engine

async def send_email(to_email: str, subject: str, html_content: str):
    """Send email via SendGrid"""
    if not SENDGRID_API_KEY:
        print(f"Would send email to {to_email}: {subject}")
        return
    
    async with httpx.AsyncClient() as client:
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
            }
        )
        return response.status_code == 202

@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest):
    """
    Create Stripe checkout session for one-time purchase
    """
    try:
        # Create or get customer
        customers = stripe.Customer.list(email=request.customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=request.customer_email,
                metadata=request.metadata
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
                "customer_email": request.customer_email
            }
        )
        
        # Store in database
        with get_db().connect() as conn:
            conn.execute(text("""
                INSERT INTO checkout_sessions (
                    session_id,
                    customer_email,
                    price_id,
                    status,
                    metadata,
                    created_at
                ) VALUES (
                    :session_id,
                    :email,
                    :price_id,
                    'pending',
                    :metadata,
                    NOW()
                )
            """), {
                "session_id": session.id,
                "email": request.customer_email,
                "price_id": request.price_id,
                "metadata": json.dumps(request.metadata)
            })
            conn.commit()
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-subscription")
async def create_subscription(request: SubscriptionRequest, background_tasks: BackgroundTasks):
    """
    Create recurring subscription with trial period
    """
    try:
        # Create or get customer
        customers = stripe.Customer.list(email=request.customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=request.customer_email,
                metadata=request.metadata
            )
        
        # Create subscription with trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': request.price_id}],
            trial_period_days=request.trial_days,
            metadata={
                **request.metadata,
                "customer_email": request.customer_email
            },
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent']
        )
        
        # Store subscription
        with get_db().connect() as conn:
            conn.execute(text("""
                INSERT INTO subscriptions (
                    stripe_subscription_id,
                    customer_id,
                    customer_email,
                    price_id,
                    status,
                    trial_end,
                    metadata
                ) VALUES (
                    :sub_id,
                    :customer_id,
                    :email,
                    :price_id,
                    :status,
                    :trial_end,
                    :metadata
                )
            """), {
                "sub_id": subscription.id,
                "customer_id": customer.id,
                "email": request.customer_email,
                "price_id": request.price_id,
                "status": subscription.status,
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                "metadata": json.dumps(request.metadata)
            })
            conn.commit()
        
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
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
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
        
        # Update database
        with get_db().connect() as conn:
            conn.execute(text("""
                UPDATE checkout_sessions
                SET status = 'completed',
                    completed_at = NOW()
                WHERE session_id = :session_id
            """), {"session_id": session.id})
            
            # Track revenue
            conn.execute(text("""
                INSERT INTO revenue_tracking (
                    date,
                    source,
                    amount_cents,
                    customer_email,
                    stripe_payment_id
                ) VALUES (
                    CURRENT_DATE,
                    'checkout',
                    :amount,
                    :email,
                    :payment_id
                )
            """), {
                "amount": session.amount_total,
                "email": session.customer_email,
                "payment_id": session.payment_intent
            })
            conn.commit()
        
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
        with get_db().connect() as conn:
            conn.execute(text("""
                UPDATE subscriptions
                SET status = :status,
                    current_period_start = :start,
                    current_period_end = :end
                WHERE stripe_subscription_id = :sub_id
            """), {
                "status": subscription.status,
                "start": datetime.fromtimestamp(subscription.current_period_start),
                "end": datetime.fromtimestamp(subscription.current_period_end),
                "sub_id": subscription.id
            })
            conn.commit()
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        
        # Track recurring revenue
        with get_db().connect() as conn:
            conn.execute(text("""
                INSERT INTO revenue_tracking (
                    date,
                    source,
                    amount_cents,
                    customer_email,
                    stripe_payment_id,
                    subscription_id
                ) VALUES (
                    CURRENT_DATE,
                    'subscription',
                    :amount,
                    :email,
                    :payment_id,
                    :sub_id
                )
            """), {
                "amount": invoice.amount_paid,
                "email": invoice.customer_email,
                "payment_id": invoice.payment_intent,
                "sub_id": invoice.subscription
            })
            conn.commit()
    
    return {"received": True}

@router.get("/dashboard-metrics")
async def get_revenue_metrics():
    """
    Real-time revenue dashboard metrics
    """
    with get_db().connect() as conn:
        # Today's revenue
        today_result = conn.execute(text("""
            SELECT COALESCE(SUM(amount_cents), 0) / 100.0 as revenue
            FROM revenue_tracking
            WHERE date = CURRENT_DATE
        """))
        today_revenue = today_result.scalar()
        
        # This month's revenue
        month_result = conn.execute(text("""
            SELECT COALESCE(SUM(amount_cents), 0) / 100.0 as revenue
            FROM revenue_tracking
            WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
        """))
        month_revenue = month_result.scalar()
        
        # Active subscriptions
        subs_result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM subscriptions
            WHERE status = 'active'
        """))
        active_subs = subs_result.scalar()
        
        # Conversion rate
        conv_result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM checkout_sessions
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """))
        conv_row = conv_result.fetchone()
        conversion_rate = (conv_row[1] / conv_row[0] * 100) if conv_row[0] > 0 else 0
        
        return {
            "today_revenue": today_revenue or 0,
            "month_revenue": month_revenue or 0,
            "active_subscriptions": active_subs or 0,
            "conversion_rate": round(conversion_rate, 2),
            "mrr": (active_subs or 0) * 99.99,  # Assuming $99.99 average
            "targets": {
                "week_1": 2500,
                "week_2": 7500,
                "week_4": 25000
            }
        }

@router.post("/cancel-subscription")
async def cancel_subscription(subscription_id: str, reason: Optional[str] = None):
    """
    Handle subscription cancellation with retention attempt
    """
    try:
        # Offer discount before canceling
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Create 50% off coupon for retention
        coupon = stripe.Coupon.create(
            percent_off=50,
            duration='repeating',
            duration_in_months=3,
            id=f"retention_{subscription_id[:8]}"
        )
        
        # Apply to subscription
        stripe.Subscription.modify(
            subscription_id,
            coupon=coupon.id
        )
        
        return {
            "message": "We've applied 50% off for 3 months! Please reconsider.",
            "discount_applied": True,
            "new_price": subscription.items.data[0].price.unit_amount / 200  # 50% off
        }
        
    except Exception as e:
        # If retention fails, cancel
        stripe.Subscription.delete(subscription_id)
        
        with get_db().connect() as conn:
            conn.execute(text("""
                UPDATE subscriptions
                SET status = 'canceled',
                    canceled_at = NOW(),
                    cancellation_reason = :reason
                WHERE stripe_subscription_id = :sub_id
            """), {
                "reason": reason,
                "sub_id": subscription_id
            })
            conn.commit()
        
        return {"message": "Subscription canceled", "status": "canceled RETURNING * RETURNING * RETURNING *"}
