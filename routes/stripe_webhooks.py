"""Stripe Webhook Handler for MyRoofGenius."""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional, Dict, Any
import stripe
import os
import json
import logging
from datetime import datetime
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal as _SessionLocal
from services.subscription_lifecycle import subscription_lifecycle_service

if _SessionLocal is None:  # pragma: no cover

    def SessionLocal():  # type: ignore
        raise RuntimeError(
            "DATABASE_URL must be configured for Stripe webhook handling."
        )
else:
    SessionLocal = _SessionLocal

logger = logging.getLogger(__name__)


def _timestamp_to_datetime(value: Optional[Any]) -> Optional[datetime]:
    if value in (None, 0, "0", ""):
        return None
    try:
        return datetime.fromtimestamp(float(value))
    except (TypeError, ValueError, OSError):
        return None


def _extract_subscription_plan_and_amount(payload: Dict[str, Any]) -> tuple[Optional[str], Optional[float]]:
    price = (
        payload.get("items", {})
        .get("data", [{}])[0]
        .get("price", {})
    )
    plan_id = price.get("id")
    unit_amount = price.get("unit_amount")
    amount = (float(unit_amount) / 100.0) if unit_amount is not None else None
    return plan_id, amount


def _resolve_tenant_id(
    db: "Session",
    *,
    metadata: dict,
    subscription_id: str = None,
    customer_id: str = None,
    customer_email: str = None,
) -> Optional[str]:
    """Resolve tenant_id using a strict lookup chain. Returns None if unresolvable.

    Priority:
      1. metadata['tenant_id'] (Stripe object metadata)
      2. subscriptions.tenant_id by stripe_subscription_id
      3. customers.tenant_id by stripe_customer_id
      4. customers.tenant_id by email
    """
    # 1) Metadata
    tid = (metadata or {}).get("tenant_id")
    if tid:
        return str(tid)

    # 2) Subscription lookup
    if subscription_id:
        row = db.execute(
            text(
                "SELECT tenant_id FROM subscriptions WHERE stripe_subscription_id = :sid"
            ),
            {"sid": subscription_id},
        ).first()
        if row and row.tenant_id:
            return str(row.tenant_id)

    # 3) Customer lookup by stripe_customer_id
    if customer_id:
        row = db.execute(
            text("SELECT tenant_id FROM customers WHERE stripe_customer_id = :cid"),
            {"cid": customer_id},
        ).first()
        if row and row.tenant_id:
            return str(row.tenant_id)

    # 4) Customer lookup by email
    if customer_email:
        row = db.execute(
            text("SELECT tenant_id FROM customers WHERE email = :email"),
            {"email": customer_email},
        ).first()
        if row and row.tenant_id:
            return str(row.tenant_id)

    return None


def _quarantine_webhook_event(
    db: "Session", stripe_event_id: str, event_type: str, reason: str
) -> None:
    """Mark a webhook event as quarantined so it can be recovered later.

    Updates the already-logged webhook_events row to indicate tenant resolution failure.
    Uses a separate quarantine status column if available, otherwise logs to a new row
    with a synthetic stripe_event_id to avoid unique constraint violation.
    """
    logger.error(
        f"QUARANTINE [{event_type}]: {reason} (stripe_event_id={stripe_event_id})"
    )

    # Insert a quarantine record with a distinct synthetic event id
    quarantine_id = f"quarantine_{stripe_event_id}"
    db.execute(
        text(
            """
        INSERT INTO webhook_events (id, event_type, stripe_event_id, data, created_at)
        VALUES (:id, :event_type, :stripe_event_id, :data, NOW())
        ON CONFLICT (stripe_event_id) DO NOTHING
    """
        ),
        {
            "id": str(uuid.uuid4()),
            "event_type": f"quarantined.{event_type}",
            "stripe_event_id": quarantine_id,
            "data": json.dumps(
                {"reason": reason, "original_stripe_event_id": stripe_event_id}
            ),
        },
    )
    db.commit()


_webhook_attempt_tables_ready = False


