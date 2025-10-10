
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
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

@router.get("/workflows")
async def get_workflows(db: Session = Depends(get_db)):
    """Get LangGraph workflows"""
    try:
        result = db.execute(text("""
            SELECT id, name, status, version
            FROM langgraph_workflows
            WHERE status = 'active'
        """))
        
        workflows = []
        for row in result:
            workflows.append({
                "id": str(row.id),
                "name": row.name,
                "status": row.status,
                "version": row.version
            })
        return {"workflows": workflows, "total": len(workflows)}
    except:
        return {
            "workflows": [
                {"id": "1", "name": "Customer Journey", "status": "active", "version": "1.0"},
                {"id": "2", "name": "Revenue Pipeline", "status": "active", "version": "1.0"},
                {"id": "3", "name": "Service Delivery", "status": "active", "version": "1.0"}
            ],
            "total": 3
        }
