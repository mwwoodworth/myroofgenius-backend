"""Subscription management routes with tenant-scoped lifecycle tracking."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.request_safety import require_tenant_id, sanitize_text
from core.supabase_auth import get_authenticated_user
from database import get_db
from services.subscription_lifecycle import subscription_lifecycle_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


class SubscriptionTier(str, Enum):
    FREE = "free"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


TIER_PRICE_MAP = {
    SubscriptionTier.FREE: 0.0,
    SubscriptionTier.PROFESSIONAL: 97.0,
    SubscriptionTier.BUSINESS: 297.0,
    SubscriptionTier.ENTERPRISE: 997.0,
}

TIER_PLAN_MAP = {
    SubscriptionTier.FREE: "plan_free",
    SubscriptionTier.PROFESSIONAL: "plan_professional",
    SubscriptionTier.BUSINESS: "plan_business",
    SubscriptionTier.ENTERPRISE: "plan_enterprise",
}


class TrialSignupRequest(BaseModel):
    tier: SubscriptionTier = SubscriptionTier.PROFESSIONAL
    stripe_subscription_id: str = Field(..., min_length=3, max_length=255)
    customer_id: Optional[str] = Field(default=None, max_length=255)
    trial_days: int = Field(default=14, ge=1, le=60)


class PlanChangeRequest(BaseModel):
    stripe_subscription_id: str = Field(..., min_length=3, max_length=255)
    target_tier: SubscriptionTier
    effective_immediately: bool = True


class GracePeriodRequest(BaseModel):
    stripe_subscription_id: str = Field(..., min_length=3, max_length=255)
    days: int = Field(default=7, ge=1, le=30)


class UsageEventRequest(BaseModel):
    stripe_subscription_id: str = Field(..., min_length=3, max_length=255)
    feature_key: str = Field(..., min_length=1, max_length=120)
    units: int = Field(default=1, ge=1, le=100000)
    metadata: Optional[Dict[str, Any]] = None


def _ensure_usage_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS subscription_usage_events (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                stripe_subscription_id VARCHAR(255) NOT NULL,
                feature_key VARCHAR(120) NOT NULL,
                units INTEGER NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_subscription_usage_tenant_sub
            ON subscription_usage_events(tenant_id, stripe_subscription_id, created_at DESC)
            """
        )
    )


@router.get("/tiers")
def get_subscription_tiers() -> Dict[str, Any]:
    return {
        "tiers": [
            {
                "id": tier.value,
                "price": TIER_PRICE_MAP[tier],
                "plan_id": TIER_PLAN_MAP[tier],
            }
            for tier in SubscriptionTier
        ]
    }


@router.post("/signup-trial")
def signup_trial(
    payload: TrialSignupRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    tenant_id = require_tenant_id(current_user)

    try:
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=payload.trial_days)

        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=sanitize_text(payload.stripe_subscription_id, max_length=255) or "",
            customer_id=sanitize_text(payload.customer_id, max_length=255),
            plan_id=TIER_PLAN_MAP[payload.tier],
            status="trialing",
            amount=TIER_PRICE_MAP[payload.tier],
            trial_end=trial_end,
        )
        subscription_lifecycle_service.mark_trial_started(
            db,
            tenant_id=tenant_id,
            subscription_id=payload.stripe_subscription_id,
            trial_end=trial_end,
        )
        db.commit()

        return {
            "status": "trialing",
            "trial_end": trial_end.isoformat(),
            "tier": payload.tier.value,
            "lifecycle": {
                "change_type": lifecycle.get("change_type"),
                "grace_until": lifecycle.get("grace_until").isoformat() if lifecycle.get("grace_until") else None,
            },
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("subscription.signup_trial failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/change-plan")
def change_plan(
    payload: PlanChangeRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    tenant_id = require_tenant_id(current_user)

    try:
        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=sanitize_text(payload.stripe_subscription_id, max_length=255) or "",
            customer_id=None,
            plan_id=TIER_PLAN_MAP[payload.target_tier],
            status="active",
            amount=TIER_PRICE_MAP[payload.target_tier],
            trial_end=None,
        )
        db.commit()

        return {
            "status": "active",
            "tier": payload.target_tier.value,
            "effective_immediately": payload.effective_immediately,
            "change_type": lifecycle.get("change_type") or "no_change",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("subscription.change_plan failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/grace-period")
def start_grace_period(
    payload: GracePeriodRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    tenant_id = require_tenant_id(current_user)

    try:
        original_days = subscription_lifecycle_service.grace_period_days
        subscription_lifecycle_service.grace_period_days = payload.days
        lifecycle = subscription_lifecycle_service.upsert_subscription_state(
            db,
            tenant_id=tenant_id,
            subscription_id=sanitize_text(payload.stripe_subscription_id, max_length=255) or "",
            customer_id=None,
            plan_id=None,
            status="past_due",
            amount=None,
            trial_end=None,
        )
        subscription_lifecycle_service.grace_period_days = original_days
        db.commit()
        return {
            "status": "past_due",
            "grace_until": lifecycle.get("grace_until").isoformat() if lifecycle.get("grace_until") else None,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("subscription.grace_period failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/current/{stripe_subscription_id}")
def get_current_subscription(
    stripe_subscription_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    tenant_id = require_tenant_id(current_user)

    row = db.execute(
        text(
            """
            SELECT *
            FROM subscriptions
            WHERE stripe_subscription_id = :subscription_id
              AND tenant_id = :tenant_id
            LIMIT 1
            """
        ),
        {
            "subscription_id": sanitize_text(stripe_subscription_id, max_length=255),
            "tenant_id": tenant_id,
        },
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Subscription not found")

    serialized = {}
    for key, value in dict(row).items():
        if isinstance(value, uuid.UUID):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


@router.post("/usage")
def record_usage(
    payload: UsageEventRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    tenant_id = require_tenant_id(current_user)

    try:
        _ensure_usage_table(db)

        active_status = db.execute(
            text(
                """
                SELECT status
                FROM subscriptions
                WHERE stripe_subscription_id = :subscription_id
                  AND tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {
                "subscription_id": sanitize_text(payload.stripe_subscription_id, max_length=255),
                "tenant_id": tenant_id,
            },
        ).scalar()

        if active_status is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if str(active_status).lower() in {"canceled", "cancelled", "unpaid"}:
            raise HTTPException(status_code=402, detail="Subscription is not active")

        event_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO subscription_usage_events (
                    id, tenant_id, stripe_subscription_id, feature_key, units, metadata, created_at
                ) VALUES (
                    :id, :tenant_id, :subscription_id, :feature_key, :units, :metadata::jsonb, NOW()
                )
                """
            ),
            {
                "id": event_id,
                "tenant_id": tenant_id,
                "subscription_id": sanitize_text(payload.stripe_subscription_id, max_length=255),
                "feature_key": sanitize_text(payload.feature_key, max_length=120),
                "units": payload.units,
                "metadata": json.dumps(payload.metadata or {}),
            },
        )
        db.commit()

        return {
            "event_id": event_id,
            "status": "recorded",
            "feature_key": payload.feature_key,
            "units": payload.units,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("subscription.record_usage failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal server error")
