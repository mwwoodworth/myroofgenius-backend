"""
Revenue Automation System - PRODUCTION READY
Handles Stripe integration, billing, subscriptions, and payment collection
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import os
import stripe
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncio
import hashlib
import hmac

logger = logging.getLogger(__name__)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY environment variable is required")
stripe.api_key = STRIPE_SECRET_KEY

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
if not STRIPE_WEBHOOK_SECRET:
    raise RuntimeError("STRIPE_WEBHOOK_SECRET environment variable is required")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SubscriptionTier(str, Enum):
    STARTER = "starter"  # $199/month
    PROFESSIONAL = "professional"  # $399/month
    ENTERPRISE = "enterprise"  # $999/month


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class RevenueAutomation:
    """
    Complete revenue automation system with Stripe integration
    """

    def __init__(self):
        self.price_ids = {
            SubscriptionTier.STARTER: "price_starter_199",
            SubscriptionTier.PROFESSIONAL: "price_professional_399",
            SubscriptionTier.ENTERPRISE: "price_enterprise_999"
        }

    async def create_checkout_session(
        self,
        customer_email: str,
        subscription_tier: SubscriptionTier,
        success_url: str,
        cancel_url: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for new subscription
        """
        try:
            # Create or get Stripe customer
            customer = await self._get_or_create_stripe_customer(customer_email)

            # Create checkout session
            # Stripe's SDK is synchronous; run in a worker thread so this async
            # endpoint doesn't block the event loop.
            session = await asyncio.to_thread(
                stripe.checkout.Session.create,
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": self.price_ids.get(subscription_tier),
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
                subscription_data={
                    "trial_period_days": 7,
                    "metadata": {"tier": subscription_tier.value},
                },
            )

            # Record in database
            def _record_checkout_session():
                with SessionLocal() as db:
                    db.execute(
                        text(
                            """
                            INSERT INTO stripe_checkout_sessions (
                                id, session_id, customer_email,
                                subscription_tier, status, created_at
                            ) VALUES (
                                :id, :session_id, :customer_email,
                                :subscription_tier, 'pending', CURRENT_TIMESTAMP
                            )
                            """
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "session_id": session.id,
                            "customer_email": customer_email,
                            "subscription_tier": subscription_tier.value,
                        },
                    )
                    db.commit()

            await asyncio.to_thread(_record_checkout_session)

            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "status": "created"
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }

    async def handle_webhook(
        self,
        payload: str,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )

            # Handle different event types
            handlers = {
                "checkout.session.completed": self._handle_checkout_completed,
                "invoice.payment_succeeded": self._handle_payment_succeeded,
                "invoice.payment_failed": self._handle_payment_failed,
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_cancelled
            }

            handler = handlers.get(event.type)
            if handler:
                result = await handler(event.data.object)

                # Record webhook processing
                with SessionLocal() as db:
                    db.execute(text("""
                        INSERT INTO stripe_webhook_events (
                            id, event_id, event_type, status,
                            processed_at
                        ) VALUES (
                            :id, :event_id, :event_type, 'processed',
                            CURRENT_TIMESTAMP
                        )
                    """), {
                        "id": str(uuid.uuid4()),
                        "event_id": event.id,
                        "event_type": event.type
                    })
                    db.commit()

                return result
            else:
                logger.info(f"Unhandled webhook event type: {event.type}")
                return {"status": "ignored"}

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return {"error": "Invalid payload", "status": "failed"}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return {"error": "Invalid signature", "status": "failed"}

    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful checkout session completion
        """
        customer_email = session.get("customer_email")
        subscription_id = session.get("subscription")

        with SessionLocal() as db:
            # Update tenant with Stripe details
            db.execute(text("""
                UPDATE tenants
                SET stripe_customer_id = :customer_id,
                    stripe_subscription_id = :subscription_id,
                    subscription_status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = :email
            """), {
                "customer_id": session.get("customer"),
                "subscription_id": subscription_id,
                "email": customer_email
            })

            # Create payment record
            db.execute(text("""
                INSERT INTO stripe_payments (
                    id, customer_email, amount, currency,
                    status, stripe_payment_id, created_at
                ) VALUES (
                    :id, :email, :amount, :currency,
                    'succeeded', :payment_id, CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "email": customer_email,
                "amount": session.get("amount_total", 0) / 100,
                "currency": session.get("currency", "usd"),
                "payment_id": session.get("payment_intent")
            })

            # Record revenue
            db.execute(text("""
                INSERT INTO mrg_revenue (
                    id, customer_id, amount, source,
                    description, created_at
                ) VALUES (
                    :id,
                    (SELECT id FROM tenants WHERE email = :email LIMIT 1),
                    :amount, 'stripe', :description,
                    CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "email": customer_email,
                "amount": session.get("amount_total", 0) / 100,
                "description": f"Subscription payment - {session.get('id')}"
            })

            db.commit()

        # Trigger onboarding workflow
        await self._trigger_onboarding(customer_email)

        return {"status": "processed", "subscription_id": subscription_id}

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment
        """
        with SessionLocal() as db:
            # Update payment status
            db.execute(text("""
                UPDATE stripe_payments
                SET status = 'succeeded',
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_payment_id = :payment_id
            """), {
                "payment_id": invoice.get("payment_intent")
            })

            # Update revenue metrics
            db.execute(text("""
                INSERT INTO revenue_metrics (
                    id, metric_type, value, date,
                    created_at
                ) VALUES (
                    :id, 'daily_revenue', :amount, :date,
                    CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "amount": invoice.get("amount_paid", 0) / 100,
                "date": datetime.utcnow().date()
            })

            db.commit()

        return {"status": "processed"}

    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed payment
        """
        customer_email = invoice.get("customer_email")

        with SessionLocal() as db:
            # Update payment status
            db.execute(text("""
                UPDATE stripe_payments
                SET status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_payment_id = :payment_id
            """), {
                "payment_id": invoice.get("payment_intent")
            })

            # Create retry task
            db.execute(text("""
                INSERT INTO payment_retry_queue (
                    id, customer_email, invoice_id,
                    retry_count, next_retry_at, created_at
                ) VALUES (
                    :id, :email, :invoice_id,
                    0, :next_retry, CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "email": customer_email,
                "invoice_id": invoice.get("id"),
                "next_retry": datetime.utcnow() + timedelta(days=3)
            })

            db.commit()

        # Send payment failed notification
        await self._send_payment_failed_notification(customer_email)

        return {"status": "processed"}

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle new subscription creation
        """
        with SessionLocal() as db:
            db.execute(text("""
                INSERT INTO stripe_subscriptions (
                    id, stripe_subscription_id, customer_id,
                    status, current_period_start, current_period_end,
                    created_at
                ) VALUES (
                    :id, :subscription_id, :customer_id,
                    :status, :period_start, :period_end,
                    CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "subscription_id": subscription.get("id"),
                "customer_id": subscription.get("customer"),
                "status": subscription.get("status"),
                "period_start": datetime.fromtimestamp(subscription.get("current_period_start")),
                "period_end": datetime.fromtimestamp(subscription.get("current_period_end"))
            })
            db.commit()

        return {"status": "processed"}

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription update
        """
        with SessionLocal() as db:
            db.execute(text("""
                UPDATE stripe_subscriptions
                SET status = :status,
                    current_period_start = :period_start,
                    current_period_end = :period_end,
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = :subscription_id
            """), {
                "subscription_id": subscription.get("id"),
                "status": subscription.get("status"),
                "period_start": datetime.fromtimestamp(subscription.get("current_period_start")),
                "period_end": datetime.fromtimestamp(subscription.get("current_period_end"))
            })
            db.commit()

        return {"status": "processed"}

    async def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription cancellation
        """
        with SessionLocal() as db:
            # Update subscription status
            db.execute(text("""
                UPDATE stripe_subscriptions
                SET status = 'cancelled',
                    cancelled_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = :subscription_id
            """), {
                "subscription_id": subscription.get("id")
            })

            # Update tenant status
            db.execute(text("""
                UPDATE tenants
                SET subscription_status = 'cancelled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = :subscription_id
            """), {
                "subscription_id": subscription.get("id")
            })

            db.commit()

        # Trigger retention workflow
        await self._trigger_retention_workflow(subscription.get("customer"))

        return {"status": "processed"}

    async def _get_or_create_stripe_customer(self, email: str) -> Any:
        """
        Get existing or create new Stripe customer
        """
        # Stripe SDK is synchronous; keep this non-blocking for async endpoints.
        customers = await asyncio.to_thread(stripe.Customer.list, email=email, limit=1)

        if getattr(customers, "data", None):
            return customers.data[0]

        return await asyncio.to_thread(
            stripe.Customer.create,
            email=email,
            metadata={"source": "myroofgenius"},
        )

    async def _trigger_onboarding(self, customer_email: str) -> None:
        """
        Trigger customer onboarding workflow
        """
        with SessionLocal() as db:
            db.execute(text("""
                INSERT INTO workflow_queue (
                    id, workflow_type, entity_id,
                    context, status, created_at
                ) VALUES (
                    :id, 'customer_onboarding', :entity_id,
                    :context, 'pending', CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "entity_id": customer_email,
                "context": json.dumps({"email": customer_email})
            })
            db.commit()

    async def _send_payment_failed_notification(self, customer_email: str) -> None:
        """
        Send payment failed notification
        """
        with SessionLocal() as db:
            db.execute(text("""
                INSERT INTO email_queue (
                    id, recipient_email, template,
                    status, created_at
                ) VALUES (
                    :id, :email, 'payment_failed',
                    'pending', CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "email": customer_email
            })
            db.commit()

    async def _trigger_retention_workflow(self, customer_id: str) -> None:
        """
        Trigger customer retention workflow
        """
        with SessionLocal() as db:
            db.execute(text("""
                INSERT INTO workflow_queue (
                    id, workflow_type, entity_id,
                    context, status, created_at
                ) VALUES (
                    :id, 'retention_campaign', :entity_id,
                    :context, 'pending', CURRENT_TIMESTAMP
                )
            """), {
                "id": str(uuid.uuid4()),
                "entity_id": customer_id,
                "context": json.dumps({"customer_id": customer_id})
            })
            db.commit()

    async def process_payment_retries(self) -> Dict[str, Any]:
        """
        Process failed payment retries
        """
        with SessionLocal() as db:
            # Get payments to retry
            retries = db.execute(text("""
                SELECT * FROM payment_retry_queue
                WHERE next_retry_at <= CURRENT_TIMESTAMP
                AND retry_count < 3
                AND status = 'pending'
                LIMIT 10
            """)).fetchall()

            processed = 0
            for retry in retries:
                try:
                    # Attempt to collect payment
                    invoice = stripe.Invoice.retrieve(retry.invoice_id)
                    invoice.pay()

                    # Update retry status
                    db.execute(text("""
                        UPDATE payment_retry_queue
                        SET status = 'succeeded',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """), {"id": retry.id})

                    processed += 1

                except stripe.error.StripeError as e:
                    # Update retry count
                    db.execute(text("""
                        UPDATE payment_retry_queue
                        SET retry_count = retry_count + 1,
                            next_retry_at = :next_retry,
                            last_error = :error,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """), {
                        "id": retry.id,
                        "next_retry": datetime.utcnow() + timedelta(days=3),
                        "error": str(e)
                    })

            db.commit()

            return {
                "processed": processed,
                "total_retries": len(retries)
            }

    async def get_revenue_metrics(self) -> Dict[str, Any]:
        """
        Get revenue metrics and analytics
        """
        with SessionLocal() as db:
            # Get current month metrics
            metrics = db.execute(text("""
                SELECT
                    COUNT(DISTINCT customer_id) as customers,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_transaction,
                    COUNT(*) as transactions
                FROM mrg_revenue
                WHERE created_at >= date_trunc('month', CURRENT_DATE)
            """)).fetchone()

            # Get MRR (Monthly Recurring Revenue)
            mrr = db.execute(text("""
                SELECT
                    COUNT(*) as active_subscriptions,
                    SUM(CASE
                        WHEN subscription_tier = 'starter' THEN 199
                        WHEN subscription_tier = 'professional' THEN 399
                        WHEN subscription_tier = 'enterprise' THEN 999
                        ELSE 0
                    END) as mrr
                FROM tenants
                WHERE subscription_status = 'active'
            """)).fetchone()

            # Get growth metrics
            growth = db.execute(text("""
                SELECT
                    date_trunc('month', created_at) as month,
                    SUM(amount) as revenue
                FROM mrg_revenue
                WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY month
                ORDER BY month
            """)).fetchall()

            return {
                "current_month": {
                    "customers": metrics.customers or 0,
                    "revenue": float(metrics.total_revenue or 0),
                    "avg_transaction": float(metrics.avg_transaction or 0),
                    "transactions": metrics.transactions or 0
                },
                "mrr": {
                    "value": float(mrr.mrr or 0),
                    "subscriptions": mrr.active_subscriptions or 0
                },
                "growth": [
                    {"month": g.month.strftime("%Y-%m"), "revenue": float(g.revenue)}
                    for g in growth
                ],
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
revenue_automation = RevenueAutomation()
