"""
AI Core Routes - Central AI functionality
Provides core AI status and generation endpoints
"""

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import json
import os

from ai_core.real_ai_system import ai_system

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Core"])

def _has_any_ai_provider_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY"))

class AIGenerateRequest(BaseModel):
    """Request for AI text generation"""
    prompt: str
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    model: Optional[str] = "gpt-3.5-turbo"

class AIGenerateResponse(BaseModel):
    """Response from AI text generation"""
    success: bool
    text: str
    model_used: str
    tokens_used: Optional[int] = None

@router.get("/status")
async def ai_status(request: Request):
    """Get AI system status"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        configured_providers = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
        }

        # Get AI agent counts
        agent_count = None
        recent_activity = None
        if db_pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    agent_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM ai_agents WHERE status = 'active'"
                    )
                    recent_activity = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM ai_agents
                        WHERE last_activation > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                        """
                    )
            except Exception:
                agent_count = None
                recent_activity = None

        return {
            "status": "operational",
            "ai_available": any(configured_providers.values()),
            "api_status": {
                **configured_providers,
                "ai_core_initialized": any(configured_providers.values()),
            },
            "metrics": {
                "active_agents": agent_count,
                "recent_executions": recent_activity,
                "models_available": [
                    name
                    for name, enabled in (
                        ("openai", configured_providers["openai"]),
                        ("anthropic", configured_providers["anthropic"]),
                        ("gemini", configured_providers["gemini"]),
                    )
                    if enabled
                ],
            },
            "capabilities": [
                "text_generation",
                "image_analysis",
                "embeddings",
                "classification",
                "summarization"
            ]
        }
    except Exception as e:
        logger.error(f"AI status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI status")

@router.post("/generate", response_model=AIGenerateResponse)
async def generate_text(
    request: AIGenerateRequest,
    req: Request
):
    """Generate text using AI"""
    try:
        if not _has_any_ai_provider_configured():
            raise HTTPException(status_code=503, detail="No AI providers configured on this server")

        provider = None
        if request.model:
            model_lower = request.model.lower()
            if "anthropic" in model_lower or "claude" in model_lower:
                provider = "anthropic"
            elif "gemini" in model_lower:
                provider = "gemini"
            elif "openai" in model_lower or "gpt" in model_lower:
                provider = "openai"

        text = await ai_system.think(request.prompt, context=None, provider=provider)

        return AIGenerateResponse(
            success=True,
            text=text,
            model_used=provider or "auto",
            tokens_used=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate text")

@router.post("/analyze")
async def analyze_content(
    content: str = Body(...),
    analysis_type: str = Body(default="general"),
    request: Request = None
):
    """Analyze content using AI"""
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        prompt = (
            f"Analyze the following {analysis_type} content and return JSON with keys: "
            "sentiment, key_topics (list), entities (object), summary, recommendations (list), confidence (0-1).\n\n"
            f"Content:\n{content}"
        )

        try:
            analysis = await ai_service.generate_json(prompt)
        except AIServiceNotConfiguredError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return {
            "success": True,
            "analysis": {
                "type": analysis_type,
                **analysis,
            },
            "model_used": analysis.get("ai_provider") if isinstance(analysis, dict) else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze content")
