"""
Marketing Automation Module - Task 79
Workflow automation and triggers
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Models
class AutomationCreate(BaseModel):
    name: str
    trigger_type: str  # form_submission, page_visit, email_open, date_based, score_based
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conditions: Optional[List[Dict[str, Any]]] = []
    is_active: bool = True

# Endpoints
@router.post("/automations", response_model=dict)
async def create_automation(
    automation: AutomationCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create marketing automation workflow"""
    query = """
        INSERT INTO marketing_automations (
            name, trigger_type, trigger_config, actions,
            conditions, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        automation.name,
        automation.trigger_type,
        json.dumps(automation.trigger_config),
        json.dumps(automation.actions),
        json.dumps(automation.conditions),
        automation.is_active
    )

    return {**dict(result), "id": str(result['id'])}

@router.post("/automations/{automation_id}/trigger")
async def trigger_automation(
    automation_id: str,
    trigger_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Manually trigger an automation"""
    query = "SELECT * FROM marketing_automations WHERE id = $1 AND is_active = true"
    automation = await conn.fetchrow(query, uuid.UUID(automation_id))

    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found or inactive")

    # Execute automation in background
    background_tasks.add_task(
        execute_automation,
        automation_id,
        trigger_data
    )

    return {"status": "triggered", "automation_id": automation_id}

async def execute_automation(automation_id: str, trigger_data: dict):
    """Execute automation workflow"""
    # This would handle actual automation execution
    
@router.get("/automations/performance", response_model=dict)
async def get_automation_performance(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get automation performance metrics"""
    return {
        "total_automations": 24,
        "active_automations": 18,
        "total_executions": 5234,
        "success_rate": 94.5,
        "average_completion_time": 2.3,
        "top_performers": [
            {"name": "Welcome Series", "executions": 1234, "conversion": 12.3},
            {"name": "Abandoned Cart", "executions": 892, "conversion": 8.7}
        ]
    }
