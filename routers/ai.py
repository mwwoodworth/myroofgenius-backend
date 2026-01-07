
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
import json
from datetime import datetime
import logging
from core.supabase_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])

def get_db():
    """Database dependency"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/board/status")
async def get_ai_board_status(db: Session = Depends(get_db)):
    """Get AI board status"""
    try:
        # Get agent count
        result = db.execute(text("SELECT COUNT(*) FROM ai_agents WHERE status = 'active'"))
        active_agents = result.scalar() or 0
        
        return {
            "status": "operational",
            "active_agents": active_agents,
            "total_agents": active_agents,
            "last_sync": datetime.now().isoformat(),
            "health": "healthy" if active_agents > 0 else "degraded",
        }
    except Exception as e:
        logger.error("Failed to fetch AI board status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch AI board status")

@router.get("/agents")
async def get_ai_agents(db: Session = Depends(get_db)):
    """Get all AI agents"""
    try:
        result = db.execute(text("""
            SELECT id, name, type, status, capabilities
            FROM ai_agents
            ORDER BY name
        """))
        agents = []
        for row in result:
            agents.append({
                "id": str(row.id),
                "name": row.name,
                "type": row.type,
                "status": row.status,
                "capabilities": row.capabilities if row.capabilities else []
            })
        return {"agents": agents}
    except Exception as e:
        logger.error("Failed to fetch AI agents: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch AI agents")
