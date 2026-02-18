from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from middleware.authentication import AuthenticationMiddleware


def _build_request(path: str, headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers or [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, _receive)


@pytest.mark.asyncio
async def test_middleware_allows_exempt_health_path(monkeypatch):
    middleware = AuthenticationMiddleware(app=lambda scope, receive, send: None)

    request = _build_request("/health")

    async def call_next(_request):
        return JSONResponse({"ok": True}, status_code=200)

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_middleware_blocks_protected_path_without_auth(monkeypatch):
    middleware = AuthenticationMiddleware(app=lambda scope, receive, send: None)

    async def _raise_missing_auth(*_args, **_kwargs):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    monkeypatch.setattr("middleware.authentication.get_current_user", _raise_missing_auth)

    request = _build_request("/api/v1/private")

    async def call_next(_request):
        return JSONResponse({"ok": True}, status_code=200)

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 401
    assert b"Missing authorization header" in response.body