def _ensure_webhook_attempts_table(db: "Session") -> None:
    """Create retry/audit table for webhook attempts if needed."""
    global _webhook_attempt_tables_ready
    if _webhook_attempt_tables_ready:
        return

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS webhook_event_attempts (
                id UUID PRIMARY KEY,
                stripe_event_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(255) NOT NULL,
                attempt_no INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_webhook_event_attempts_lookup
            ON webhook_event_attempts (stripe_event_id, created_at DESC)
            """
        )
    )
    db.commit()
    _webhook_attempt_tables_ready = True


def _next_attempt_number(db: "Session", stripe_event_id: str) -> int:
    row = db.execute(
        text(
            """
            SELECT COALESCE(MAX(attempt_no), 0) AS last_attempt
            FROM webhook_event_attempts
            WHERE stripe_event_id = :stripe_event_id
            """
        ),
        {"stripe_event_id": stripe_event_id},
    ).first()
    return int((row.last_attempt if row and row.last_attempt is not None else 0) + 1)


def _record_webhook_attempt(
    db: "Session",
    *,
    stripe_event_id: str,
    event_type: str,
    status: str,
    error_message: Optional[str] = None,
) -> int:
    _ensure_webhook_attempts_table(db)
    attempt_no = _next_attempt_number(db, stripe_event_id)
    db.execute(
        text(
            """
            INSERT INTO webhook_event_attempts (
                id, stripe_event_id, event_type, attempt_no, status, error_message, created_at
            ) VALUES (
                :id, :stripe_event_id, :event_type, :attempt_no, :status, :error_message, NOW()
            )
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "stripe_event_id": stripe_event_id,
            "event_type": event_type,
            "attempt_no": attempt_no,
            "status": status,
            "error_message": error_message,
        },
    )
    db.commit()
    return attempt_no


# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY is not configured; Stripe operations may fail.")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-webhooks"])


