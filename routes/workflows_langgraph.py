"""
LangGraph Workflow API Routes
Endpoints for executing and monitoring AI-powered workflows
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["LangGraph Workflows"])

# Request models
class EstimateWorkflowRequest(BaseModel):
    customer_id: str
    property_info: Dict[str, Any]
    user_id: Optional[str] = None

# Helper to get db_pool from app state
async def get_db_pool(request: Request):
    return request.app.state.db_pool

@router.post("/estimate/execute")
async def execute_estimate_workflow(
    req: EstimateWorkflowRequest,
    db_pool = Depends(get_db_pool)
):
    """
    Execute estimate generation workflow

    Orchestrates AI agents to create intelligent estimates:
    1. Fetch customer data
    2. Analyze property with AI
    3. Generate pricing
    4. Create estimate record

    **Time**: ~30 seconds (vs 45 minutes manual)
    """
    try:
        try:
            from workflows.estimate import EstimateWorkflow
        except (ImportError, ModuleNotFoundError) as import_error:
            logger.error("LangGraph workflow dependencies unavailable: %s", import_error)
            raise HTTPException(
                status_code=501,
                detail="LangGraph workflows are not available in this deployment (missing dependencies).",
            ) from import_error

        workflow = EstimateWorkflow(db_pool)

        result = await workflow.execute(
            customer_id=req.customer_id,
            property_info=req.property_info,
            user_id=req.user_id
        )

        return result

    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: UUID,
    db_pool = Depends(get_db_pool)
):
    """
    Get workflow execution status and results

    Returns complete workflow state including:
    - Current status (running/completed/failed)
    - Execution steps with timestamps
    - Agent calls and durations
    - Final results
    """
    try:
        try:
            from workflows.state_manager import WorkflowStateManager
        except (ImportError, ModuleNotFoundError) as import_error:
            logger.error("LangGraph workflow dependencies unavailable: %s", import_error)
            raise HTTPException(
                status_code=501,
                detail="LangGraph workflows are not available in this deployment (missing dependencies).",
            ) from import_error

        state_manager = WorkflowStateManager(db_pool)
        try:
            normalized_workflow_id = str(UUID(str(workflow_id)))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid workflow_id format. Expected UUID.")

        status = await state_manager.get_workflow_status(normalized_workflow_id)
        return status

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/performance")
async def get_workflow_performance(db_pool = Depends(get_db_pool)):
    """
    Get workflow performance analytics

    Returns metrics for all workflow types:
    - Total executions
    - Average duration
    - Success/failure rates
    """
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM workflow_performance
            """)

            return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/agents")
async def get_agent_usage(db_pool = Depends(get_db_pool)):
    """
    Get AI agent usage statistics

    Returns metrics for all AI agents:
    - Total calls
    - Success rate
    - Average duration
    - Last used timestamp
    """
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM agent_usage
            """)

            return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching agent usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def workflow_health():
    """Health check for workflow system"""
    return {
        "status": "healthy",
        "service": "langgraph-workflows",
        "version": "1.0.0",
        "features": [
            "estimate_generation",
            "state_persistence",
            "agent_tracking",
            "performance_analytics"
        ]
    }
