"""Subscription lifecycle service for trial/grace/upgrade flows."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SubscriptionLifecycleService:
    """Handles subscription lifecycle transitions with tenant scoping."""

    def __init__(self, grace_period_days: int = 7):
        self.grace_period_days = max(1, grace_period_days)
        self._subscriptions_columns: Optional[Set[str]] = None
        self._lifecycle_tables_ready = False

    def _ensure_lifecycle_tables(self, db: Session) -> None:
        if self._lifecycle_tables_ready:
            return
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS subscription_lifecycle_events (
                    id UUID PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    stripe_subscription_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    from_plan_id VARCHAR(255),
                    to_plan_id VARCHAR(255),
                    from_amount NUMERIC,
                    to_amount NUMERIC,
                    details JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_subscription_lifecycle_events_lookup
                    ON subscription_lifecycle_events(tenant_id, stripe_subscription_id, created_at DESC)
                """
            )
        )
        self._lifecycle_tables_ready = True

    def _get_subscription_columns(self, db: Session) -> Set[str]:
        if self._subscriptions_columns is not None:
            return self._subscriptions_columns

        rows = db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'subscriptions'
                """
            )
        ).fetchall()
        self._subscriptions_columns = {row[0] for row in rows}
        return self._subscriptions_columns

    def _to_decimal(self, amount: Optional[float]) -> Optional[Decimal]:
        if amount is None:
            return None
        return Decimal(str(amount))

    def _determine_change_type(
        self,
        previous_plan_id: Optional[str],
        next_plan_id: Optional[str],
        previous_amount: Optional[Decimal],
        next_amount: Optional[Decimal],
    ) -> Optional[str]:
        if not previous_plan_id or not next_plan_id:
            return None
        if previous_plan_id == next_plan_id:
            return None

        if previous_amount is None or next_amount is None:
            return "plan_change"

        if next_amount > previous_amount:
            return "upgrade"
        if next_amount < previous_amount:
            return "downgrade"
        return "plan_change"

    def _record_lifecycle_event(
        self,
        db: Session,
        *,
        tenant_id: str,
        subscription_id: str,
        event_type: str,
        from_plan_id: Optional[str],
        to_plan_id: Optional[str],
        from_amount: Optional[Decimal],
        to_amount: Optional[Decimal],
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._ensure_lifecycle_tables(db)
        db.execute(
            text(
                """
                INSERT INTO subscription_lifecycle_events (
                    id, tenant_id, stripe_subscription_id, event_type,
                    from_plan_id, to_plan_id, from_amount, to_amount, details, created_at
                ) VALUES (
                    :id, :tenant_id, :subscription_id, :event_type,
                    :from_plan_id, :to_plan_id, :from_amount, :to_amount, :details, NOW()
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "subscription_id": subscription_id,
                "event_type": event_type,
                "from_plan_id": from_plan_id,
                "to_plan_id": to_plan_id,
                "from_amount": from_amount,
                "to_amount": to_amount,
                "details": json.dumps(details or {}),
            },
        )

    def upsert_subscription_state(
        self,
        db: Session,
        *,
        tenant_id: str,
        subscription_id: str,
        customer_id: Optional[str],
        plan_id: Optional[str],
        status: str,
        amount: Optional[float],
        trial_end: Optional[datetime],
    ) -> Dict[str, Any]:
        """Apply subscription state from Stripe and return lifecycle metadata."""
        columns = self._get_subscription_columns(db)

        select_fields = ["plan_id", "amount", "status"]
        if "trial_ends_at" in columns:
            select_fields.append("trial_ends_at")
        if "grace_period_ends_at" in columns:
            select_fields.append("grace_period_ends_at")

        previous = db.execute(
            text(
                f"""
                SELECT {', '.join(select_fields)}
                FROM subscriptions
                WHERE stripe_subscription_id = :subscription_id
                  AND tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"subscription_id": subscription_id, "tenant_id": tenant_id},
        ).mappings().first()

        previous_plan_id = previous.get("plan_id") if previous else None
        previous_amount = self._to_decimal(previous.get("amount") if previous else None)
        next_amount = self._to_decimal(amount)
        change_type = self._determine_change_type(
            previous_plan_id,
            plan_id,
            previous_amount,
            next_amount,
        )

        now = datetime.now(timezone.utc)
        grace_until = None
        if status in {"past_due", "unpaid"}:
            grace_until = now + timedelta(days=self.grace_period_days)

        insert_fields = ["id", "stripe_subscription_id", "tenant_id", "status", "created_at"]
        params: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "stripe_subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "status": status,
            "created_at": now,
        }

        if "customer_id" in columns:
            insert_fields.append("customer_id")
            params["customer_id"] = customer_id

        if "plan_id" in columns:
            insert_fields.append("plan_id")
            params["plan_id"] = plan_id

        if "amount" in columns:
            insert_fields.append("amount")
            params["amount"] = amount

        if "trial_ends_at" in columns:
            insert_fields.append("trial_ends_at")
            params["trial_ends_at"] = trial_end

        if "grace_period_ends_at" in columns:
            insert_fields.append("grace_period_ends_at")
            params["grace_period_ends_at"] = grace_until

        if "updated_at" in columns:
            insert_fields.append("updated_at")
            params["updated_at"] = now

        if "lifecycle_stage" in columns:
            lifecycle_stage = "active"
            if status == "trialing":
                lifecycle_stage = "trial"
            elif status in {"past_due", "unpaid"}:
                lifecycle_stage = "grace"
            elif status in {"canceled", "cancelled"}:
                lifecycle_stage = "canceled"
            insert_fields.append("lifecycle_stage")
            params["lifecycle_stage"] = lifecycle_stage

        placeholders = [f":{field}" for field in insert_fields]

        update_fields = ["status", "tenant_id"]
        if "customer_id" in columns:
            update_fields.append("customer_id")
        if "plan_id" in columns:
            update_fields.append("plan_id")
        if "amount" in columns:
            update_fields.append("amount")
        if "trial_ends_at" in columns:
            update_fields.append("trial_ends_at")
        if "grace_period_ends_at" in columns:
            update_fields.append("grace_period_ends_at")
        if "lifecycle_stage" in columns:
            update_fields.append("lifecycle_stage")
        if "updated_at" in columns:
            update_fields.append("updated_at")

        update_clause = ", ".join([f"{field} = EXCLUDED.{field}" for field in update_fields])

        db.execute(
            text(
                f"""
                INSERT INTO subscriptions ({', '.join(insert_fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (stripe_subscription_id) DO UPDATE
                SET {update_clause}
                """
            ),
            params,
        )

        if change_type:
            self._record_lifecycle_event(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                event_type=change_type,
                from_plan_id=previous_plan_id,
                to_plan_id=plan_id,
                from_amount=previous_amount,
                to_amount=next_amount,
                details={"status": status},
            )

        if status in {"past_due", "unpaid"}:
            self._record_lifecycle_event(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                event_type="grace_period_started",
                from_plan_id=previous_plan_id,
                to_plan_id=plan_id,
                from_amount=previous_amount,
                to_amount=next_amount,
                details={"grace_until": grace_until.isoformat() if grace_until else None},
            )

        if status == "active" and previous and previous.get("status") in {"past_due", "unpaid"}:
            self._record_lifecycle_event(
                db,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                event_type="grace_period_recovered",
                from_plan_id=previous_plan_id,
                to_plan_id=plan_id,
                from_amount=previous_amount,
                to_amount=next_amount,
            )

        return {
            "change_type": change_type,
            "grace_until": grace_until,
            "status": status,
        }

    def mark_trial_started(
        self,
        db: Session,
        *,
        tenant_id: str,
        subscription_id: str,
        trial_end: Optional[datetime],
    ) -> None:
        self._record_lifecycle_event(
            db,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            event_type="trial_started",
            from_plan_id=None,
            to_plan_id=None,
            from_amount=None,
            to_amount=None,
            details={"trial_end": trial_end.isoformat() if trial_end else None},
        )


subscription_lifecycle_service = SubscriptionLifecycleService()
