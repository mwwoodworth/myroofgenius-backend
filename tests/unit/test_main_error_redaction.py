from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from main import _http_exception_handler


def _build_request(path: str = "/test") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, _receive)


@pytest.mark.asyncio
async def test_http_500_is_redacted():
    response = await _http_exception_handler(
        _build_request(),
        HTTPException(status_code=500, detail="sqlalchemy.OperationalError: relation missing"),
    )

    assert response.status_code == 500
    assert b"Internal server error" in response.body


@pytest.mark.asyncio
async def test_http_400_internal_markers_are_redacted():
    response = await _http_exception_handler(
        _build_request(),
        HTTPException(status_code=400, detail="OperationalError: invalid input syntax for uuid"),
    )

    assert response.status_code == 400
    assert b"Bad request" in response.body


@pytest.mark.asyncio
async def test_http_400_user_message_is_preserved():
    response = await _http_exception_handler(
        _build_request(),
        HTTPException(status_code=400, detail="Invalid lead ID"),
    )

    assert response.status_code == 400
    assert b"Invalid lead ID" in response.body
