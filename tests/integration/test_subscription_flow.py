from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class _Result:
    def __init__(self, *, first=None, scalar=None, mappings_first=None):
        self._first = first
        self._scalar = scalar
        self._mappings_first = mappings_first

    def first(self):
        return self._first

    def scalar(self):
        return self._scalar

    def mappings(self):
        class _Mappings:
            def __init__(self, row):
                self._row = row

            def first(self):
                return self._row

        return _Mappings(self._mappings_first)


@dataclass
class _FakeDB:
    subscriptions: Dict[str, Dict[str, Any]]

    def __init__(self):
        self.subscriptions = {}
        self.usage_events = []

    def execute(self, query, params: Optional[Dict[str, Any]] = None):
        sql = str(query)
        params = params or {}

        if "SELECT *" in sql and "FROM subscriptions" in sql:
            sub = self.subscriptions.get(params.get("subscription_id"))
            if sub and sub.get("tenant_id") == params.get("tenant_id"):
                return _Result(mappings_first=sub)
            return _Result(mappings_first=None)

        if "SELECT status" in sql and "FROM subscriptions" in sql:
            sub = self.subscriptions.get(params.get("subscription_id"))
            if sub and sub.get("tenant_id") == params.get("tenant_id"):
                return _Result(scalar=sub.get("status"))
            return _Result(scalar=None)

        if "INSERT INTO subscription_usage_events" in sql:
            self.usage_events.append(dict(params))
            return _Result()

        return _Result()

    def commit(self):
        return None

    def rollback(self):
        return None


def test_signup_subscribe_use_flow(monkeypatch):
    from routes import subscriptions as mod

    fake_db = _FakeDB()

    def _upsert_subscription_state(
        db,
        *,
        tenant_id,
        subscription_id,
        customer_id,
        plan_id,
        status,
        amount,
        trial_end,
    ):
        previous = fake_db.subscriptions.get(subscription_id, {})
        fake_db.subscriptions[subscription_id] = {
            **previous,
            "tenant_id": tenant_id,
            "stripe_subscription_id": subscription_id,
            "status": status,
            "plan_id": plan_id,
            "amount": amount,
            "trial_end": trial_end,
        }
        return {"change_type": "upgrade" if previous else None, "grace_until": None}

    monkeypatch.setattr(
        mod.subscription_lifecycle_service,
        "upsert_subscription_state",
        _upsert_subscription_state,
    )
    monkeypatch.setattr(
        mod.subscription_lifecycle_service,
        "mark_trial_started",
        lambda *_args, **_kwargs: None,
    )

    user = {"id": "user-1", "tenant_id": "tenant-1", "role": "admin"}

    signup = mod.signup_trial(
        mod.TrialSignupRequest(
            tier=mod.SubscriptionTier.PROFESSIONAL,
            stripe_subscription_id="sub_123",
            customer_id="cus_123",
            trial_days=14,
        ),
        db=fake_db,
        current_user=user,
    )
    assert signup["status"] == "trialing"

    subscribe = mod.change_plan(
        mod.PlanChangeRequest(
            stripe_subscription_id="sub_123",
            target_tier=mod.SubscriptionTier.BUSINESS,
            effective_immediately=True,
        ),
        db=fake_db,
        current_user=user,
    )
    assert subscribe["status"] == "active"

    usage = mod.record_usage(
        mod.UsageEventRequest(
            stripe_subscription_id="sub_123",
            feature_key="ai_analysis",
            units=3,
            metadata={"source": "test"},
        ),
        db=fake_db,
        current_user=user,
    )
    assert usage["status"] == "recorded"
    assert len(fake_db.usage_events) == 1
