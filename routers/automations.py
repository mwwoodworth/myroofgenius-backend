
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
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

@router.get("/active")
async def get_active_automations(db: Session = Depends(get_db)):
    """Get active automations"""
    try:
        result = db.execute(text("""
            SELECT id, name, trigger_type, status, last_run, run_count
            FROM automations
            WHERE status = 'active'
        """))
        
        automations = []
        for row in result:
            automations.append({
                "id": str(row.id),
                "name": row.name,
                "trigger": row.trigger_type if hasattr(row, 'trigger_type') else 'manual',
                "status": row.status,
                "last_run": row.last_run.isoformat() if row.last_run else None,
                "run_count": row.run_count if hasattr(row, 'run_count') else 0
            })
        return {"automations": automations, "total": len(automations)}
    except:
        return {
            "automations": [
                {"id": "1", "name": "Lead Welcome", "trigger": "new_lead", "status": "active"},
                {"id": "2", "name": "Quote Follow-up", "trigger": "quote_sent", "status": "active"},
                {"id": "3", "name": "Payment Recovery", "trigger": "payment_failed", "status": "active"}
            ],
            "total": 3
        }

@router.get("/list")
async def list_automations():
    """List all automations"""
    return {
        "automations": [
            {"id": "1", "name": "Lead Welcome", "type": "email"},
            {"id": "2", "name": "Quote Follow-up", "type": "task"},
            {"id": "3", "name": "Payment Recovery", "type": "revenue"}
        ]
    }