@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request, stripe_signature: Optional[str] = Header(None)
):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body
        payload = await request.body()

        # SECURITY FIX: Always require webhook signature verification
        if not STRIPE_WEBHOOK_SECRET:
            logger.error(
                "CRITICAL: Stripe webhook secret not configured - rejecting request"
            )
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
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})
        stripe_event_id = event.get("id", "")
        if not stripe_event_id:
            raise HTTPException(status_code=400, detail="Invalid event ID")

        logger.info("Processing webhook event: %s (%s)", event_type, stripe_event_id)

        with SessionLocal() as db:
            # Insert canonical webhook event row. We intentionally keep a single row
            # per Stripe event ID and track retries in webhook_event_attempts.
            inserted = db.execute(
                text(
                    """
                INSERT INTO webhook_events (id, event_type, stripe_event_id, data, created_at)
                VALUES (:id, :event_type, :stripe_event_id, :data, NOW())
                ON CONFLICT (stripe_event_id) DO NOTHING
                RETURNING stripe_event_id
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "event_type": event_type,
                    "stripe_event_id": stripe_event_id,
                    "data": json.dumps(event),
                },
            ).first()
            db.commit()

            is_retry = False
            if not inserted:
                _ensure_webhook_attempts_table(db)
                # Event already seen. Only short-circuit when last attempt succeeded.
                last_attempt = db.execute(
                    text(
                        """
                        SELECT status
                        FROM webhook_event_attempts
                        WHERE stripe_event_id = :stripe_event_id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"stripe_event_id": stripe_event_id},
                ).first()
                if last_attempt and last_attempt.status == "processed":
                    _record_webhook_attempt(
                        db,
                        stripe_event_id=stripe_event_id,
                        event_type=event_type,
                        status="duplicate",
                    )
                    return {
                        "received": True,
                        "type": event_type,
                        "duplicate": True,
                    }
                is_retry = True

            attempt_no = _record_webhook_attempt(
                db,
                stripe_event_id=stripe_event_id,
                event_type=event_type,
                status="processing",
            )

            try:
                # Process specific events
                if event_type == "checkout.session.completed":
                    await handle_checkout_completed(db, data, stripe_event_id)

                elif event_type == "customer.subscription.created":
                    await handle_subscription_created(db, data, stripe_event_id)

                elif event_type == "customer.subscription.updated":
                    await handle_subscription_updated(db, data, stripe_event_id)

                elif event_type == "customer.subscription.deleted":
                    await handle_subscription_deleted(db, data, stripe_event_id)

                elif event_type == "invoice.payment_succeeded":
                    await handle_payment_succeeded(db, data, stripe_event_id)

                elif event_type == "invoice.payment_failed":
                    await handle_payment_failed(db, data, stripe_event_id)

                elif event_type == "customer.created":
                    await handle_customer_created(db, data, stripe_event_id)

                elif event_type == "payment_intent.succeeded":
                    await handle_payment_intent_succeeded(db, data, stripe_event_id)

                elif event_type == "payment_method.attached":
                    await handle_payment_method_attached(db, data, stripe_event_id)

                else:
                    logger.info("Unhandled event type: %s", event_type)

                _record_webhook_attempt(
                    db,
                    stripe_event_id=stripe_event_id,
                    event_type=event_type,
                    status="processed",
                )
            except Exception as event_exc:
                _record_webhook_attempt(
                    db,
                    stripe_event_id=stripe_event_id,
                    event_type=event_type,
                    status="failed",
                    error_message=str(event_exc),
                )
                logger.exception(
                    "Webhook processing failed for event %s (attempt %s)",
                    stripe_event_id,
                    attempt_no,
                    exc_info=event_exc,
                )
                # Return non-2xx to let Stripe retry this event.
                raise HTTPException(status_code=500, detail="Webhook processing failed")

        return {
            "received": True,
            "type": event_type,
            "retry": is_retry,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Webhook processing error", exc_info=e)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_checkout_completed(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle completed checkout session"""
    try:
        customer_email = data.get("customer_email")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        amount_total = data.get("amount_total", 0) / 100  # Convert from cents
        mode = data.get("mode", "payment")  # 'payment' or 'subscription'

        metadata = data.get("metadata", {})
        product_key = metadata.get("product_key")
        plan = metadata.get("plan")

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
            customer_email=customer_email,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "checkout.session.completed",
                "tenant_id unresolvable from metadata/subscription/customer/email",
            )
            return

        # Create or update customer
        if customer_email:
            db.execute(
                text(
                    """
                INSERT INTO customers (id, email, stripe_customer_id, tenant_id, created_at)
                VALUES (:id, :email, :stripe_id, :tenant_id, NOW())
                ON CONFLICT (email) DO UPDATE
                SET stripe_customer_id = :stripe_id, tenant_id = COALESCE(customers.tenant_id, :tenant_id)
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "email": customer_email,
                    "stripe_id": customer_id,
                    "tenant_id": tenant_id,
                },
            )

            # Create subscription record with tenant_id
            if subscription_id:
                subscription_lifecycle_service.upsert_subscription_state(
                    db,
                    tenant_id=tenant_id,
                    subscription_id=subscription_id,
                    customer_id=customer_id,
                    plan_id=plan,
                    status="active",
                    amount=amount_total,
                    trial_end=None,
                )

            # CRITICAL: Track revenue in mrg_revenue table for MRR/ARR calculations
            revenue_type = "subscription" if mode == "subscription" else "one_time"

            db.execute(
                text(
                    """
                INSERT INTO mrg_revenue (
                    id, tenant_id, amount, currency, type, description,
                    stripe_payment_intent_id, status, created_at, paid_at, metadata
                )
                VALUES (
                    gen_random_uuid(), :tenant_id, :amount, 'USD', :type, :description,
                    :payment_intent_id, 'completed', NOW(), NOW(),
                    jsonb_build_object('product_key', :product_key, 'plan', :plan, 'stripe_customer_id', :stripe_customer_id, 'stripe_subscription_id', :stripe_subscription_id)
                )
            """
                ),
                {
                    "tenant_id": tenant_id,
                    "amount": amount_total,
                    "type": revenue_type,
                    "description": f"Checkout: {product_key or 'MRG Product'}",
                    "payment_intent_id": data.get("payment_intent"),
                    "product_key": product_key,
                    "plan": plan,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                },
            )

            db.commit()
            logger.info(
                f"Checkout completed for {customer_email} (tenant: {tenant_id}, amount: ${amount_total}, type: {revenue_type})"
            )

    except Exception as e:
        logger.error(f"Error handling checkout: {str(e)}")
        db.rollback()


async def handle_subscription_created(
    db: Session, data: dict, stripe_event_id: str = ""
):
    """Handle new subscription creation"""
    try:
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status") or "active"
        plan_id, amount = _extract_subscription_plan_and_amount(data)
        trial_end = _timestamp_to_datetime(data.get("trial_end"))

        metadata = data.get("metadata", {})

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "customer.subscription.created",
                "tenant_id unresolvable from metadata/subscription/customer",
            )
            return

        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            amount=amount,
            trial_end=trial_end,
        )
        if status == "trialing":
            subscription_lifecycle_service.mark_trial_started(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                trial_end=trial_end,
            )
        db.commit()
        logger.info(
            "Subscription created: %s (tenant: %s, lifecycle=%s)",
            subscription_id,
            tenant_id,
            lifecycle.get("change_type"),
        )

    except Exception as e:
        logger.error("Error handling subscription creation: %s", str(e))
        db.rollback()


async def handle_subscription_updated(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle subscription updates.

    SECURITY FIX (F-009): Previously updated by stripe_subscription_id only,
    without a tenant predicate. A subscription ID collision or replay attack
    could update the wrong tenant's subscription. Now resolves tenant_id first
    and includes it in the WHERE clause.
    """
    try:
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status") or "active"
        plan_id, amount = _extract_subscription_plan_and_amount(data)
        trial_end = _timestamp_to_datetime(data.get("trial_end"))
        metadata = data.get("metadata", {})

        # SECURITY (F-009): Resolve tenant to scope the UPDATE
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "customer.subscription.updated",
                "tenant_id unresolvable from metadata/subscription/customer",
            )
            return

        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            plan_id=plan_id,
            status=status,
            amount=amount,
            trial_end=trial_end,
        )
        db.commit()
        logger.info(
            "Subscription updated: %s to %s (tenant: %s, change=%s)",
            subscription_id,
            status,
            tenant_id,
            lifecycle.get("change_type"),
        )

    except Exception as e:
        logger.error("Error updating subscription: %s", str(e))
        db.rollback()


