import os

# Ensure required environment variables are present for import-time validation.
os.environ.setdefault("DATABASE_URL", "postgresql://user:<DB_PASSWORD_REDACTED>@localhost:5432/testdb")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

from typing import Any, Optional

import types
import sys

settings_stub = types.SimpleNamespace(
    RATE_LIMIT_REQUESTS=100,
    RATE_LIMIT_PERIOD=60,
    is_production=False,
    redis_url=None,
)
sys.modules.setdefault("app.core.config", types.SimpleNamespace(settings=settings_stub))

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from middleware.authentication import AuthenticationMiddleware
from app.middleware.security import APIKeyMiddleware
from app.core.exceptions import AuthenticationError


@pytest.fixture(scope="session")
def db_connection():
    """Stub database connection used by autouse fixtures if invoked."""

    class DummyCursor:
        def execute(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - no-op
            return None

        def close(self) -> None:  # pragma: no cover - no-op
            return None

    class DummyConnection:
        def cursor(self) -> DummyCursor:
            return DummyCursor()

        def rollback(self) -> None:  # pragma: no cover - no-op
            return None

        def close(self) -> None:  # pragma: no cover - no-op
            return None

    return DummyConnection()


@pytest.fixture(autouse=True)
def patch_get_current_user(monkeypatch):
    """Replace Supabase user lookup with a fast local stub."""

    async def _fake_get_current_user(authorization: Optional[str] = None, **_: Any):
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        return {"id": "test-user", "tenant_id": "tenant-123"}

    monkeypatch.setattr(
        "middleware.authentication.get_current_user",
        _fake_get_current_user,
    )


def _build_app_with_auth(route_path: str, method: str = "GET"):
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)

    async def _handler(request: Request):
        return {"ok": True, "path": request.url.path}

    if method == "POST":
        app.post(route_path)(_handler)
    else:
        app.get(route_path)(_handler)

    return app


def _build_api_key_test_app(pool, **middleware_kwargs):
    app = FastAPI()
    app.state.db_pool = pool
    app.state.settings = types.SimpleNamespace(is_production=False)
    app.add_middleware(APIKeyMiddleware, **middleware_kwargs)

    @app.exception_handler(AuthenticationError)
    async def _handle_auth_error(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    return app


def test_authentication_blocks_protected_route_without_token():
    app = _build_app_with_auth("/api/v1/protected")
    client = TestClient(app)

    response = client.get("/api/v1/protected")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization header"


def test_authentication_allows_reviewed_webhook_without_token():
    app = _build_app_with_auth("/api/v1/stripe/webhook", method="POST")
    client = TestClient(app)

    response = client.post("/api/v1/stripe/webhook", json={"event": "test"})

    assert response.status_code == 200
    assert response.json()["path"] == "/api/v1/stripe/webhook"


class _FakeAcquire:
    def __init__(self, connection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return _FakeAcquire(self.connection)


class _CachingConnection:
    def __init__(self):
        self.queries = []

    async def fetchrow(self, query: str, *_: Any):
        self.queries.append(query.strip())
        if "key_hash" in query:
            return {"id": "cached-key", "expires_at": None}
        if "id = $1" in query:
            return {"expires_at": None}
        return None


def test_api_key_middleware_caches_valid_keys(monkeypatch):
    connection = _CachingConnection()
    pool = _FakePool(connection)

    app = _build_api_key_test_app(
        pool,
        cache_ttl_seconds=120,
        usage_touch_interval_seconds=60,
        public_paths=(),
    )

    @app.get("/secure")
    async def secure_endpoint(request: Request):
        return {"api_key_id": getattr(request.state, "api_key_id", None)}

    client = TestClient(app)
    headers = {"Authorization": "Bearer " + "x" * 32}

    first = client.get("/secure", headers=headers)
    second = client.get("/secure", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["api_key_id"] == "cached-key"
    # Only the initial validation should hit the database.
    assert len(connection.queries) == 1


class _RevokingConnection:
    def __init__(self):
        self.key_hash_calls = 0
        self.id_calls = 0

    async def fetchrow(self, query: str, *_: Any):
        if "key_hash" in query:
            self.key_hash_calls += 1
            if self.key_hash_calls == 1:
                return {"id": "revoked-key", "expires_at": None}
            return None

        if "id = $1" in query:
            self.id_calls += 1
            return None

        return None


def _time_sequence(*values: float):
    iterator = iter(values)
    last = values[-1]

    def _time():
        nonlocal last
        try:
            last = next(iterator)
        except StopIteration:
            pass
        return last

    return _time


@pytest.mark.asyncio
async def test_api_key_middleware_revokes_cached_key(monkeypatch):
    connection = _RevokingConnection()
    pool = _FakePool(connection)

    monkeypatch.setattr(
        "app.middleware.security.time.time",
        _time_sequence(1000.0, 1001.0, 1003.0),
    )

    middleware = APIKeyMiddleware(
        FastAPI(),
        cache_ttl_seconds=60,
        usage_touch_interval_seconds=2,
        public_paths=(),
    )

    key = "y" * 32

    first = await middleware._validate_api_key(key, pool)
    second = await middleware._validate_api_key(key, pool)
    third = await middleware._validate_api_key(key, pool)

    assert first is not None
    assert second is first
    assert third is None
    assert connection.key_hash_calls == 2
    assert connection.id_calls == 1
