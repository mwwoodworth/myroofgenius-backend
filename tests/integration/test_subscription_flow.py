from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _mk_result(
    *,
    first: Any = None,
    scalar: Any = None,
    mappings_first: Any = None,
):
    class _Result:
        def first(self):
            return first

        def scalar(self):
            return scalar

        def mappings(self):
            class _Map:
                def first(self_inner):
                    return mappings_first

            return _Map()

    return _Result()


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
                return _mk_result(mappings_first=sub)
            return _mk_result(mappings_first=None)

        if "SELECT status" in sql and "FROM subscriptions" in sql:
            sub = self.subscriptions.get(params.get("subscription_id"))
            if sub and sub.get("tenant_id") == params.get("tenant_id"):
                return _mk_result(scalar=sub.get("status"))
            return _mk_result(scalar=None)

        if "INSERT INTO subscription_usage_events" in sql:
            self.usage_events.append(dict(params))
            return _mk_result()

        # DDL and all other statements are no-ops in this fake.
        return _mk_result()

    def commit(self):
        return None

    def rollback(self):
        return None


def test_signup_subscribe_use_flow(monkeypatch):
    from routes import subscriptions as mod
    from core.supabase_auth import get_authenticated_user

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

    def _mark_trial_started(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        mod.subscription_lifecycle_service,
        "upsert_subscription_state",
        _upsert_subscription_state,
    )
    monkeypatch.setattr(
        mod.subscription_lifecycle_service,
        "mark_trial_started",
        _mark_trial_started,
    )

    app = FastAPI()
    app.include_router(mod.router)

    def _override_db():
        yield fake_db

    app.dependency_overrides[mod.get_db] = _override_db
    app.dependency_overrides[get_authenticated_user] = lambda: {
        "id": "user-1",
        "tenant_id": "tenant-1",
        "role": "admin",
    }

    client = TestClient(app)

    signup = client.post(
        "/api/v1/subscriptions/signup-trial",
        json={
            "tier": "professional",
            "stripe_subscription_id": "sub_123",
            "customer_id": "cus_123",
            "trial_days": 14,
        },
    )
    assert signup.status_code == 200
    assert signup.json()["status"] == "trialing"

    subscribe = client.post(
        "/api/v1/subscriptions/change-plan",
        json={
            "stripe_subscription_id": "sub_123",
            "target_tier": "business",
            "effective_immediately": True,
        },
    )
    assert subscribe.status_code == 200
    assert subscribe.json()["status"] == "active"

    usage = client.post(
        "/api/v1/subscriptions/usage",
        json={
            "stripe_subscription_id": "sub_123",
            "feature_key": "ai_analysis",
            "units": 3,
            "metadata": {"source": "test"},
        },
    )
    assert usage.status_code == 200
    assert usage.json()["status"] == "recorded"
    assert len(fake_db.usage_events) == 1
