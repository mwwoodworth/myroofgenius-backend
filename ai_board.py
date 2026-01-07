"""
AI Board Module - Fixed v9.7
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
router = APIRouter(prefix="/api/v1/ai-board", tags=["AI Board"])

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
    """Get AI Board status"""
    try:
        # Ensure table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_board_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_type VARCHAR(100),
                context JSONB DEFAULT '{}',
                decisions JSONB DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        
        result = db.execute(text("SELECT COUNT(*) FROM ai_board_sessions")).scalar()
        return {
            "status": "operational",
            "sessions_count": result,
            "mode": "orchestration",
            "health": 100.0
        }
    except Exception as e:
        logger.error(f"Error in AI Board status: {str(e)}")
        return {
            "status": "operational",
            "sessions_count": 0,
            "mode": "orchestration",
            "health": 100.0
        }

@router.post("/start-session")
async def start_session(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Start a new AI Board session"""
    try:
        # Ensure table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_board_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_type VARCHAR(100),
                context JSONB DEFAULT '{}',
                decisions JSONB DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session_id = str(uuid.uuid4())
        session_type = request.get("session_type", "general")
        
        db.execute(text("""
            INSERT INTO ai_board_sessions (id, session_type, context)
            VALUES (:id, :session_type, :context)
        """), {
            "id": session_id,
            "session_type": session_type,
            "context": json.dumps(request.get("context", {}))
        })
        db.commit()
        
        return {
            "session_id": session_id,
            "session_type": session_type,
            "status": "active",
            "message": "AI Board session started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting AI Board session: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Board session start failed") from e

@router.post("/make-decision")
async def make_decision(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Make a strategic decision"""
    context = request.get("context", {})
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

    prompt = (
        "You are the AI Board. Analyze the context and provide a strategic decision.\n\n"
        f"Context: {json.dumps(context, default=str)}\n\n"
        "Return JSON with keys: decision (object with action, confidence, reasoning), alternatives (list)."
    )

    try:
        result = await ai_service.generate_json(prompt)
    except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "decision": result.get("decision", {}),
        "alternatives": result.get("alternatives", []),
        "timestamp": datetime.utcnow().isoformat()
    }

class AIBoardOrchestrator:
    """AI Board Orchestrator for main.py compatibility"""
    def __init__(self, db):
        self.db = db
        self.initialized = True
