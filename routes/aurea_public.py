from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/aurea/public", tags=["Public AUREA"])

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    session_id: str

@router.post("/chat", response_model=ChatResponse)
async def public_chat(message: ChatMessage):
    """Public AUREA chat endpoint - NO AUTH REQUIRED"""
    import uuid
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

    prompt = (
        "You are AUREA, a helpful roofing assistant for WeatherCraft. "
        "Respond clearly, ask clarifying questions when needed, and avoid making up numbers.\n\n"
        f"User message: {message.message}\n"
        f"Context: {message.context or {}}\n\n"
        "Return JSON with key: response."
    )

    try:
        result = await ai_service.generate_json(prompt)
    except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response_text = result.get("response")
    if not response_text:
        raise HTTPException(status_code=500, detail="AI response missing 'response' field")

    return ChatResponse(
        response=response_text,
        timestamp=datetime.now(),
        session_id=str(uuid.uuid4())
    )

@router.get("/status")
async def aurea_status():
    """Check AUREA availability"""
    from ai_services.real_ai_integration import ai_service
    providers = ai_service._configured_providers() if ai_service else []

    return {
        "status": "online" if providers else "degraded",
        "version": "2.0",
        "capabilities": ["chat", "product_info", "scheduling", "quotes"],
        "providers": providers
    }
