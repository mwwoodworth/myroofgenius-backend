"""Contract tests for the brain store HTTP boundary (backend → agents).

Verifies:
1. URL resolution always produces a valid /brain endpoint.
2. Headers always include Content-Type and conditionally X-API-Key.
3. store_to_brain increments failure counters on HTTP errors.
4. store_to_brain increments failure counters on network errors.
5. recall_context falls back through 3 endpoints.
6. recall_context returns empty list on total failure.
7. dispatch_brain_store is fire-and-forget (never raises).
8. Timestamp tracking works correctly.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.brain_store as brain_store  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Reset module-level counters before each test."""
    brain_store._dispatch_count = 0
    brain_store._dispatch_failures = 0
    brain_store._last_failure_detail = None
    brain_store._last_brain_store_timestamp = None
    brain_store._last_brain_status_timestamp = None
    brain_store._last_brain_status_checked_at = None


# ---------------------------------------------------------------------------
# Contract 1: URL resolution
# ---------------------------------------------------------------------------


class TestURLResolution:
    """_resolve_brain_base_url must always return a URL ending in /brain."""

    def test_default_url(self):
        with patch.dict(os.environ, {}, clear=True):
            url = brain_store._resolve_brain_base_url()
        assert url.endswith("/brain")
        assert "brainops-ai-agents" in url

    def test_custom_url_without_brain_suffix(self):
        with patch.dict(os.environ, {"BRAINOPS_AI_AGENTS_URL": "https://my-agents.example.com"}):
            url = brain_store._resolve_brain_base_url()
        assert url == "https://my-agents.example.com/brain"

    def test_custom_url_with_brain_suffix(self):
        with patch.dict(
            os.environ, {"BRAINOPS_AI_AGENTS_URL": "https://my-agents.example.com/brain"}
        ):
            url = brain_store._resolve_brain_base_url()
        assert url == "https://my-agents.example.com/brain"

    def test_trailing_slash_stripped(self):
        with patch.dict(os.environ, {"BRAINOPS_AI_AGENTS_URL": "https://my-agents.example.com/"}):
            url = brain_store._resolve_brain_base_url()
        assert url == "https://my-agents.example.com/brain"
        assert not url.endswith("//brain")

    def test_fallback_url_used(self):
        with patch.dict(os.environ, {"BRAINOPS_AGENTS_URL": "https://fallback.example.com"}):
            url = brain_store._resolve_brain_base_url()
        assert url == "https://fallback.example.com/brain"


# ---------------------------------------------------------------------------
# Contract 2: Headers
# ---------------------------------------------------------------------------


class TestHeaders:
    """_brain_headers must always include Content-Type, conditionally X-API-Key."""

    def test_always_includes_content_type(self):
        with patch.dict(os.environ, {}, clear=True):
            headers = brain_store._brain_headers()
        assert headers["Content-Type"] == "application/json"

    def test_includes_api_key_when_set(self):
        with patch.dict(os.environ, {"BRAINOPS_API_KEY": "test-key-123"}):
            headers = brain_store._brain_headers()
        assert headers["X-API-Key"] == "test-key-123"

    def test_omits_api_key_when_empty(self):
        with patch.dict(os.environ, {"BRAINOPS_API_KEY": ""}):
            headers = brain_store._brain_headers()
        assert "X-API-Key" not in headers

    def test_omits_api_key_when_whitespace(self):
        with patch.dict(os.environ, {"BRAINOPS_API_KEY": "  "}):
            headers = brain_store._brain_headers()
        assert "X-API-Key" not in headers


# ---------------------------------------------------------------------------
# Contract 3: Failure counting on HTTP errors
# ---------------------------------------------------------------------------


