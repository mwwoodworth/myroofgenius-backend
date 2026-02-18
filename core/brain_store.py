"""
Shared helpers for non-blocking writes to the AI Agents brain store.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_AI_AGENTS_URL = "https://brainops-ai-agents.onrender.com"


def build_brain_key(scope: str, action: str, tenant_id: Optional[str] = None) -> str:
    """Build a unique key for operational memory writes."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    tenant_scope = tenant_id or "global"
    return f"{scope}:{action}:{tenant_scope}:{ts}:{uuid.uuid4().hex[:8]}"


async def store_to_brain(
    key: str,
    value: Dict[str, Any],
    category: str = "operational",
    priority: str = "medium",
    source: str = "backend_api",
) -> None:
    """Write a memory record to the AI Agents brain API."""
    base_url = os.getenv("BRAINOPS_AI_AGENTS_URL", DEFAULT_AI_AGENTS_URL).rstrip("/")
    url = f"{base_url}/brain/store"
    api_key = os.getenv("BRAINOPS_API_KEY", "")

    payload = {
        "key": key,
        "value": value,
        "category": category,
        "source": source,
        "priority": priority,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload, headers={"X-API-Key": api_key})
    except Exception as exc:  # pragma: no cover - non-blocking telemetry path
        logger.debug("Brain store write failed for key=%s: %s", key, exc)


def dispatch_brain_store(
    key: str,
    value: Dict[str, Any],
    category: str = "operational",
    priority: str = "medium",
    source: str = "backend_api",
) -> None:
    """
    Fire-and-forget wrapper so route handlers never block on memory persistence.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(
        store_to_brain(
            key=key,
            value=value,
            category=category,
            priority=priority,
            source=source,
        )
    )
