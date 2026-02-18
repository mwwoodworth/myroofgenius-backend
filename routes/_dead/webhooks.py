"""
Webhook handlers for external integrations.

Goals:
- Keep public webhook endpoints lightweight and safe.
- Avoid drift by delegating Stripe verification + processing to the canonical
  handler in routes/stripe_webhooks.py.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Header, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Webhooks"])


async def _safe_json(request: Request) -> Dict[str, Any]:
    body = await request.body()
    if not body:
        return {}
    try:
        return await request.json()
    except Exception:
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return {}


@router.post("/revenue/webhook")
async def handle_revenue_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle generic revenue webhook events (non-Stripe)."""
    try:
        payload = await _safe_json(request)
        logger.info("Revenue webhook received: %s", payload.get("type", "unknown"))
        background_tasks.add_task(process_revenue_event, payload)
    except Exception:
        logger.exception("Revenue webhook error")

    # Always return success to prevent retry storms from external providers.
    return {"status": "received"}


async def process_revenue_event(payload: Dict[str, Any]) -> None:
    """Process revenue event in background."""
    try:
        event_type = payload.get("type", "unknown")

        if event_type == "payment_intent.succeeded":
            logger.info("Payment succeeded: %s", payload.get("id"))
        elif event_type == "customer.created":
            logger.info("Customer created: %s", payload.get("id"))
        else:
            logger.info("Unhandled revenue event type: %s", event_type)
    except Exception:
        logger.exception("Error processing revenue event")


@router.post("/webhooks/stripe")
async def handle_stripe_webhook_alias(
    request: Request,
    stripe_signature: Optional[str] = Header(default=None),
):
    """Stripe webhook compatibility endpoint (signature verified)."""
    # Delegate to the canonical Stripe handler so /api/v1/webhooks/stripe and
    # /api/v1/stripe/webhook behave identically.
    from routes import stripe_webhooks as stripe_webhooks_routes

    return await stripe_webhooks_routes.handle_stripe_webhook(
        request=request,
        stripe_signature=stripe_signature,
    )

