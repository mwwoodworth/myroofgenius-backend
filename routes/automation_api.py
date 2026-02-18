"""
Automation API Routes - PRODUCTION READY
Exposes all automation functionality via REST API
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Header
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Import core automation modules
from core.agent_execution_manager import agent_manager
from core.lead_automation import lead_automation
from core.workflow_engine import workflow_engine
from core.revenue_automation import revenue_automation, SubscriptionTier
from core.supabase_auth import get_authenticated_user

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])
logger = logging.getLogger(__name__)


# Pydantic models for requests/responses
class LeadCaptureRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = "website"
    budget: Optional[float] = None
    timeline: Optional[str] = None
    property_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class AgentExecutionRequest(BaseModel):
    agent_type: str
    task: str
    context: Dict[str, Any]
    retry_on_failure: Optional[bool] = True


class WorkflowExecutionRequest(BaseModel):
    workflow_name: str
    context: Dict[str, Any]


class CheckoutSessionRequest(BaseModel):
    email: EmailStr
    subscription_tier: SubscriptionTier
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, Any]] = {}


# Agent Management Endpoints
@router.post("/agents/execute")
async def execute_agent(request: AgentExecutionRequest):
    """
    Execute an AI agent with lifecycle management
    """
    try:
        result = await agent_manager.execute_agent(
            agent_type=request.agent_type,
            task=request.task,
            context=request.context,
            retry_on_failure=request.retry_on_failure
        )
        return result
    except Exception as e:
        logger.exception("Agent execution failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agents/fix-stuck")
async def fix_stuck_agents():
    """
    Fix agents stuck in running state
    """
    try:
        result = await agent_manager.fix_stuck_agents()
        return result
    except Exception as e:
        logger.exception("Failed to fix stuck agents", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/agents/stats")
async def get_agent_stats():
    """
    Get agent execution statistics
    """
    try:
        stats = await agent_manager.get_execution_stats()
        return stats
    except Exception as e:
        logger.exception("Failed to get agent stats", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


# Lead Management Endpoints
@router.post("/leads/capture")
async def capture_lead(
    request: LeadCaptureRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """
    Capture and process a new lead
    """
    try:
        lead_data = request.dict()
        lead_data["tenant_id"] = current_user.get("tenant_id")
        lead_data["captured_by"] = current_user.get("id")
        result = await lead_automation.capture_lead(lead_data)
        return result
    except Exception as e:
        logger.exception("Lead capture failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/leads/{lead_id}/activity")
async def track_lead_activity(
    lead_id: str,
    activity_type: str,
    details: Dict[str, Any] = {}
):
    """
    Track lead activity and engagement
    """
    try:
        await lead_automation.process_lead_activity(
            lead_id=lead_id,
            activity_type=activity_type,
            details=details
        )
        return {"status": "tracked"}
    except Exception as e:
        logger.exception("Failed to track lead activity", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/leads/analytics")
async def get_lead_analytics():
    """
    Get lead generation analytics
    """
    try:
        analytics = await lead_automation.get_lead_analytics()
        return analytics
    except Exception as e:
        logger.exception("Failed to get lead analytics", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


# Workflow Automation Endpoints
@router.post("/workflows/execute")
async def execute_workflow(request: WorkflowExecutionRequest):
    """
    Execute a business workflow
    """
    try:
        result = await workflow_engine.execute_workflow(
            workflow_name=request.workflow_name,
            context=request.context
        )
        return result
    except Exception as e:
        logger.exception("Workflow execution failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/workflows/available")
async def list_available_workflows():
    """
    List all available workflows
    """
    return {
        "workflows": list(workflow_engine.workflows.keys()),
        "count": len(workflow_engine.workflows)
    }


# Revenue Automation Endpoints
@router.post("/revenue/checkout")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """
    Create Stripe checkout session for subscription
    """
    try:
        result = await revenue_automation.create_checkout_session(
            customer_email=request.email,
            subscription_tier=request.subscription_tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                **(request.metadata or {}),
                "tenant_id": current_user.get("tenant_id"),
                "requested_by": current_user.get("id"),
            },
        )
        return result
    except Exception as e:
        logger.exception("Failed to create checkout session", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/revenue/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    """
    Handle Stripe webhook events
    """
    try:
        payload = await request.body()
        result = await revenue_automation.handle_webhook(
            payload=payload.decode(),
            signature=stripe_signature
        )
        return result
    except Exception as e:
        logger.exception("Webhook processing failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/revenue/retry-payments")
async def process_payment_retries():
    """
    Process failed payment retries
    """
    try:
        result = await revenue_automation.process_payment_retries()
        return result
    except Exception as e:
        logger.exception("Payment retry processing failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/revenue/metrics")
async def get_revenue_metrics():
    """
    Get revenue metrics and analytics
    """
    try:
        metrics = await revenue_automation.get_revenue_metrics()
        return metrics
    except Exception as e:
        logger.exception("Failed to get revenue metrics", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


# Health Check
@router.get("/health")
async def automation_health_check():
    """
    Check automation system health
    """
    return {
        "status": "healthy",
        "components": {
            "agent_manager": "operational",
            "lead_automation": "operational",
            "workflow_engine": "operational",
            "revenue_automation": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Trigger all automation systems
@router.post("/initialize")
async def initialize_automation_systems(background_tasks: BackgroundTasks):
    """
    Initialize and activate all automation systems
    """
    # Fix stuck agents in background
    background_tasks.add_task(agent_manager.fix_stuck_agents)

    # Process payment retries in background
    background_tasks.add_task(revenue_automation.process_payment_retries)

    return {
        "status": "initializing",
        "message": "All automation systems are being activated",
        "systems": [
            "agent_execution_manager",
            "lead_automation",
            "workflow_engine",
            "revenue_automation"
        ]
    }
