
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
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

@router.get("/pathways")
async def get_neural_pathways(db: Session = Depends(get_db)):
    """Get neural pathways between agents"""
    try:
        result = db.execute(text("""
            SELECT np.*, 
                   a1.name as source_name,
                   a2.name as target_name
            FROM neural_pathways np
            JOIN ai_agents a1 ON np.source_agent_id = a1.id
            JOIN ai_agents a2 ON np.target_agent_id = a2.id
        """))
        
        pathways = []
        for row in result:
            pathways.append({
                "id": str(row.id),
                "source": row.source_name,
                "target": row.target_name,
                "type": row.pathway_type,
                "strength": row.strength
            })
        return {"pathways": pathways, "total": len(pathways)}
    except Exception as e:
        logger.error("Failed to fetch neural pathways: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch neural pathways")

@router.get("/status")
async def get_neural_status(db: Session = Depends(get_db)):
    """Get neural network status"""
    try:
        connections = db.execute(text("SELECT COUNT(*) FROM neural_pathways")).scalar() or 0
        active_agents = db.execute(
            text("SELECT COUNT(*) FROM ai_agents WHERE status = 'active'")
        ).scalar() or 0
        throughput = db.execute(
            text(
                "SELECT COUNT(*) FROM ai_agent_executions "
                "WHERE created_at >= NOW() - INTERVAL '1 minute'"
            )
        ).scalar() or 0
        latency_result = db.execute(
            text(
                "SELECT AVG(total_duration_ms) "
                "FROM ai_agent_executions "
                "WHERE created_at >= NOW() - INTERVAL '15 minutes'"
            )
        ).scalar()
        latency_ms = float(latency_result) if latency_result is not None else None

        status = "active" if active_agents > 0 else "degraded"
        health = "optimal" if latency_ms is not None and latency_ms < 2000 else "degraded"

        return {
            "status": status,
            "connections": connections,
            "active_agents": active_agents,
            "throughput": throughput,
            "latency_ms": latency_ms,
            "health": health
        }
    except Exception as e:
        logger.error("Failed to compute neural status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compute neural status")