async def handle_subscription_deleted(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle subscription cancellation.

    SECURITY FIX (F-009): Previously updated by stripe_subscription_id only,
    without a tenant predicate. Now resolves tenant_id first and includes it
    in the WHERE clause to prevent cross-tenant writes.
    """
    try:
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        plan_id, amount = _extract_subscription_plan_and_amount(data)
        metadata = data.get("metadata", {})

        # SECURITY (F-009): Resolve tenant to scope the UPDATE
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "customer.subscription.deleted",
                "tenant_id unresolvable from metadata/subscription/customer",
            )
            return

        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            plan_id=plan_id,
            status="canceled",
            amount=amount,
            trial_end=None,
        )
        db.commit()
        logger.info(
            "Subscription canceled: %s (tenant: %s, change=%s)",
            subscription_id,
            tenant_id,
            lifecycle.get("change_type"),
        )

    except Exception as e:
        logger.error("Error canceling subscription: %s", str(e))
        db.rollback()


async def handle_payment_succeeded(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle successful payment"""
    try:
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        amount_paid = data.get("amount_paid", 0) / 100
        subscription_id = data.get("subscription")

        metadata = (
            data.get("subscription_details", {}).get("metadata", {})
            if data.get("subscription_details")
            else {}
        )

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "invoice.payment_succeeded",
                "tenant_id unresolvable from metadata/subscription/customer",
            )
            return

        # Record payment with tenant_id
        db.execute(
            text(
                """
            INSERT INTO payments (id, invoice_id, customer_id, amount, status, tenant_id, created_at)
            VALUES (:id, :invoice_id, :customer_id, :amount, 'succeeded', :tenant_id, NOW())
        """
            ),
            {
                "id": str(uuid.uuid4()),
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "amount": amount_paid,
                "tenant_id": tenant_id,
            },
        )

        # Update subscription payment date — now tenant-scoped
        if subscription_id:
            db.execute(
                text(
                    """
                    UPDATE subscriptions
                    SET last_payment_at = NOW()
                    WHERE stripe_subscription_id = :subscription_id
                      AND tenant_id = :tenant_id
                    """
                ),
                {"subscription_id": subscription_id, "tenant_id": tenant_id},
            )

            # Recover accounts from grace period after successful payment.
            subscription_lifecycle_service.upsert_subscription_state(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                customer_id=customer_id,
                plan_id=None,
                status="active",
                amount=amount_paid,
                trial_end=None,
            )

        # Track revenue for recurring subscription payments in mrg_revenue
        if subscription_id:
            db.execute(
                text(
                    """
                INSERT INTO mrg_revenue (
                    id, tenant_id, amount, currency, type, description,
                    stripe_invoice_id, status, created_at, paid_at, metadata
                )
                VALUES (
                    gen_random_uuid(), :tenant_id, :amount, 'USD', 'subscription', :description,
                    :invoice_id, 'completed', NOW(), NOW(),
                    jsonb_build_object('stripe_customer_id', :stripe_customer_id, 'stripe_subscription_id', :stripe_subscription_id)
                )
            """
                ),
                {
                    "tenant_id": tenant_id,
                    "amount": amount_paid,
                    "description": f"Subscription payment",
                    "invoice_id": invoice_id,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                },
            )

        db.commit()
        logger.info(
            f"Payment succeeded: {invoice_id} for ${amount_paid} (tenant: {tenant_id})"
        )

    except Exception as e:
        logger.error("Error handling payment success: %s", str(e))
        db.rollback()


