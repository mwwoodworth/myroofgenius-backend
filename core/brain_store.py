"""Operational brain client helpers for non-blocking telemetry and context recall."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Coroutine, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BRAIN_BASE_URL = "https://brainops-ai-agents.onrender.com/brain/"
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("BRAINOPS_BRAIN_TIMEOUT_SECS", "8"))
STATUS_CACHE_SECONDS = max(float(os.getenv("BRAINOPS_BRAIN_STATUS_CACHE_SECS", "10")), 1.0)

_last_brain_store_timestamp: Optional[str] = None
_last_brain_status_timestamp: Optional[str] = None
_last_brain_status_checked_at: Optional[datetime] = None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        dt = datetime.fromisoformat(candidate)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _newer_iso_timestamp(first: Optional[str], second: Optional[str]) -> Optional[str]:
    first_dt = _parse_iso_timestamp(first)
    second_dt = _parse_iso_timestamp(second)
    if first_dt and second_dt:
        return first if first_dt >= second_dt else second
    return first or second


def _record_local_store_timestamp(value: Optional[str]) -> None:
    global _last_brain_store_timestamp
    candidate = value or _now_utc_iso()
    _last_brain_store_timestamp = _newer_iso_timestamp(_last_brain_store_timestamp, candidate)


def _record_brain_status_timestamp(value: Optional[str]) -> None:
    global _last_brain_status_timestamp
    if not value:
        return
    _last_brain_status_timestamp = _newer_iso_timestamp(_last_brain_status_timestamp, value)


def _resolve_brain_base_url() -> str:
    """Resolve a normalized /brain base URL from environment or defaults."""
    base_url = (
        os.getenv("BRAINOPS_AI_AGENTS_URL")
        or os.getenv("BRAINOPS_AGENTS_URL")
        or DEFAULT_BRAIN_BASE_URL
    ).strip()
    if not base_url:
        base_url = DEFAULT_BRAIN_BASE_URL

    normalized = base_url.rstrip("/")
    if not normalized.endswith("/brain"):
        normalized = f"{normalized}/brain"
    return normalized


def _brain_headers() -> Dict[str, str]:
    api_key = (os.getenv("BRAINOPS_API_KEY") or "").strip()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def _create_task(coro: Coroutine[Any, Any, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(coro)


def _normalize_context_items(payload: Any, limit: int) -> List[Dict[str, Any]]:
    def _coerce(item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            return item
        return {"value": item}

    if isinstance(payload, list):
        return [_coerce(item) for item in payload[:limit]]

    if isinstance(payload, dict):
        for key in ("results", "memories", "items", "matches", "context", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [_coerce(item) for item in value[:limit]]
        if payload:
            return [_coerce(payload)]

    return []


def build_brain_key(scope: str, action: str, tenant_id: Optional[str] = None) -> str:
    """Build a unique key for operational memory writes."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    tenant_scope = tenant_id or "global"
    return f"{scope}:{action}:{tenant_scope}:{ts}:{uuid.uuid4().hex[:8]}"


def get_last_brain_store_timestamp() -> Optional[str]:
    """Return the last successful write timestamp to the external brain store."""
    return _last_brain_store_timestamp


async def _refresh_brain_status_timestamp(force_refresh: bool = False) -> Optional[str]:
    global _last_brain_status_checked_at
    now = datetime.now(timezone.utc)

    if (
        not force_refresh
        and _last_brain_status_checked_at is not None
        and (now - _last_brain_status_checked_at).total_seconds() < STATUS_CACHE_SECONDS
    ):
        return _last_brain_status_timestamp

    url = f"{_resolve_brain_base_url()}/status"
    headers = _brain_headers()
    timeout = min(DEFAULT_TIMEOUT_SECONDS, 2.5)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            if response.is_success:
                payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                if isinstance(payload, dict):
                    _record_brain_status_timestamp(payload.get("last_update") or payload.get("timestamp"))
            else:
                logger.debug("Brain status fetch failed status=%s body=%s", response.status_code, response.text[:300])
    except Exception as exc:
        logger.debug("Brain status fetch failed: %s", exc)
    finally:
        _last_brain_status_checked_at = now

    return _last_brain_status_timestamp


