"""
Comprehensive AI Endpoints
Provider-backed AI analysis endpoints with no rule-based/mock fallbacks.
"""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

logger = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Core"])

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception  # type: ignore


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}
    analysis_type: Optional[str] = "general"


class VisionAnalyzeRequest(BaseModel):
    image_data: Optional[str] = None  # base64-encoded image bytes
    image_url: Optional[str] = None
    analysis_type: Optional[str] = "roof"
    options: Optional[Dict[str, Any]] = {}


def _providers_configured() -> Dict[str, bool]:
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
    }


async def _resolve_image_base64(image_data: Optional[str], image_url: Optional[str]) -> str:
    if image_data:
        return image_data

    if not image_url:
        raise HTTPException(status_code=400, detail="Either image_data or image_url required")

    if image_url.startswith("data:image"):
        parts = image_url.split(",", 1)
        if len(parts) != 2 or not parts[1].strip():
            raise HTTPException(status_code=400, detail="Invalid data URL")
        return parts[1].strip()

    if not image_url.startswith(("http://", "https://")):
        # Assume caller already provided raw base64.
        return image_url

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        if len(response.content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large (max 10MB)")
        return base64.b64encode(response.content).decode("utf-8")


@router.get("/ai/status")
async def get_ai_status():
    """Get AI system status and capabilities (no fake performance metrics)."""
    providers = _providers_configured()
    return {
        "status": "configured" if any(providers.values()) else "not_configured",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
        "capabilities": {
            "text_analysis": ai_service is not None,
            "vision_analysis": ai_service is not None,
            "roof_analysis": ai_service is not None,
        },
        "performance": {
            "average_response_time": None,
            "success_rate": None,
            "requests_today": None,
        },
    }


@router.post("/ai/analyze")
async def analyze_text(request: AnalyzeRequest):
    """Analyze text using a real AI provider (JSON response)."""
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided for analysis")
    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI service not available on this server")

    prompt = (
        f"Analyze this {request.analysis_type} text. Return JSON with keys: "
        "sentiment, key_topics (list), entities (object), summary, recommendations (list), confidence (0-1).\n\n"
        f"Text:\n{request.text}"
    )

    try:
        analysis = await ai_service.generate_json(prompt)
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": {"text_length": len(request.text), "analysis_type": request.analysis_type},
        "analysis": analysis,
    }


@router.post("/ai/vision/analyze")
async def analyze_vision(request: VisionAnalyzeRequest):
    """Analyze images using a real AI provider (roof only)."""
    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI service not available on this server")

    if (request.analysis_type or "roof").lower() != "roof":
        raise HTTPException(status_code=501, detail="Only roof vision analysis is supported on this server")

    try:
        image_b64 = await _resolve_image_base64(request.image_data, request.image_url)
        results = await ai_service.analyze_roof_image(image_b64, {"options": request.options or {}})
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_type": request.analysis_type,
        "results": results,
    }


@router.post("/ai/roof/analyze")
async def analyze_roof(file: Optional[UploadFile] = File(None), image_url: Optional[str] = None):
    """Specialized roof analysis using a real AI provider."""
    if not file and not image_url:
        raise HTTPException(status_code=400, detail="Either file upload or image_url required")

    if file:
        contents = await file.read()
        image_data = base64.b64encode(contents).decode("utf-8")
        request = VisionAnalyzeRequest(image_data=image_data, analysis_type="roof")
    else:
        request = VisionAnalyzeRequest(image_url=image_url, analysis_type="roof")

    return await analyze_vision(request)

