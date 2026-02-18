from __future__ import annotations

import pytest
from fastapi import FastAPI

from app.middleware.security import APIKeyMiddleware


@pytest.mark.asyncio
async def test_api_key_rotation_accepts_previous_internal_key(monkeypatch):
    monkeypatch.setenv("BACKEND_INTERNAL_API_KEY", "active-key-1234567890")
    monkeypatch.setenv("BACKEND_INTERNAL_API_KEY_PREVIOUS", "prev-key-1234567890")

    middleware = APIKeyMiddleware(FastAPI(), public_paths=())
    cache_entry = await middleware._validate_api_key("prev-key-1234567890", db_pool=None)

    assert cache_entry is not None
    assert cache_entry.key_id == "internal"