async def handle_payment_failed(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle failed payment"""
    try:
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")

        metadata = (
            data.get("subscription_details", {}).get("metadata", {})
            if data.get("subscription_details")
            else {}
        )

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(
            db,
            metadata=metadata,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "invoice.payment_failed",
                "tenant_id unresolvable from metadata/subscription/customer",
            )
            return

        # Record failed payment
        db.execute(
            text(
                """
            INSERT INTO payment_failures (id, invoice_id, customer_id, subscription_id, tenant_id, created_at)
            VALUES (:id, :invoice_id, :customer_id, :subscription_id, :tenant_id, NOW())
        """
            ),
            {
                "id": str(uuid.uuid4()),
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
            },
        )

        # Mark subscription as past_due — now tenant-scoped
        if subscription_id:
            db.execute(
                text(
                    """
                    UPDATE subscriptions
                    SET status = 'past_due'
                    WHERE stripe_subscription_id = :subscription_id
                      AND tenant_id = :tenant_id
                    """
                ),
                {"subscription_id": subscription_id, "tenant_id": tenant_id},
            )

            subscription_lifecycle_service.upsert_subscription_state(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                customer_id=customer_id,
                plan_id=None,
                status="past_due",
                amount=None,
                trial_end=None,
            )

        db.commit()
        logger.warning(f"Payment failed: {invoice_id}")

    except Exception as e:
        logger.error("Error handling payment failure: %s", str(e))
        db.rollback()


async def handle_customer_created(db: Session, data: dict, stripe_event_id: str = ""):
    """Handle new customer creation"""
    try:
        customer_id = data.get("id")
        email = data.get("email")
        name = data.get("name")

        metadata = data.get("metadata", {})

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(
            db, metadata=metadata, customer_id=customer_id, customer_email=email
        )
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "customer.created",
                "tenant_id unresolvable from metadata/customer/email",
            )
            return

        if email:
            db.execute(
                text(
                    """
                INSERT INTO customers (id, email, name, stripe_customer_id, tenant_id, created_at)
                VALUES (:id, :email, :name, :stripe_id, :tenant_id, NOW())
                ON CONFLICT (email) DO UPDATE
                SET stripe_customer_id = :stripe_id, name = COALESCE(:name, name), tenant_id = COALESCE(customers.tenant_id, :tenant_id)
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "name": name,
                    "stripe_id": customer_id,
                    "tenant_id": tenant_id,
                },
            )
            db.commit()
            logger.info(f"Customer created: {email} (tenant: {tenant_id})")

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        db.rollback()


