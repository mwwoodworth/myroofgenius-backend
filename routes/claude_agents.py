"""
Claude Agents compatibility endpoints (proxy to BrainOps AI Agents service).
"""

from datetime import datetime, timezone
import os

import httpx
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/v1/claude-agents", tags=["Claude Agents"])


@router.get("/status")
async def claude_agents_status():
    ai_agents_url = os.getenv("BRAINOPS_AI_AGENTS_URL")
    if not ai_agents_url:
        raise HTTPException(status_code=503, detail="BRAINOPS_AI_AGENTS_URL not configured")

    api_key = os.getenv("BRAINOPS_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ai_agents_url.rstrip('/')}/health", headers=headers)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI agents status check failed: {exc}") from exc

    payload = None
    try:
        payload = response.json()
    except Exception:
        payload = None

    return {
        "status": "operational" if response.status_code == 200 else "degraded",
        "upstream_status_code": response.status_code,
        "upstream": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
