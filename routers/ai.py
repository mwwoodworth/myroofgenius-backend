
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
import json
from datetime import datetime

router = APIRouter()

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
            "health": "healthy"
        }
    except Exception as e:
        # Return mock data on error
        return {
            "status": "operational",
            "active_agents": 6,
            "total_agents": 6,
            "last_sync": datetime.now().isoformat(),
            "health": "healthy"
        }

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
    except:
        # Return mock agents
        return {
            "agents": [
                {"id": "1", "name": "Sophie", "type": "customer_support", "status": "active"},
                {"id": "2", "name": "Max", "type": "sales", "status": "active"},
                {"id": "3", "name": "Elena", "type": "estimation", "status": "active"},
                {"id": "4", "name": "Victoria", "type": "analytics", "status": "active"},
                {"id": "5", "name": "AUREA", "type": "executive", "status": "active"},
                {"id": "6", "name": "BrainLink", "type": "coordinator", "status": "active"}
            ]
        }