async def handle_payment_intent_succeeded(
    db: Session, data: dict, stripe_event_id: str = ""
):
    """Handle successful payment intent"""
    try:
        payment_intent_id = data.get("id")
        amount = data.get("amount", 0) / 100
        customer_id = data.get("customer")

        metadata = data.get("metadata", {})

        # SECURITY: Strict tenant resolution — no default fallback (removed MRG_DEFAULT_TENANT_ID)
        tenant_id = _resolve_tenant_id(db, metadata=metadata, customer_id=customer_id)
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "payment_intent.succeeded",
                "tenant_id unresolvable from metadata/customer",
            )
            return

        # Record one-time payment with tenant_id
        db.execute(
            text(
                """
            INSERT INTO payments (id, payment_intent_id, customer_id, amount, status, tenant_id, created_at)
            VALUES (:id, :payment_intent_id, :customer_id, :amount, 'succeeded', :tenant_id, NOW())
            ON CONFLICT (payment_intent_id) DO NOTHING
        """
            ),
            {
                "id": str(uuid.uuid4()),
                "payment_intent_id": payment_intent_id,
                "customer_id": customer_id,
                "amount": amount,
                "tenant_id": tenant_id,
            },
        )

        # Track one-time revenue in mrg_revenue
        product_key = metadata.get("product_key")

        db.execute(
            text(
                """
            INSERT INTO mrg_revenue (
                id, tenant_id, amount, currency, type, description,
                stripe_payment_intent_id, status, created_at, paid_at, metadata
            )
            VALUES (
                gen_random_uuid(), :tenant_id, :amount, 'USD', 'one_time', :description,
                :payment_intent_id, 'completed', NOW(), NOW(),
                jsonb_build_object('product_key', :product_key, 'stripe_customer_id', :stripe_customer_id)
            )
        """
            ),
            {
                "tenant_id": tenant_id,
                "amount": amount,
                "description": f"One-time payment: {product_key or 'MRG Product'}",
                "payment_intent_id": payment_intent_id,
                "product_key": product_key,
                "stripe_customer_id": customer_id,
            },
        )

        db.commit()
        logger.info(
            f"Payment intent succeeded: {payment_intent_id} for ${amount} (tenant: {tenant_id})"
        )

    except Exception as e:
        logger.error(f"Error handling payment intent: {str(e)}")
        db.rollback()


async def handle_payment_method_attached(db: Session, data: dict, stripe_event_id: str):
    """Handle payment method attachment"""
    try:
        payment_method_id = data.get("id")
        customer_id = data.get("customer")
        card_info = data.get("card", {})
        metadata = data.get("metadata", {})

        # SECURITY: Strict tenant resolution — no default fallback
        tenant_id = _resolve_tenant_id(db, metadata=metadata, customer_id=customer_id)
        if not tenant_id:
            _quarantine_webhook_event(
                db,
                stripe_event_id,
                "payment_method.attached",
                f"Cannot resolve tenant for customer {customer_id}",
            )
            return

        # Store payment method info
        db.execute(
            text(
                """
            INSERT INTO payment_methods (id, customer_id, tenant_id, type, last4, brand, created_at)
            VALUES (:id, :customer_id, :tenant_id, :type, :last4, :brand, NOW())
            ON CONFLICT (id) DO UPDATE
            SET customer_id = :customer_id, tenant_id = :tenant_id
        """
            ),
            {
                "id": payment_method_id,
                "customer_id": customer_id,
                "tenant_id": tenant_id,
                "type": data.get("type", "card"),
                "last4": card_info.get("last4"),
                "brand": card_info.get("brand"),
            },
        )
        db.commit()
        logger.info(
            f"Payment method attached: {payment_method_id} (tenant: {tenant_id})"
        )

    except Exception as e:
        logger.error(f"Error attaching payment method: {str(e)}")
        db.rollback()


@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "operational",
        "webhook_url": "https://brainops-backend-prod.onrender.com/api/v1/stripe/webhook",
        "instructions": "Configure this URL in Stripe Dashboard > Webhooks",
    }
