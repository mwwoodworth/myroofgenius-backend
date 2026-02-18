from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.security import APIKeyMiddleware


def test_api_key_rotation_accepts_previous_internal_key(monkeypatch):
    monkeypatch.setenv("BACKEND_INTERNAL_API_KEY", "active-key-1234567890")
    monkeypatch.setenv("BACKEND_INTERNAL_API_KEY_PREVIOUS", "prev-key-1234567890")

    app = FastAPI()
    app.state.db_pool = None
    app.add_middleware(APIKeyMiddleware, public_paths=())

    @app.get("/secure")
    async def secure_endpoint(request: Request):
        return {
            "ok": True,
            "api_key_id": getattr(request.state, "api_key_id", None),
        }

    client = TestClient(app)

    response = client.get("/secure", headers={"X-API-Key": "prev-key-1234567890"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["api_key_id"] == "internal"