async def get_effective_brain_timestamp(
    force_refresh: bool = False,
    prefer_remote_status: bool = True,
) -> Optional[str]:
    """Return the effective brain timestamp for health/telemetry reporting.

    In multi-instance production, in-process local write timestamps can drift between
    instances. Prefer the central AI Agents `/brain/status` timestamp for a more
    consistent cross-instance value, with local timestamp as fallback.
    """
    status_timestamp = await _refresh_brain_status_timestamp(force_refresh=force_refresh)
    if prefer_remote_status and status_timestamp:
        return status_timestamp
    return _newer_iso_timestamp(_last_brain_store_timestamp, status_timestamp)


async def store_to_brain(
    key: str,
    value: Dict[str, Any],
    category: str = "operational",
    priority: str = "medium",
    source: str = "backend_api",
) -> None:
    """Write a memory record to the AI Agents brain API."""
    global _last_brain_store_timestamp

    url = f"{_resolve_brain_base_url()}/store"
    payload = {
        "key": key,
        "value": value,
        "category": category,
        "source": source,
        "priority": priority,
        "timestamp": _now_utc_iso(),
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=_brain_headers())
            if response.is_success:
                response_timestamp: Optional[str] = None
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        body = response.json()
                        if isinstance(body, dict):
                            response_timestamp = body.get("last_update") or body.get("timestamp")
                    except Exception:
                        response_timestamp = None
                _record_local_store_timestamp(response_timestamp or _now_utc_iso())
            else:
                logger.debug(
                    "Brain store write failed status=%s key=%s body=%s",
                    response.status_code,
                    key,
                    response.text[:500],
                )
    except Exception as exc:  # pragma: no cover - non-blocking telemetry path
        logger.debug("Brain store write failed for key=%s: %s", key, exc)


def dispatch_brain_store(
    key: str,
    value: Dict[str, Any],
    category: str = "operational",
    priority: str = "medium",
    source: str = "backend_api",
) -> None:
    """Fire-and-forget wrapper so route handlers never block on persistence."""
    _create_task(
        store_to_brain(
            key=key,
            value=value,
            category=category,
            priority=priority,
            source=source,
        )
    )


def store_event(event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
    """Store an operational event in the brain using fire-and-forget dispatch."""
    safe_action = (event_type or "event").strip().lower().replace(" ", "_")
    tenant_id = None
    if metadata and isinstance(metadata, dict):
        tenant_id = str(metadata.get("tenant_id")) if metadata.get("tenant_id") else None

    dispatch_brain_store(
        key=build_brain_key(scope="event", action=safe_action, tenant_id=tenant_id),
        value={
            "event_type": event_type,
            "data": data or {},
            "metadata": metadata or {},
            "recorded_at": _now_utc_iso(),
        },
        category="operational_event",
        priority="high" if safe_action in {"error", "failure", "critical"} else "medium",
        source="backend_api",
    )


async def recall_context(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Recall relevant operational context from the brain service."""
    if not query:
        return []

    normalized_limit = max(1, min(int(limit or 5), 25))
    base_url = _resolve_brain_base_url()
    headers = _brain_headers()
    payload = {"query": query, "limit": normalized_limit}

    endpoints = [f"{base_url}/recall", f"{base_url}/query", f"{base_url}/search"]
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            for endpoint in endpoints:
                try:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                    return _normalize_context_items(response.json(), normalized_limit)
                except httpx.HTTPStatusError:
                    continue
                except Exception as exc:
                    logger.debug("Brain recall call failed for %s: %s", endpoint, exc)
                    continue
    except Exception as exc:
        logger.debug("Brain recall context failed: %s", exc)

    return []


def store_api_insight(route: str, method: str, status_code: int, response_time_ms: float) -> None:
    """Store API performance insight records in the brain service."""
    safe_route = route or "/unknown"
    safe_method = (method or "GET").upper()
    safe_status = int(status_code or 0)
    safe_response_time = float(response_time_ms or 0.0)

    priority = "high" if safe_status >= 500 or safe_response_time >= 2000 else "medium"
    dispatch_brain_store(
        key=build_brain_key(scope="api", action="performance"),
        value={
            "route": safe_route,
            "method": safe_method,
            "status_code": safe_status,
            "response_time_ms": round(safe_response_time, 2),
            "insight_type": "api_performance",
            "recorded_at": _now_utc_iso(),
        },
        category="api_performance",
        priority=priority,
        source="backend_api",
    )
