"""
Weathercraft ERP Integration API Routes
Exposes deep bidirectional integration between ERP and AI backend
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/erp/weathercraft", tags=["Weathercraft ERP Integration"])

# Request models
class CustomerSyncRequest(BaseModel):
    customer_id: str
    customer_data: Dict[str, Any]

class EstimateDraftRequest(BaseModel):
    customer_id: str
    property_info: Dict[str, Any]
    user_id: str

class InsightFeedbackRequest(BaseModel):
    insight_id: str
    user_action: str  # accepted, rejected, modified

# Helper to get integration instance
async def get_integration(request: Request):
    """Get Weathercraft integration from app state"""
    if not hasattr(request.app.state, 'weathercraft_integration'):
        raise HTTPException(status_code=503, detail="Weathercraft integration not initialized")
    return request.app.state.weathercraft_integration

# =========================================================================
# CUSTOMER SYNC ENDPOINTS
# =========================================================================

@router.post("/customers/sync")
async def sync_customer(
    req: CustomerSyncRequest,
    integration = Depends(get_integration)
):
    """
    Sync customer from ERP to backend with AI enrichment

    When customer is created/updated in Weathercraft ERP:
    1. Customer data synced to backend
    2. AI analyzes customer and generates insights
    3. Enrichments returned to ERP for display
    """
    try:
        result = await integration.sync_customer_to_backend(
            customer_id=req.customer_id,
            customer_data=req.customer_data
        )
        return result
    except Exception as e:
        logger.exception("Customer sync error")
        raise HTTPException(status_code=500, detail="Customer sync failed") from e

@router.get("/customers/{customer_id}/unified")
async def get_unified_customer_view(
    customer_id: str,
    integration = Depends(get_integration)
):
    """
    Get complete unified view of customer across ERP and AI systems

    Returns:
    - Customer base data
    - AI enrichments (churn risk, upsell potential, predictions)
    - AI insights and recommendations
    - Workflow history
    - Complete jobs and estimates
    - Relationship strength score
    """
    try:
        view = await integration.get_unified_customer_view(customer_id)
        return view
    except Exception as e:
        logger.exception("Unified view error")
        raise HTTPException(status_code=500, detail="Unified customer view failed") from e

# =========================================================================
# WORKFLOW TRIGGER ENDPOINTS
# =========================================================================

@router.post("/estimates/generate-draft")
async def generate_estimate_draft(
    req: EstimateDraftRequest,
    integration = Depends(get_integration)
):
    """
    ERP user clicks 'Generate AI Draft' → triggers workflow

    Flow:
    1. ERP sends property info
    2. Backend executes EstimateWorkflow
    3. AI analyzes property and generates pricing
    4. Draft estimate created with status='draft'
    5. Result returned to ERP for human review

    **Key**: Estimate stays in 'draft' status until ERP user approves
    """
    try:
        result = await integration.trigger_estimate_workflow_from_erp(
            customer_id=req.customer_id,
            property_info=req.property_info,
            user_id=req.user_id
        )
        return result
    except Exception as e:
        logger.exception("Estimate draft generation error")
        raise HTTPException(status_code=500, detail="Estimate draft generation failed") from e

@router.get("/estimates/{estimate_id}/ai-analysis")
async def get_estimate_ai_analysis(
    estimate_id: str,
    integration = Depends(get_integration)
):
    """
    Get AI analysis of an estimate for ERP display

    Shows:
    - Confidence score
    - Pricing breakdown
    - Comparison to similar jobs
    - Risk factors
    """
    try:
        insights = await integration.get_erp_insights(
            entity_type="estimate",
            entity_id=estimate_id
        )
        return {"insights": insights}
    except Exception as e:
        logger.exception("Estimate analysis error")
        raise HTTPException(status_code=500, detail="Estimate AI analysis failed") from e

# =========================================================================
# AI INSIGHTS ENDPOINTS
# =========================================================================

@router.get("/insights")
async def get_ai_insights(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    unviewed_only: bool = False,
    integration = Depends(get_integration)
):
    """
    Get AI insights for ERP to display

    Use cases:
    - Dashboard: Show all unviewed insights
    - Customer page: Show insights for specific customer
    - Job page: Show insights for specific job

    Insight types:
    - customer_enrichment: AI analysis of customer
    - ai_estimate_draft: Draft estimate ready for review
    - recommendation: AI-generated action item
    - prediction: Future event prediction
    - alert: Important notification
    """
    try:
        insights = await integration.get_erp_insights(
            entity_type=entity_type,
            entity_id=entity_id,
            unviewed_only=unviewed_only
        )
        return {"insights": insights, "count": len(insights)}
    except Exception as e:
        logger.exception("Get insights error")
        raise HTTPException(status_code=500, detail="Failed to fetch insights") from e

@router.post("/insights/{insight_id}/feedback")
async def provide_insight_feedback(
    insight_id: str,
    req: InsightFeedbackRequest,
    integration = Depends(get_integration)
):
    """
    ERP user provides feedback on AI insight

    Actions:
    - accepted: User approved and used the insight
    - rejected: User dismissed the insight
    - modified: User edited AI suggestion

    This feedback improves future AI recommendations
    """
    try:
        await integration.mark_insight_viewed(
            insight_id=insight_id,
            user_action=req.user_action
        )
        return {"status": "feedback_recorded", "insight_id": insight_id}
    except Exception as e:
        logger.exception("Insight feedback error")
        raise HTTPException(status_code=500, detail="Failed to record insight feedback") from e

# =========================================================================
# SYNC STATUS ENDPOINTS
# =========================================================================

@router.get("/sync/status")
async def get_sync_status(
    integration = Depends(get_integration)
):
    """
    Get overall ERP-Backend sync status

    Shows:
    - Total entities synced
    - Last sync times
    - Sync health
    - Pending workflows
    """
    try:
        async with integration.db_pool.acquire() as conn:
            # Count synced entities
            sync_counts = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_synced,
                    COUNT(*) FILTER (WHERE sync_direction = 'erp_to_backend') as erp_to_backend,
                    COUNT(*) FILTER (WHERE sync_direction = 'backend_to_erp') as backend_to_erp,
                    MAX(last_synced_at) as last_sync
                FROM erp_backend_sync
            """)

            # Count pending workflows
            pending_workflows = await conn.fetchval("""
                SELECT COUNT(*) FROM erp_workflow_triggers
                WHERE completed_at IS NULL
            """)

            # Count undelivered insights
            pending_insights = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_to_erp_insights
                WHERE delivered_to_erp = false
            """)

        return {
            "status": "healthy",
            "sync_stats": dict(sync_counts) if sync_counts else {},
            "pending_workflows": pending_workflows,
            "pending_insights": pending_insights,
            "integration_active": True
        }
    except Exception as e:
        logger.exception("Sync status error")
        raise HTTPException(status_code=500, detail="Failed to fetch sync status") from e

@router.get("/health")
async def integration_health():
    """Health check for Weathercraft integration"""
    return {
        "status": "healthy",
        "service": "weathercraft-erp-integration",
        "version": "1.0.0",
        "features": [
            "bidirectional_sync",
            "ai_enrichment",
            "workflow_triggers",
            "unified_customer_view",
            "deep_relationships"
        ]
    }
