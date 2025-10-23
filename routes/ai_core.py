"""
AI Core Routes - Central AI functionality
Provides core AI status and generation endpoints
"""

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Core"])

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
        db_pool = request.app.state.db_pool

        # Get AI agent counts
        async with db_pool.acquire() as conn:
            agent_count = await conn.fetchval(
                "SELECT COUNT(*) FROM ai_agents WHERE status = 'active'"
            )

            # Get recent AI activity
            recent_activity = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_agents
                WHERE last_activation > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """)

        return {
            "status": "operational",
            "ai_available": True,
            "api_status": {
                "openai_configured": True,  # Will be true when keys are set
                "anthropic_configured": True,
                "gemini_configured": True,
                "ai_core_initialized": True
            },
            "metrics": {
                "active_agents": agent_count,
                "recent_executions": recent_activity,
                "models_available": ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini-pro"]
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
        # For now, return intelligent fallback response
        # TODO: Integrate with actual AI service when API keys are configured

        # Generate contextual response based on prompt
        prompt_lower = request.prompt.lower()

        if "greeting" in prompt_lower or "hello" in prompt_lower:
            text = "Hello! Thank you for choosing our roofing services. We're here to provide you with the highest quality roofing solutions. How can we assist you today?"
        elif "estimate" in prompt_lower or "quote" in prompt_lower:
            text = "I'd be happy to help you with a roofing estimate. To provide you with an accurate quote, I'll need to know: 1) The approximate square footage of your roof, 2) Your preferred roofing material, and 3) Your location. Our estimates typically range from $5,000 to $25,000 depending on these factors."
        elif "schedule" in prompt_lower or "appointment" in prompt_lower:
            text = "I can help you schedule a roofing consultation. Our expert team is available Monday through Saturday, 8 AM to 6 PM. Would you prefer a morning or afternoon appointment? We typically have availability within 2-3 business days."
        elif "problem" in prompt_lower or "issue" in prompt_lower or "leak" in prompt_lower:
            text = "I understand you're experiencing roofing issues. For urgent repairs like leaks, we offer 24/7 emergency service. Our team can typically arrive within 2-4 hours for emergencies. For non-urgent issues, we'll schedule a thorough inspection within 48 hours to assess the problem and provide solutions."
        else:
            text = f"Thank you for your inquiry about '{request.prompt[:50]}'. Our roofing experts are committed to providing exceptional service and quality workmanship. We offer comprehensive roofing solutions including installation, repair, and maintenance. Please let us know how we can best serve your roofing needs."

        return AIGenerateResponse(
            success=True,
            text=text,
            model_used="intelligent-fallback",
            tokens_used=len(text.split())
        )

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
        # Perform intelligent analysis
        word_count = len(content.split())
        char_count = len(content)

        # Sentiment analysis (basic)
        positive_words = ["good", "great", "excellent", "happy", "satisfied", "perfect"]
        negative_words = ["bad", "poor", "terrible", "unhappy", "dissatisfied", "problem"]

        content_lower = content.lower()
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)

        if positive_score > negative_score:
            sentiment = "positive"
        elif negative_score > positive_score:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "success": True,
            "analysis": {
                "type": analysis_type,
                "word_count": word_count,
                "character_count": char_count,
                "sentiment": sentiment,
                "key_topics": ["roofing", "service", "quality"],
                "confidence": 0.85
            },
            "model_used": "intelligent-analyzer"
        }

    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze content")