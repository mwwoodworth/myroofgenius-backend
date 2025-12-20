"""
AI Services Router - Critical AI Endpoints
Provides essential AI functionality for ERP system
"""

import base64
import os
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception  # type: ignore

from core.supabase_auth import get_authenticated_user

class RoofAnalysisRequest(BaseModel):
    image_url: str
    property_address: Optional[str] = None

class LeadScoringRequest(BaseModel):
    lead_id: str

class ContentGenerationRequest(BaseModel):
    type: str  # blog, email, social, etc.
    topic: str
    target_audience: Optional[str] = None


async def _resolve_image_base64(image_url: str) -> str:
    if image_url.startswith("data:image"):
        parts = image_url.split(",", 1)
        if len(parts) != 2 or not parts[1].strip():
            raise HTTPException(status_code=400, detail="Invalid data URL")
        return parts[1].strip()

    # Heuristic: treat as base64 if it doesn't look like a URL.
    if not image_url.startswith(("http://", "https://")):
        try:
            base64.b64decode(image_url, validate=True)
            return image_url
        except Exception as exc:
            raise HTTPException(status_code=400, detail="image_url must be a data URL, base64, or http(s) URL") from exc

    # Fetch remote image.
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        content = response.content
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large (max 10MB)")
        return base64.b64encode(content).decode("utf-8")


@router.post("/roof-analysis")
async def analyze_roof(request: RoofAnalysisRequest):
    """Analyze roof from image using AI vision"""
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        image_data = await _resolve_image_base64(request.image_url)
        analysis = await ai_service.analyze_roof_image(
            image_data,
            {"property_address": request.property_address},
        )
        analysis.setdefault("analysis_id", str(uuid.uuid4()))
        analysis.setdefault("analysis_date", datetime.now(timezone.utc).isoformat())
        return {"success": True, "analysis": analysis}
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as e:
        logger.error(f"Roof analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lead-scoring")
async def score_lead(
    request: LeadScoringRequest,
    http_request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Score lead using AI algorithms"""
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        pool = getattr(http_request.app.state, "db_pool", None)
        if pool is None:
            raise HTTPException(status_code=503, detail="Database connection not available")

        tenant_id = current_user.get("tenant_id")

        try:
            lead_uuid = uuid.UUID(request.lead_id)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid lead_id") from exc

        async with pool.acquire() as conn:
            # Best-effort tenant scoping when the column exists.
            lead_row = None
            try:
                if tenant_id:
                    lead_row = await conn.fetchrow(
                        "SELECT * FROM leads WHERE id = $1::uuid AND tenant_id = $2",
                        lead_uuid,
                        tenant_id,
                    )
            except Exception:
                lead_row = None

            if lead_row is None:
                lead_row = await conn.fetchrow(
                    "SELECT * FROM leads WHERE id = $1::uuid",
                    lead_uuid,
                )

        if not lead_row:
            raise HTTPException(status_code=404, detail="Lead not found")

        lead_data = dict(lead_row)
        result = await ai_service.score_lead(lead_data, [])
        result.setdefault("lead_id", request.lead_id)
        result.setdefault("scored_at", datetime.now(timezone.utc).isoformat())
        return {"success": True, "scoring": result}
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as e:
        logger.error(f"Lead scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content-generation")
async def generate_content(request: ContentGenerationRequest):
    """Generate content using AI"""
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        style = request.type
        if request.target_audience:
            style = f"{style} for {request.target_audience}"

        prompt = (
            "Generate marketing content for a roofing company.\n\n"
            f"Type: {request.type}\n"
            f"Topic: {request.topic}\n"
            f"Target audience: {request.target_audience or 'general'}\n\n"
            "Return JSON with keys: title (optional), content, cta, seo_keywords (list), social_media (list)."
        )

        try:
            content = await ai_service.generate_json(prompt)
        except Exception:
            content = await ai_service.generate_content(request.topic, style)

        result: Dict[str, Any] = {
            "content_id": str(uuid.uuid4()),
            "type": request.type,
            "topic": request.topic,
            "target_audience": request.target_audience,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **(content if isinstance(content, dict) else {"content": content}),
        }
        return {"success": True, "content": result}
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ai_services_health():
    """Health check for AI services"""
    providers = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
    }
    return {
        "status": "configured" if any(providers.values()) else "not_configured",
        "services": {
            "roof_analysis": "available" if ai_service is not None else "unavailable",
            "lead_scoring": "available" if ai_service is not None else "unavailable",
            "content_generation": "available" if ai_service is not None else "unavailable",
        },
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
