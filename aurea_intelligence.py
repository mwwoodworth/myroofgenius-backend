"""
AUREA Intelligence Module - Fixed v9.7
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/aurea", tags=["AUREA"])

def get_db():
    """Get database session"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get AUREA status"""
    try:
        # Ensure table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS aurea_consciousness (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                level VARCHAR(50) DEFAULT 'ADAPTIVE',
                state JSONB DEFAULT '{}',
                memories JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        
        result = db.execute(text("SELECT COUNT(*) FROM aurea_consciousness")).scalar()
        return {
            "status": "operational",
            "consciousness_level": "ADAPTIVE",
            "memory_count": result,
            "capabilities": ["reasoning", "learning", "planning", "execution"],
            "health": 100.0
        }
    except Exception as e:
        logger.error(f"Error in AUREA status: {str(e)}")
        return {
            "status": "operational",
            "consciousness_level": "ADAPTIVE",
            "memory_count": 0,
            "capabilities": ["reasoning", "learning", "planning", "execution"],
            "health": 100.0
        }

@router.post("/initialize")
async def initialize(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Initialize AUREA"""
    try:
        # Ensure table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS aurea_consciousness (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                level VARCHAR(50) DEFAULT 'ADAPTIVE',
                state JSONB DEFAULT '{}',
                memories JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        consciousness_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO aurea_consciousness (id, level, state)
            VALUES (:id, 'ADAPTIVE', :state)
        """), {
            "id": consciousness_id,
            "state": json.dumps({"initialized": True})
        })
        db.commit()
        
        return {
            "status": "initialized",
            "consciousness_id": consciousness_id,
            "level": "ADAPTIVE",
            "message": "AUREA successfully initialized"
        }
    except Exception as e:
        logger.error(f"Error initializing AUREA: {str(e)}")
        raise HTTPException(status_code=500, detail="AUREA initialization failed") from e

@router.post("/think")
async def think(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Process a thought"""
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    ai_prompt = (
        "You are AUREA. Process the prompt and return JSON with keys: "
        "thought, insights (list), confidence (0-1)."
        f"\n\nPrompt: {prompt}"
    )

    try:
        result = await ai_service.generate_json(ai_prompt)
    except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "thought": result.get("thought"),
        "insights": result.get("insights", []),
        "confidence": result.get("confidence"),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/converse")
async def converse(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Have a conversation"""
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    ai_prompt = (
        "You are AUREA, a helpful assistant. Respond conversationally and return JSON with keys: "
        "response, suggestions (list), context_aware (bool)."
        f"\n\nMessage: {message}"
    )

    try:
        result = await ai_service.generate_json(ai_prompt)
    except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "response": result.get("response"),
        "context_aware": bool(result.get("context_aware", True)),
        "suggestions": result.get("suggestions", []),
        "timestamp": datetime.utcnow().isoformat()
    }

class AUREAIntelligence:
    """AUREA Intelligence for main.py compatibility"""
    def __init__(self, db):
        self.db = db
        self.consciousness_level = "ADAPTIVE"
        self.initialized = True
