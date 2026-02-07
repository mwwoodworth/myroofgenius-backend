import hashlib
import hmac
import json
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _sign(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


class _FakeConn:
    def __init__(self, inserted_sale_id: Optional[str]):
        self._inserted_sale_id = inserted_sale_id

    async def fetchval(self, *_args, **_kwargs):
        return self._inserted_sale_id


class _Acquire:
    def __init__(self, conn: _FakeConn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn):
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


@pytest.fixture
def gumroad_app(monkeypatch):
    from routes import gumroad_revenue as mod

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1/gumroad-revenue")

    return app, mod


def test_rejects_when_secret_missing(gumroad_app, monkeypatch):
    app, mod = gumroad_app
    monkeypatch.setattr(mod, "GUMROAD_WEBHOOK_SECRET", "")
    # Keep DB out of the equation for this test.
    monkeypatch.setattr(mod, "get_db_async", lambda: None)

    client = TestClient(app)
    resp = client.post("/api/v1/gumroad-revenue/webhook/gumroad", data=b"{}")
    assert resp.status_code == 503


def test_rejects_missing_or_invalid_signature(gumroad_app, monkeypatch):
    app, mod = gumroad_app
    secret = "test_secret"
    monkeypatch.setattr(mod, "GUMROAD_WEBHOOK_SECRET", secret)

    async def fake_get_db_async():
        return type("DB", (), {"pool": _FakePool(_FakeConn("SALE-1"))})()

    monkeypatch.setattr(mod, "get_db_async", fake_get_db_async)

    client = TestClient(app)

    payload = b'{"sale_id":"SALE-1","email":"x@example.com","product_name":"X"}'

    resp = client.post(
        "/api/v1/gumroad-revenue/webhook/gumroad",
        data=payload,
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 401

    resp = client.post(
        "/api/v1/gumroad-revenue/webhook/gumroad",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-gumroad-signature": "not-a-real-signature",
        },
    )
    assert resp.status_code == 401


def test_records_sale_and_queues_automations_once(gumroad_app, monkeypatch):
    app, mod = gumroad_app
    secret = "test_secret"
    monkeypatch.setattr(mod, "GUMROAD_WEBHOOK_SECRET", secret)

    calls = {"convertkit": 0, "sendgrid": 0}

    async def fake_add_to_convertkit(*_args, **_kwargs):
        calls["convertkit"] += 1

    async def fake_send_purchase_email(*_args, **_kwargs):
        calls["sendgrid"] += 1

    monkeypatch.setattr(mod, "add_to_convertkit", fake_add_to_convertkit)
    monkeypatch.setattr(mod, "send_purchase_email", fake_send_purchase_email)

    async def fake_get_db_async():
        return type("DB", (), {"pool": _FakePool(_FakeConn("SALE-1"))})()

    monkeypatch.setattr(mod, "get_db_async", fake_get_db_async)

    payload_obj = {
        "sale_id": "SALE-1",
        "email": "buyer@example.com",
        "full_name": "Buyer One",
        "product_name": "Commercial Roofing Intelligence Bundle",
        "product_permalink": "gr-roofint",
        "price": "9700",
        "currency": "USD",
    }
    payload = json.dumps(payload_obj, separators=(",", ":")).encode("utf-8")
    signature = _sign(secret, payload)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/gumroad-revenue/webhook/gumroad",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-gumroad-signature": signature,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["sale_id"] == "SALE-1"
    assert calls == {"convertkit": 1, "sendgrid": 1}


def test_duplicate_sale_is_idempotent(gumroad_app, monkeypatch):
    app, mod = gumroad_app
    secret = "test_secret"
    monkeypatch.setattr(mod, "GUMROAD_WEBHOOK_SECRET", secret)

    calls = {"convertkit": 0, "sendgrid": 0}

    async def fake_add_to_convertkit(*_args, **_kwargs):
        calls["convertkit"] += 1

    async def fake_send_purchase_email(*_args, **_kwargs):
        calls["sendgrid"] += 1

    monkeypatch.setattr(mod, "add_to_convertkit", fake_add_to_convertkit)
    monkeypatch.setattr(mod, "send_purchase_email", fake_send_purchase_email)

    async def fake_get_db_async():
        # Simulate ON CONFLICT DO NOTHING: RETURNING sale_id => None
        return type("DB", (), {"pool": _FakePool(_FakeConn(None))})()

    monkeypatch.setattr(mod, "get_db_async", fake_get_db_async)

    payload_obj = {
        "sale_id": "SALE-1",
        "email": "buyer@example.com",
        "full_name": "Buyer One",
        "product_name": "Commercial Roofing Intelligence Bundle",
        "product_permalink": "gr-roofint",
        "price": "9700",
        "currency": "USD",
    }
    payload = json.dumps(payload_obj, separators=(",", ":")).encode("utf-8")
    signature = _sign(secret, payload)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/gumroad-revenue/webhook/gumroad",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-gumroad-signature": signature,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "duplicate"
    assert body["sale_id"] == "SALE-1"
    assert calls == {"convertkit": 0, "sendgrid": 0}

