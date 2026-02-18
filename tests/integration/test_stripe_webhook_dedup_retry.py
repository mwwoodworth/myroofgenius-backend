from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient


class _Result:
    def __init__(self, first_value: Any = None):
        self._first_value = first_value

    def first(self):
        return self._first_value


@dataclass
class _FakeStripeDB:
    webhook_events: set
    attempts: List[Dict[str, Any]]

    def __init__(self):
        self.webhook_events = set()
        self.attempts = []

    def execute(self, query, params: Optional[Dict[str, Any]] = None):
        sql = str(query).lower()
        params = params or {}

        if "insert into webhook_events" in sql:
            event_id = params.get("stripe_event_id")
            if event_id in self.webhook_events:
                return _Result(None)
            self.webhook_events.add(event_id)
            return _Result(SimpleNamespace(stripe_event_id=event_id))

        if "select status" in sql and "from webhook_event_attempts" in sql:
            event_id = params.get("stripe_event_id")
            found = [row for row in self.attempts if row["stripe_event_id"] == event_id]
            if not found:
                return _Result(None)
            return _Result(SimpleNamespace(status=found[-1]["status"]))

        if "select coalesce(max(attempt_no)" in sql:
            event_id = params.get("stripe_event_id")
            matching = [row["attempt_no"] for row in self.attempts if row["stripe_event_id"] == event_id]
            return _Result(SimpleNamespace(last_attempt=max(matching) if matching else 0))

        if "insert into webhook_event_attempts" in sql:
            self.attempts.append(
                {
                    "stripe_event_id": params.get("stripe_event_id"),
                    "event_type": params.get("event_type"),
                    "attempt_no": params.get("attempt_no"),
                    "status": params.get("status"),
                    "error_message": params.get("error_message"),
                }
            )
            return _Result(None)

        # DDL and indexes are no-ops.
        return _Result(None)

    def commit(self):
        return None

    def rollback(self):
        return None


class _SessionCtx:
    def __init__(self, db: _FakeStripeDB):
        self._db = db

    def __enter__(self):
        return self._db

    def __exit__(self, exc_type, exc, tb):
        return False


def _build_client(monkeypatch, db: _FakeStripeDB, event_payload: Dict[str, Any]) -> TestClient:
    from routes import stripe_webhooks as mod

    monkeypatch.setattr(mod, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(mod, "SessionLocal", lambda: _SessionCtx(db))
    monkeypatch.setattr(mod.stripe.Webhook, "construct_event", lambda *_args, **_kwargs: event_payload)

    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app)


def test_webhook_event_deduplicates_after_success(monkeypatch):
    db = _FakeStripeDB()
    event = {"id": "evt_dedup", "type": "unknown.event", "data": {"object": {}}}
    client = _build_client(monkeypatch, db, event)

    first = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "sig_test"},
    )
    second = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "sig_test"},
    )

    assert first.status_code == 200
    assert first.json()["received"] is True

    assert second.status_code == 200
    assert second.json()["duplicate"] is True


def test_webhook_retries_when_previous_attempt_failed(monkeypatch):
    db = _FakeStripeDB()
    db.webhook_events.add("evt_retry")
    db.attempts.append(
        {
            "stripe_event_id": "evt_retry",
            "event_type": "unknown.event",
            "attempt_no": 1,
            "status": "failed",
            "error_message": "transient",
        }
    )

    event = {"id": "evt_retry", "type": "unknown.event", "data": {"object": {}}}
    client = _build_client(monkeypatch, db, event)

    response = client.post(
        "/api/v1/stripe/webhook",
        data=b"{}",
        headers={"stripe-signature": "sig_test"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["received"] is True
    assert body["retry"] is True

    # Ensure a successful processed attempt was recorded after the retry.
    assert any(attempt["status"] == "processed" for attempt in db.attempts)
