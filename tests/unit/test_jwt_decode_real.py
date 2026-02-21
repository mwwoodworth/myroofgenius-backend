"""
P2-4: Real JWT decode path tests (no monkeypatching of get_current_user).

Tests the actual jwt.decode() path in core/supabase_auth.py.
"""

import os
import time
from datetime import datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure test JWT secret is set BEFORE importing the app
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-p2-4")
os.environ.setdefault("SUPABASE_JWT_AUDIENCE", "authenticated")

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
JWT_AUDIENCE = os.environ["SUPABASE_JWT_AUDIENCE"]


def _make_token(
    sub="test-user-id",
    email="test@example.com",
    aud="authenticated",
    tenant_id="test-tenant-id",
    exp_delta_seconds=3600,
    secret=None,
):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "aud": aud,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_delta_seconds,
        "user_metadata": {"tenant_id": tenant_id},
    }
    return jwt.encode(payload, secret or JWT_SECRET, algorithm="HS256")


@pytest.fixture
def valid_token():
    return _make_token()


@pytest.fixture
def expired_token():
    return _make_token(exp_delta_seconds=-60)


@pytest.fixture
def wrong_audience_token():
    return _make_token(aud="wrong-audience")


@pytest.fixture
def wrong_secret_token():
    return _make_token(secret="totally-wrong-secret")


@pytest.mark.asyncio
async def test_valid_jwt_decoded_successfully(valid_token):
    """A properly signed JWT with correct audience should be accepted."""
    from core.supabase_auth import get_current_user
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock(spec=[])  # No .user attribute

    user = await get_current_user(
        request=request,
        authorization=f"Bearer {valid_token}",
    )
    assert user["id"] == "test-user-id"
    assert user["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_expired_jwt_rejected(expired_token):
    """An expired JWT should be rejected with 401."""
    from core.supabase_auth import get_current_user
    from fastapi import HTTPException
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock(spec=[])

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=request,
            authorization=f"Bearer {expired_token}",
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_wrong_audience_rejected(wrong_audience_token):
    """A JWT with wrong audience should be rejected with 401."""
    from core.supabase_auth import get_current_user
    from fastapi import HTTPException
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock(spec=[])

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=request,
            authorization=f"Bearer {wrong_audience_token}",
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_signature_rejected(wrong_secret_token):
    """A JWT signed with wrong secret should be rejected with 401."""
    from core.supabase_auth import get_current_user
    from fastapi import HTTPException
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock(spec=[])

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=request,
            authorization=f"Bearer {wrong_secret_token}",
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_bearer_prefix_rejected():
    """Authorization header without 'Bearer ' prefix should be rejected."""
    from core.supabase_auth import get_current_user
    from fastapi import HTTPException
    from unittest.mock import MagicMock

    request = MagicMock()
    request.state = MagicMock(spec=[])

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=request,
            authorization="NotBearer some-token",
        )
    assert exc_info.value.status_code == 401
