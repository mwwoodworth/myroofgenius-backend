"""Stripe Webhook Handler for MyRoofGenius"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import stripe
import os
import json
import logging
from datetime import datetime
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal as _SessionLocal

if _SessionLocal is None:  # pragma: no cover
    def SessionLocal():  # type: ignore
        raise RuntimeError("DATABASE_URL must be configured for Stripe webhook handling.")
else:
    SessionLocal = _SessionLocal

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY is not configured; Stripe operations may fail.")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-webhooks"])

@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body
        payload = await request.body()

        # SECURITY FIX: Always require webhook signature verification
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("CRITICAL: Stripe webhook secret not configured - rejecting request")
            raise HTTPException(status_code=500, detail="Webhook configuration error")

        if not stripe_signature:
            logger.error("Missing Stripe signature header")
            raise HTTPException(status_code=400, detail="Missing signature")

        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        event_type = event.get('type', '')
        data = event.get('data', {}).get('object', {})

        logger.info(f"Processing webhook event: {event_type}")

        with SessionLocal() as db:
            # Log the webhook event
            db.execute(text("""
                INSERT INTO webhook_events (id, event_type, stripe_event_id, data, created_at)
                VALUES (:id, :event_type, :stripe_event_id, :data, NOW())
                ON CONFLICT (stripe_event_id) DO NOTHING
            """), {
                "id": str(uuid.uuid4()),
                "event_type": event_type,
                "stripe_event_id": event.get('id', ''),
                "data": json.dumps(event)
            })
            db.commit()

            # Process specific events
            if event_type == 'checkout.session.completed':
                await handle_checkout_completed(db, data)

            elif event_type == 'customer.subscription.created':
                await handle_subscription_created(db, data)

            elif event_type == 'customer.subscription.updated':
                await handle_subscription_updated(db, data)

            elif event_type == 'customer.subscription.deleted':
                await handle_subscription_deleted(db, data)

            elif event_type == 'invoice.payment_succeeded':
                await handle_payment_succeeded(db, data)

            elif event_type == 'invoice.payment_failed':
                await handle_payment_failed(db, data)

            elif event_type == 'customer.created':
                await handle_customer_created(db, data)

            elif event_type == 'payment_intent.succeeded':
                await handle_payment_intent_succeeded(db, data)

            elif event_type == 'payment_method.attached':
                await handle_payment_method_attached(db, data)

            else:
                logger.info(f"Unhandled event type: {event_type}")

        return {"received": True, "type": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # Return success to prevent Stripe retries on non-critical errors
        return {"received": True, "error": str(e)}


async def handle_checkout_completed(db: Session, data: dict):
    """Handle completed checkout session"""
    try:
        customer_email = data.get('customer_email')
        customer_id = data.get('customer')
        subscription_id = data.get('subscription')
        amount_total = data.get('amount_total', 0) / 100  # Convert from cents
        mode = data.get('mode', 'payment')  # 'payment' or 'subscription'

        # CRITICAL: Extract tenant_id from metadata for revenue attribution
        metadata = data.get('metadata', {})
        tenant_id = metadata.get('tenant_id')
        product_key = metadata.get('product_key')
        plan = metadata.get('plan')
        user_id = metadata.get('user_id')

        # Default tenant for MRG if not specified (guest checkouts)
        MRG_DEFAULT_TENANT_ID = os.getenv('MRG_DEFAULT_TENANT_ID', '00000000-0000-0000-0000-000000000001')
        if not tenant_id:
            tenant_id = MRG_DEFAULT_TENANT_ID
            logger.info(f"Using default MRG tenant for checkout: {tenant_id}")

        # Create or update customer
        if customer_email:
            db.execute(text("""
                INSERT INTO customers (id, email, stripe_customer_id, tenant_id, created_at)
                VALUES (:id, :email, :stripe_id, :tenant_id, NOW())
                ON CONFLICT (email) DO UPDATE
                SET stripe_customer_id = :stripe_id, tenant_id = COALESCE(customers.tenant_id, :tenant_id)
            """), {
                "id": str(uuid.uuid4()),
                "email": customer_email,
                "stripe_id": customer_id,
                "tenant_id": tenant_id
            })

            # Create subscription record with tenant_id
            if subscription_id:
                db.execute(text("""
                    INSERT INTO subscriptions (id, customer_id, stripe_subscription_id, status, amount, tenant_id, created_at)
                    VALUES (:id, :customer_id, :subscription_id, 'active', :amount, :tenant_id, NOW())
                    ON CONFLICT (stripe_subscription_id) DO UPDATE
                    SET status = 'active', amount = :amount, tenant_id = COALESCE(subscriptions.tenant_id, :tenant_id)
                """), {
                    "id": str(uuid.uuid4()),
                    "customer_id": customer_id,
                    "subscription_id": subscription_id,
                    "amount": amount_total,
                    "tenant_id": tenant_id
                })

            # CRITICAL: Track revenue in mrg_revenue table for MRR/ARR calculations
            revenue_type = 'subscription' if mode == 'subscription' else 'one_time'

            db.execute(text("""
                INSERT INTO mrg_revenue (
                    id, tenant_id, amount, currency, type, description,
                    stripe_payment_intent_id, status, created_at, paid_at, metadata
                )
                VALUES (
                    gen_random_uuid(), :tenant_id, :amount, 'USD', :type, :description,
                    :payment_intent_id, 'completed', NOW(), NOW(),
                    jsonb_build_object('product_key', :product_key, 'plan', :plan, 'stripe_customer_id', :stripe_customer_id, 'stripe_subscription_id', :stripe_subscription_id)
                )
            """), {
                "tenant_id": tenant_id,
                "amount": amount_total,
                "type": revenue_type,
                "description": f"Checkout: {product_key or 'MRG Product'}",
                "payment_intent_id": data.get('payment_intent'),
                "product_key": product_key,
                "plan": plan,
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id
            })

            db.commit()
            logger.info(f"Checkout completed for {customer_email} (tenant: {tenant_id}, amount: ${amount_total}, type: {revenue_type})")

    except Exception as e:
        logger.error(f"Error handling checkout: {str(e)}")
        db.rollback()


async def handle_subscription_created(db: Session, data: dict):
    """Handle new subscription creation"""
    try:
        subscription_id = data.get('id')
        customer_id = data.get('customer')
        status = data.get('status')
        plan_id = data.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
        amount = data.get('items', {}).get('data', [{}])[0].get('price', {}).get('unit_amount', 0) / 100

        # Extract tenant_id from subscription metadata
        metadata = data.get('metadata', {})
        tenant_id = metadata.get('tenant_id')

        # Default tenant for MRG if not specified
        MRG_DEFAULT_TENANT_ID = os.getenv('MRG_DEFAULT_TENANT_ID', '00000000-0000-0000-0000-000000000001')
        if not tenant_id:
            tenant_id = MRG_DEFAULT_TENANT_ID

        db.execute(text("""
            INSERT INTO subscriptions (id, stripe_subscription_id, customer_id, plan_id, status, amount, tenant_id, created_at)
            VALUES (:id, :subscription_id, :customer_id, :plan_id, :status, :amount, :tenant_id, NOW())
            ON CONFLICT (stripe_subscription_id) DO UPDATE
            SET status = :status, amount = :amount, tenant_id = COALESCE(subscriptions.tenant_id, :tenant_id)
        """), {
            "id": str(uuid.uuid4()),
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "plan_id": plan_id,
            "status": status,
            "amount": amount,
            "tenant_id": tenant_id
        })
        db.commit()
        logger.info(f"Subscription created: {subscription_id} (tenant: {tenant_id})")

    except Exception as e:
        logger.error(f"Error handling subscription creation: {str(e)}")
        db.rollback()


async def handle_subscription_updated(db: Session, data: dict):
    """Handle subscription updates"""
    try:
        subscription_id = data.get('id')
        status = data.get('status')

        db.execute(text("""
            UPDATE subscriptions
            SET status = :status, updated_at = NOW()
            WHERE stripe_subscription_id = :subscription_id
        """), {
            "subscription_id": subscription_id,
            "status": status
        })
        db.commit()
        logger.info(f"Subscription updated: {subscription_id} to {status}")

    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        db.rollback()


async def handle_subscription_deleted(db: Session, data: dict):
    """Handle subscription cancellation"""
    try:
        subscription_id = data.get('id')

        db.execute(text("""
            UPDATE subscriptions
            SET status = 'canceled', canceled_at = NOW()
            WHERE stripe_subscription_id = :subscription_id
        """), {
            "subscription_id": subscription_id
        })
        db.commit()
        logger.info(f"Subscription canceled: {subscription_id}")

    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        db.rollback()


async def handle_payment_succeeded(db: Session, data: dict):
    """Handle successful payment"""
    try:
        invoice_id = data.get('id')
        customer_id = data.get('customer')
        amount_paid = data.get('amount_paid', 0) / 100
        subscription_id = data.get('subscription')

        # Try to get tenant_id from subscription metadata or fallback to default
        metadata = data.get('subscription_details', {}).get('metadata', {}) if data.get('subscription_details') else {}
        tenant_id = metadata.get('tenant_id')

        # If no tenant_id in metadata, try to look up from existing subscription
        if not tenant_id and subscription_id:
            result = db.execute(text("""
                SELECT tenant_id FROM subscriptions WHERE stripe_subscription_id = :subscription_id
            """), {"subscription_id": subscription_id}).first()
            if result and result.tenant_id:
                tenant_id = str(result.tenant_id)

        # Default tenant for MRG if not specified
        MRG_DEFAULT_TENANT_ID = os.getenv('MRG_DEFAULT_TENANT_ID', '00000000-0000-0000-0000-000000000001')
        if not tenant_id:
            tenant_id = MRG_DEFAULT_TENANT_ID

        # Record payment with tenant_id
        db.execute(text("""
            INSERT INTO payments (id, invoice_id, customer_id, amount, status, tenant_id, created_at)
            VALUES (:id, :invoice_id, :customer_id, :amount, 'succeeded', :tenant_id, NOW())
        """), {
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "amount": amount_paid,
            "tenant_id": tenant_id
        })

        # Update subscription payment date
        if subscription_id:
            db.execute(text("""
                UPDATE subscriptions
                SET last_payment_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """), {
                "subscription_id": subscription_id
            })

        # Track revenue for recurring subscription payments in mrg_revenue
        if subscription_id:
            db.execute(text("""
                INSERT INTO mrg_revenue (
                    id, tenant_id, amount, currency, type, description,
                    stripe_invoice_id, status, created_at, paid_at, metadata
                )
                VALUES (
                    gen_random_uuid(), :tenant_id, :amount, 'USD', 'subscription', :description,
                    :invoice_id, 'completed', NOW(), NOW(),
                    jsonb_build_object('stripe_customer_id', :stripe_customer_id, 'stripe_subscription_id', :stripe_subscription_id)
                )
            """), {
                "tenant_id": tenant_id,
                "amount": amount_paid,
                "description": f"Subscription payment",
                "invoice_id": invoice_id,
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id
            })

        db.commit()
        logger.info(f"Payment succeeded: {invoice_id} for ${amount_paid} (tenant: {tenant_id})")

    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")
        db.rollback()


async def handle_payment_failed(db: Session, data: dict):
    """Handle failed payment"""
    try:
        invoice_id = data.get('id')
        customer_id = data.get('customer')
        subscription_id = data.get('subscription')

        # Record failed payment
        db.execute(text("""
            INSERT INTO payment_failures (id, invoice_id, customer_id, subscription_id, created_at)
            VALUES (:id, :invoice_id, :customer_id, :subscription_id, NOW())
        """), {
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "subscription_id": subscription_id
        })

        # Mark subscription as past_due
        if subscription_id:
            db.execute(text("""
                UPDATE subscriptions
                SET status = 'past_due'
                WHERE stripe_subscription_id = :subscription_id
            """), {
                "subscription_id": subscription_id
            })

        db.commit()
        logger.warning(f"Payment failed: {invoice_id}")

    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")
        db.rollback()


async def handle_customer_created(db: Session, data: dict):
    """Handle new customer creation"""
    try:
        customer_id = data.get('id')
        email = data.get('email')
        name = data.get('name')

        # Extract tenant_id from customer metadata
        metadata = data.get('metadata', {})
        tenant_id = metadata.get('tenant_id')

        # Default tenant for MRG if not specified
        MRG_DEFAULT_TENANT_ID = os.getenv('MRG_DEFAULT_TENANT_ID', '00000000-0000-0000-0000-000000000001')
        if not tenant_id:
            tenant_id = MRG_DEFAULT_TENANT_ID

        if email:
            db.execute(text("""
                INSERT INTO customers (id, email, name, stripe_customer_id, tenant_id, created_at)
                VALUES (:id, :email, :name, :stripe_id, :tenant_id, NOW())
                ON CONFLICT (email) DO UPDATE
                SET stripe_customer_id = :stripe_id, name = COALESCE(:name, name), tenant_id = COALESCE(customers.tenant_id, :tenant_id)
            """), {
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "stripe_id": customer_id,
                "tenant_id": tenant_id
            })
            db.commit()
            logger.info(f"Customer created: {email} (tenant: {tenant_id})")

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        db.rollback()


async def handle_payment_intent_succeeded(db: Session, data: dict):
    """Handle successful payment intent"""
    try:
        payment_intent_id = data.get('id')
        amount = data.get('amount', 0) / 100
        customer_id = data.get('customer')

        # Extract tenant_id from payment intent metadata
        metadata = data.get('metadata', {})
        tenant_id = metadata.get('tenant_id')

        # Default tenant for MRG if not specified
        MRG_DEFAULT_TENANT_ID = os.getenv('MRG_DEFAULT_TENANT_ID', '00000000-0000-0000-0000-000000000001')
        if not tenant_id:
            tenant_id = MRG_DEFAULT_TENANT_ID

        # Record one-time payment with tenant_id
        db.execute(text("""
            INSERT INTO payments (id, payment_intent_id, customer_id, amount, status, tenant_id, created_at)
            VALUES (:id, :payment_intent_id, :customer_id, :amount, 'succeeded', :tenant_id, NOW())
            ON CONFLICT (payment_intent_id) DO NOTHING
        """), {
            "id": str(uuid.uuid4()),
            "payment_intent_id": payment_intent_id,
            "customer_id": customer_id,
            "amount": amount,
            "tenant_id": tenant_id
        })

        # Track one-time revenue in mrg_revenue
        product_key = metadata.get('product_key')

        db.execute(text("""
            INSERT INTO mrg_revenue (
                id, tenant_id, amount, currency, type, description,
                stripe_payment_intent_id, status, created_at, paid_at, metadata
            )
            VALUES (
                gen_random_uuid(), :tenant_id, :amount, 'USD', 'one_time', :description,
                :payment_intent_id, 'completed', NOW(), NOW(),
                jsonb_build_object('product_key', :product_key, 'stripe_customer_id', :stripe_customer_id)
            )
        """), {
            "tenant_id": tenant_id,
            "amount": amount,
            "description": f"One-time payment: {product_key or 'MRG Product'}",
            "payment_intent_id": payment_intent_id,
            "product_key": product_key,
            "stripe_customer_id": customer_id
        })

        db.commit()
        logger.info(f"Payment intent succeeded: {payment_intent_id} for ${amount} (tenant: {tenant_id})")

    except Exception as e:
        logger.error(f"Error handling payment intent: {str(e)}")
        db.rollback()


async def handle_payment_method_attached(db: Session, data: dict):
    """Handle payment method attachment"""
    try:
        payment_method_id = data.get('id')
        customer_id = data.get('customer')
        card_info = data.get('card', {})

        # Store payment method info
        db.execute(text("""
            INSERT INTO payment_methods (id, customer_id, type, last4, brand, created_at)
            VALUES (:id, :customer_id, :type, :last4, :brand, NOW())
            ON CONFLICT (id) DO UPDATE
            SET customer_id = :customer_id
        """), {
            "id": payment_method_id,
            "customer_id": customer_id,
            "type": data.get('type', 'card'),
            "last4": card_info.get('last4'),
            "brand": card_info.get('brand')
        })
        db.commit()
        logger.info(f"Payment method attached: {payment_method_id}")

    except Exception as e:
        logger.error(f"Error attaching payment method: {str(e)}")
        db.rollback()


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "operational",
        "webhook_url": "https://brainops-backend-prod.onrender.com/api/v1/stripe/webhook",
        "instructions": "Configure this URL in Stripe Dashboard > Webhooks"
    }