class TestStoreFailureCounting:
    """store_to_brain must track failures without raising."""

    @pytest.mark.asyncio
    async def test_http_error_increments_failures(self):
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            await brain_store.store_to_brain(key="test", value={"x": 1})

        assert brain_store._dispatch_count == 1
        assert brain_store._dispatch_failures == 1
        assert "status=500" in brain_store._last_failure_detail

    @pytest.mark.asyncio
    async def test_network_error_increments_failures(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            await brain_store.store_to_brain(key="test", value={"x": 1})

        assert brain_store._dispatch_failures == 1
        assert "test" in brain_store._last_failure_detail

    @pytest.mark.asyncio
    async def test_success_does_not_increment_failures(self):
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = MagicMock(return_value={"timestamp": "2026-02-20T12:00:00Z"})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            await brain_store.store_to_brain(key="test", value={"x": 1})

        assert brain_store._dispatch_count == 1
        assert brain_store._dispatch_failures == 0

    @pytest.mark.asyncio
    async def test_multiple_failures_accumulate(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            for _ in range(5):
                await brain_store.store_to_brain(key="k", value={"v": 1})

        assert brain_store._dispatch_failures == 5
        assert brain_store._dispatch_count == 5


# ---------------------------------------------------------------------------
# Contract 4: Recall fallback chain
# ---------------------------------------------------------------------------


class TestRecallFallback:
    """recall_context must try /recall, /query, /search in sequence."""

    @pytest.mark.asyncio
    async def test_recall_tries_all_three_endpoints_on_404(self):
        call_urls = []

        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.is_success = False

        async def mock_post(url, **kwargs):
            call_urls.append(url)
            return mock_response_404

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            result = await brain_store.recall_context("test query")

        assert result == []
        assert len(call_urls) == 3
        assert any("/recall" in u for u in call_urls)
        assert any("/query" in u for u in call_urls)
        assert any("/search" in u for u in call_urls)

    @pytest.mark.asyncio
    async def test_recall_returns_data_from_first_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json = MagicMock(return_value=[{"key": "test", "value": "data"}])
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            result = await brain_store.recall_context("test query")

        assert len(result) == 1
        assert result[0]["key"] == "test"

    @pytest.mark.asyncio
    async def test_recall_empty_query_returns_empty(self):
        result = await brain_store.recall_context("")
        assert result == []

    @pytest.mark.asyncio
    async def test_recall_total_failure_returns_empty(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            result = await brain_store.recall_context("test")

        assert result == []


# ---------------------------------------------------------------------------
# Contract 5: Health observability
# ---------------------------------------------------------------------------


class TestHealthObservability:
    """get_brain_store_health must expose correct counters."""

    def test_health_dict_shape(self):
        health = brain_store.get_brain_store_health()
        assert "dispatches" in health
        assert "failures" in health
        assert "last_failure" in health
        assert "last_store_timestamp" in health

    @pytest.mark.asyncio
    async def test_health_reflects_failures(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.brain_store.httpx.AsyncClient", return_value=mock_client):
            await brain_store.store_to_brain(key="k", value={"v": 1})

        health = brain_store.get_brain_store_health()
        assert health["dispatches"] == 1
        assert health["failures"] == 1
        assert health["last_failure"] is not None


# ---------------------------------------------------------------------------
# Contract 6: Timestamp tracking
# ---------------------------------------------------------------------------


class TestTimestampTracking:
    """Timestamp utilities must handle edge cases."""

    def test_parse_iso_z_suffix(self):
        result = brain_store._parse_iso_timestamp("2026-02-20T12:00:00Z")
        assert result is not None

    def test_parse_iso_none(self):
        assert brain_store._parse_iso_timestamp(None) is None

    def test_parse_iso_empty(self):
        assert brain_store._parse_iso_timestamp("") is None

    def test_parse_iso_garbage(self):
        assert brain_store._parse_iso_timestamp("not-a-date") is None

    def test_newer_picks_later(self):
        older = "2026-02-19T12:00:00Z"
        newer = "2026-02-20T12:00:00Z"
        assert brain_store._newer_iso_timestamp(older, newer) == newer
        assert brain_store._newer_iso_timestamp(newer, older) == newer

    def test_newer_with_none(self):
        ts = "2026-02-20T12:00:00Z"
        assert brain_store._newer_iso_timestamp(ts, None) == ts
        assert brain_store._newer_iso_timestamp(None, ts) == ts

    def test_build_brain_key_format(self):
        key = brain_store.build_brain_key("test", "action", "tenant123")
        assert key.startswith("test:action:tenant123:")
