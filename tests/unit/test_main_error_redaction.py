from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from main import _http_exception_handler, _unhandled_exception_handler


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)

    @app.get("/error-500")
    async def error_500():
        raise HTTPException(status_code=500, detail="sqlalchemy.OperationalError: relation does not exist")

    @app.get("/error-400-internal")
    async def error_400_internal():
        raise HTTPException(status_code=400, detail="OperationalError: invalid input syntax for uuid")

    @app.get("/error-400-user")
    async def error_400_user():
        raise HTTPException(status_code=400, detail="Invalid lead ID")

    return app


def test_http_500_is_redacted():
    client = TestClient(_build_app())
    response = client.get("/error-500")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_http_400_internal_markers_are_redacted():
    client = TestClient(_build_app())
    response = client.get("/error-400-internal")

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"


def test_http_400_user_message_is_preserved():
    client = TestClient(_build_app())
    response = client.get("/error-400-user")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid lead ID"
