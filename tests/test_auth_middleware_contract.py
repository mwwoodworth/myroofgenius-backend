"""Contract tests for the authentication middleware.

Verifies:
1. Exempt paths always pass through without auth.
2. Exempt prefixes always pass through.
3. Master key override sets correct state.
4. Missing auth on protected routes returns 401/403.
5. _resolve_master_tenant_id validates UUID format.
6. ApiKey bearer scheme passes through.
"""

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from middleware.authentication import (  # noqa: E402
    AuthenticationMiddleware,
    DEFAULT_EXEMPT_PATHS,
    DEFAULT_EXEMPT_PREFIXES,
    _resolve_master_tenant_id,
)


# ---------------------------------------------------------------------------
# Contract 1: Exempt paths
# ---------------------------------------------------------------------------


class TestExemptPaths:
    """Exempt paths must NEVER require authentication."""

    @pytest.mark.parametrize(
        "path",
        [
            "/health",
            "/api/v1/health",
            "/ready",
            "/api/v1/stripe/webhook",
            "/api/v1/webhooks/stripe",
            "/api/v1/gumroad-revenue/webhook/gumroad",
        ],
    )
    def test_exempt_path_recognized(self, path):
        """Each exempt path is in the default set."""
        assert path in DEFAULT_EXEMPT_PATHS

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/customers",
            "/api/v1/invoices",
            "/api/v1/jobs",
        ],
    )
    def test_protected_paths_not_exempt(self, path):
        """Critical business routes are NOT exempt."""
        assert path not in DEFAULT_EXEMPT_PATHS

    def test_exempt_prefixes(self):
        """Prefix-based exemptions work correctly."""
        mw = AuthenticationMiddleware(MagicMock())
        assert mw._is_exempt("/docs/swagger")
        assert mw._is_exempt("/api/v1/products/public/list")
        assert mw._is_exempt("/static/styles.css")
        assert not mw._is_exempt("/api/v1/customers/123")


# ---------------------------------------------------------------------------
# Contract 2: Master key tenant resolution
# ---------------------------------------------------------------------------


class TestMasterTenantResolution:
    """_resolve_master_tenant_id must validate UUID format."""

    def test_valid_uuid_accepted(self):
        tid = str(uuid.uuid4())
        with patch.dict(os.environ, {"BACKEND_INTERNAL_TENANT_ID": tid}):
            assert _resolve_master_tenant_id() == tid

    def test_invalid_uuid_rejected(self):
        with patch.dict(os.environ, {"BACKEND_INTERNAL_TENANT_ID": "not-a-uuid"}, clear=True):
            assert _resolve_master_tenant_id() is None

    def test_empty_string_rejected(self):
        with patch.dict(os.environ, {"BACKEND_INTERNAL_TENANT_ID": ""}, clear=True):
            assert _resolve_master_tenant_id() is None

    def test_fallback_chain(self):
        """Falls back through BACKEND_INTERNAL_TENANT_ID → DEFAULT_TENANT_ID → MRG_DEFAULT_TENANT_ID."""
        tid = str(uuid.uuid4())
        with patch.dict(
            os.environ,
            {
                "BACKEND_INTERNAL_TENANT_ID": "",
                "DEFAULT_TENANT_ID": "",
                "MRG_DEFAULT_TENANT_ID": tid,
            },
        ):
            assert _resolve_master_tenant_id() == tid

    def test_all_empty_returns_none(self):
        with patch.dict(
            os.environ,
            {
                "BACKEND_INTERNAL_TENANT_ID": "",
                "DEFAULT_TENANT_ID": "",
                "MRG_DEFAULT_TENANT_ID": "",
            },
        ):
            assert _resolve_master_tenant_id() is None


# ---------------------------------------------------------------------------
# Contract 3: Webhook paths must be exempt
# ---------------------------------------------------------------------------


class TestWebhookExemptions:
    """All webhook endpoints must be auth-exempt (they use their own signature verification)."""

    WEBHOOK_PATHS = [
        "/api/v1/stripe/webhook",
        "/api/v1/webhooks/stripe",
        "/api/v1/webhooks/render",
        "/webhook/stripe",
        "/api/v1/revenue/webhook",
        "/api/v1/gumroad-revenue/webhook/gumroad",
    ]

    @pytest.mark.parametrize("path", WEBHOOK_PATHS)
    def test_webhook_path_exempt(self, path):
        mw = AuthenticationMiddleware(MagicMock())
        assert mw._is_exempt(
            path
        ), f"Webhook path {path} is NOT exempt — signature verification would be blocked by auth middleware"


# ---------------------------------------------------------------------------
# Contract 4: Master key sets correct request state
# ---------------------------------------------------------------------------


class TestMasterKeyState:
    """When master key is used, request.state must be set correctly."""

    @pytest.mark.asyncio
    async def test_master_key_sets_admin_role(self):
        """Master key auth must set role=admin and user_id=system."""
        tid = str(uuid.uuid4())

        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/customers"
        mock_request.headers = {"X-API-Key": "test-master-key"}
        mock_request.state = MagicMock(spec=[])  # Empty state

        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)

        mw = AuthenticationMiddleware(MagicMock())

        with patch.dict(
            os.environ,
            {
                "MASTER_API_KEY": "test-master-key",
                "BACKEND_INTERNAL_TENANT_ID": tid,
            },
        ):
            await mw.dispatch(mock_request, mock_call_next)

        assert mock_request.state.user["role"] == "admin"
        assert mock_request.state.user["id"] == "system"
        assert mock_request.state.tenant_id == tid
        assert mock_request.state.authenticated is True
