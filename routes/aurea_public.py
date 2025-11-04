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
    
    # Simple response for now - can be enhanced with actual AI
    responses = {
        "hello": "Hello! I'm AUREA, your AI assistant for roofing solutions. How can I help you today?",
        "price": "Our roofing products range from $19.99 to $2,999. Would you like to see our catalog?",
        "service": "We offer complete roofing services including installation, repair, and inspection.",
        "default": "I'm here to help with all your roofing needs. You can ask about products, services, or schedule a consultation."
    }
    
    msg_lower = message.message.lower()
    
    if "hello" in msg_lower or "hi" in msg_lower:
        response_text = responses["hello"]
    elif "price" in msg_lower or "cost" in msg_lower:
        response_text = responses["price"]
    elif "service" in msg_lower or "install" in msg_lower:
        response_text = responses["service"]
    else:
        response_text = responses["default"]
    
    return ChatResponse(
        response=response_text,
        timestamp=datetime.now(),
        session_id=str(uuid.uuid4())
    )

@router.get("/status")
async def aurea_status():
    """Check AUREA availability"""
    return {
        "status": "online",
        "version": "2.0",
        "capabilities": ["chat", "product_info", "scheduling", "quotes"]
    }
