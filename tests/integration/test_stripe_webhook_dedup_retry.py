from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from starlette.requests import Request


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


def _build_request(payload: bytes, signature: str) -> Request:
    headers = [(b"stripe-signature", signature.encode("utf-8"))]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/stripe/webhook",
        "headers": headers,
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    received = False

    async def _receive():
        nonlocal received
        if received:
            return {"type": "http.request", "body": b"", "more_body": False}
        received = True
        return {"type": "http.request", "body": payload, "more_body": False}

    return Request(scope, _receive)


@pytest.mark.asyncio
async def test_webhook_event_deduplicates_after_success(monkeypatch):
    from routes import stripe_webhooks as mod

    db = _FakeStripeDB()
    event = {"id": "evt_dedup", "type": "unknown.event", "data": {"object": {}}}

    monkeypatch.setattr(mod, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(mod, "SessionLocal", lambda: _SessionCtx(db))
    monkeypatch.setattr(mod.stripe.Webhook, "construct_event", lambda *_args, **_kwargs: event)

    req_1 = _build_request(b"{}", "sig_test")
    req_2 = _build_request(b"{}", "sig_test")

    first = await mod.handle_stripe_webhook(req_1, stripe_signature="sig_test")
    second = await mod.handle_stripe_webhook(req_2, stripe_signature="sig_test")

    assert first["received"] is True
    assert second["duplicate"] is True


@pytest.mark.asyncio
async def test_webhook_retries_when_previous_attempt_failed(monkeypatch):
    from routes import stripe_webhooks as mod

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

    monkeypatch.setattr(mod, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(mod, "SessionLocal", lambda: _SessionCtx(db))
    monkeypatch.setattr(mod.stripe.Webhook, "construct_event", lambda *_args, **_kwargs: event)

    req = _build_request(b"{}", "sig_test")
    response = await mod.handle_stripe_webhook(req, stripe_signature="sig_test")

    assert response["received"] is True
    assert response["retry"] is True
    assert any(attempt["status"] == "processed" for attempt in db.attempts)
