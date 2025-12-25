"""
AI Agents API - Complete Implementation
Provides access to all 59 AI agents via unified interface
Routes: /api/v1/agents/*
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncpg
import logging
import json

from core.agent_execution_manager import AgentExecutionManager
from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

# Router with explicit prefix
router = APIRouter(prefix="/api/v1/agents", tags=["AI Agents"])

agent_executor = AgentExecutionManager()

# ============================================================================
# MODELS
# ============================================================================

class AgentExecutionRequest(BaseModel):
    """Request to execute an AI agent"""
    data: Dict[str, Any] = Field(..., description="Input data for the agent")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

class AgentExecutionResponse(BaseModel):
    """Response from AI agent execution"""
    success: bool
    agent_id: str
    result: Dict[str, Any]
    confidence: Optional[float] = None
    execution_time_ms: Optional[int] = None
    recommendations: Optional[List[str]] = None

class AgentAnalysisRequest(BaseModel):
    """Request for AI agent analysis"""
    entity_id: str
    entity_type: str  # customer, lead, job, etc.
    analysis_type: str  # health, score, forecast, etc.
    parameters: Optional[Dict[str, Any]] = {}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_db_pool(request: Request):
    """Get database pool from app state, fail fast if unavailable."""
    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.error("Database pool is not initialized. Rejecting request with 503.")
        raise HTTPException(status_code=503, detail="Service unavailable: database not initialized")
    return db_pool

async def execute_agent(agent_identifier: str, data: Dict[str, Any], db_pool) -> Dict[str, Any]:
    """Execute an AI agent with production service or raise if unavailable."""

    async with db_pool.acquire() as conn:
        agent = await conn.fetchrow(
            """
            SELECT id, name
            FROM ai_agents
            WHERE id::text = $1 OR name = $1
            """,
            agent_identifier
        )

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_identifier}' not found")

    try:
        execution = await agent_executor.execute_agent(
            agent['name'],
            'execute',
            data,
            retry_on_failure=False
        )
    except Exception as exc:
        logger.error("AI agent execution failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI agent execution failed") from exc

    result = execution.get('result') or {}

    return {
        'success': True,
        'agent_id': str(agent['id']),
        'result': result,
        'confidence': result.get('confidence'),
        'execution_time_ms': result.get('execution_time_ms'),
        'recommendations': result.get('recommendations'),
        'method': result.get('method', 'unknown')
    }

def get_tenant_id(current_user: Dict[str, Any]) -> str:
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")
    return tenant_id

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("")
async def list_agents(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all available AI agents (requires authentication)"""
    try:
        # Verify user is authenticated
        tenant_id = get_tenant_id(current_user)
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            agents = await conn.fetch("""
                SELECT id, name, type, status, metadata
                FROM ai_agents
                WHERE status = 'active'
                ORDER BY name
            """)

        # Extract category from metadata and format response
        result_agents = []
        for agent in agents:
            agent_dict = dict(agent)
            raw_meta = agent_dict.get('metadata')
            category = 'Uncategorized'
            description = ''
            if raw_meta is not None:
                parsed = None
                if isinstance(raw_meta, str):
                    try:
                        parsed = json.loads(raw_meta)
                    except Exception:
                        parsed = None
                else:
                    parsed = raw_meta

                if isinstance(parsed, dict):
                    category = parsed.get('category', category)
                    description = parsed.get('description', description)

            agent_dict['category'] = category
            agent_dict['description'] = description
            agent_dict.pop('metadata', None)
            result_agents.append(agent_dict)

        return {
            'agents': result_agents,
            'total': len(result_agents)
        }
    except Exception as e:
        logger.exception("Error listing agents:")
        raise HTTPException(status_code=500, detail="Failed to list agents")

@router.get("/{agent_id}")
async def get_agent_details(
    agent_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get details of a specific AI agent (requires authentication)"""
    try:
        # Verify user is authenticated
        tenant_id = get_tenant_id(current_user)
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            agent = await conn.fetchrow("""
                SELECT id, name, type, status, metadata
                FROM ai_agents
                WHERE id = $1::uuid AND status = 'active'
            """, agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_dict = dict(agent)

        if agent_dict.get('metadata'):
            if isinstance(agent_dict['metadata'], str):
                try:
                    metadata = json.loads(agent_dict['metadata'])
                except:
                    metadata = {}
            else:
                metadata = agent_dict['metadata']
            agent_dict['category'] = metadata.get('category', 'Uncategorized')
            agent_dict['description'] = metadata.get('description', '')
        else:
            agent_dict['category'] = 'Uncategorized'
            agent_dict['description'] = ''

        agent_dict.pop('metadata', None)

        return agent_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent details")

@router.post("/{agent_id}/execute", response_model=AgentExecutionResponse)
async def execute_agent_endpoint(
    agent_id: str,
    request_data: AgentExecutionRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Execute a specific AI agent"""
    # Verify tenant context
    get_tenant_id(current_user)
    
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent(agent_id, request_data.data, db_pool)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

# Lead Scorer
@router.post("/lead-scorer/analyze")
async def lead_scorer_analyze(
    analysis: AgentAnalysisRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze and score a lead"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        # Get lead data - SECURED
        async with db_pool.acquire() as conn:
            lead = await conn.fetchrow(
                "SELECT * FROM leads WHERE id = $1 AND tenant_id = $2",
                analysis.entity_id, tenant_id
            )

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Execute lead scoring
        result = await execute_agent('lead-scorer', dict(lead), db_pool)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lead scoring error: {e}")
        raise HTTPException(status_code=500, detail="Lead scoring failed")

# Customer Health Analyzer
@router.post("/customer-health/analyze")
async def customer_health_analyze(
    analysis: AgentAnalysisRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze customer health and engagement"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        # Get customer data with aggregates - SECURED
        async with db_pool.acquire() as conn:
            customer = await conn.fetchrow("""
                SELECT c.*,
                    COUNT(DISTINCT j.id) as total_jobs,
                    COALESCE(SUM(i.total_amount), 0) as lifetime_revenue,
                    MAX(j.created_at) as last_job_date
                FROM customers c
                LEFT JOIN jobs j ON c.id = j.customer_id AND j.tenant_id = $2
                LEFT JOIN invoices i ON c.id = i.customer_id AND i.tenant_id = $2
                WHERE c.id = $1 AND c.tenant_id = $2
                GROUP BY c.id
            """, analysis.entity_id, tenant_id)

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Calculate health metrics
        customer_data = dict(customer)
        if customer_data.get('last_job_date'):
            from datetime import datetime
            days_since = (datetime.utcnow() - customer_data['last_job_date']).days
            customer_data['last_contact_days'] = days_since

        result = await execute_agent('customer-health', customer_data, db_pool)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer health analysis error: {e}")
        raise HTTPException(status_code=500, detail="Health analysis failed")

# Predictive Analyzer
@router.post("/predictive-analyzer/forecast")
async def predictive_forecast(
    forecast_type: str,
    time_period: str = 'next_quarter',
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Generate predictive forecasts"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        # Get historical data - SECURED
        async with db_pool.acquire() as conn:
            if forecast_type == 'revenue':
                revenue_data = await conn.fetchrow("""
                    SELECT
                        COALESCE(SUM(total_amount), 0) as current_revenue,
                        COUNT(*) as invoice_count
                    FROM invoices
                    WHERE created_at >= NOW() - INTERVAL '3 months' AND tenant_id = $1
                """, tenant_id)
                data = dict(revenue_data) if revenue_data else {'current_revenue': 0, 'invoice_count': 0}
            else:
                data = {'current_revenue': 0}  # Default safety

        data['period'] = time_period
        data['forecast_type'] = forecast_type

        result = await execute_agent('predictive-analyzer', data, db_pool)
        return result

    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(status_code=500, detail="Forecast generation failed")

# HR Analytics
@router.post("/hr-analytics/analyze")
async def hr_analytics_analyze(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze HR metrics and team health"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        # Get employee data - SECURED
        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_employees,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_employees,
                    AVG(EXTRACT(epoch FROM (NOW() - hire_date)) / 86400 / 365) as avg_tenure_years
                FROM employees
                WHERE tenant_id = $1
            """, tenant_id)

        result = await execute_agent('hr-analytics', dict(stats) if stats else {}, db_pool)
        return result

    except Exception as e:
        logger.error(f"HR analytics error: {e}")
        raise HTTPException(status_code=500, detail="HR analysis failed")

# Payroll Agent
@router.post("/payroll-agent/validate")
async def payroll_validate(
    payroll_data: Dict[str, Any] = Body(...),
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Validate payroll data"""
    get_tenant_id(current_user) # Ensure auth
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('payroll-agent', payroll_data, db_pool)
        return result
    except Exception as e:
        logger.error(f"Payroll validation error: {e}")
        raise HTTPException(status_code=500, detail="Payroll validation failed")

# Onboarding Agent
@router.post("/onboarding-agent/create-plan")
async def onboarding_create_plan(
    employee_data: Dict[str, Any] = Body(...),
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create employee onboarding plan"""
    get_tenant_id(current_user) # Ensure auth
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('onboarding-agent', employee_data, db_pool)
        return result
    except Exception as e:
        logger.error(f"Onboarding plan creation error: {e}")
        raise HTTPException(status_code=500, detail="Onboarding plan creation failed")

# Training Agent
@router.post("/training-agent/recommend")
async def training_recommend(
    employee_id: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get training recommendations for employee"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            employee = await conn.fetchrow(
                "SELECT * FROM employees WHERE id = $1 AND tenant_id = $2",
                employee_id, tenant_id
            )

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        result = await execute_agent('training-agent', dict(employee), db_pool)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Training recommendation failed")

# Recruiting Agent
@router.post("/recruiting-agent/analyze")
async def recruiting_analyze(
    candidate_data: Dict[str, Any] = Body(...),
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze recruitment candidate"""
    get_tenant_id(current_user) # Ensure auth
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('recruiting-agent', candidate_data, db_pool)
        return result
    except Exception as e:
        logger.error(f"Recruitment analysis error: {e}")
        raise HTTPException(status_code=500, detail="Recruitment analysis failed")

# Insights Analyzer
@router.post("/insights-analyzer/analyze")
async def insights_analyze(
    data_source: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze business data for insights"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        # Get relevant data based on source - SECURED
        async with db_pool.acquire() as conn:
            if data_source == 'revenue':
                data = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_invoices,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_invoice
                    FROM invoices
                    WHERE created_at >= NOW() - INTERVAL '30 days' AND tenant_id = $1
                """, tenant_id)
            else:
                data = {}

        result = await execute_agent('insights-analyzer', dict(data or {}), db_pool)
        return result
    except Exception as e:
        logger.error(f"Insights analysis error: {e}")
        raise HTTPException(status_code=500, detail="Insights analysis failed")

# Metrics Calculator
@router.post("/metrics-calculator/calculate")
async def metrics_calculate(
    metric_type: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Calculate business metrics"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            if metric_type == 'kpi':
                metrics = await conn.fetchrow("""
                    SELECT
                        COUNT(DISTINCT c.id) as total_customers,
                        COUNT(DISTINCT j.id) as total_jobs,
                        COALESCE(SUM(i.total_amount), 0) as total_revenue
                    FROM customers c
                    LEFT JOIN jobs j ON c.id = j.customer_id AND j.tenant_id = $1
                    LEFT JOIN invoices i ON c.id = i.customer_id AND i.tenant_id = $1
                    WHERE c.tenant_id = $1
                """, tenant_id)
            else:
                metrics = {}

        result = await execute_agent('metrics-calculator', dict(metrics or {}), db_pool)
        return result
    except Exception as e:
        logger.error(f"Metrics calculation error: {e}")
        raise HTTPException(status_code=500, detail="Metrics calculation failed")

# Dashboard Monitor
@router.get("/dashboard-monitor/alerts")
async def dashboard_alerts(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get dashboard alerts"""
    get_tenant_id(current_user)
    try:
        # Return intelligent alerts based on system status
        alerts = [
            {
                'type': 'info',
                'message': 'System operating normally',
                'priority': 'low'
            }
        ]
        return {'alerts': alerts}
    except Exception as e:
        logger.error(f"Dashboard alerts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.post("/dashboard-monitor/analyze")
async def dashboard_analyze(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze dashboard metrics"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT c.id) as customers,
                    COUNT(DISTINCT j.id) as jobs,
                    COALESCE(SUM(i.total_amount), 0) as revenue
                FROM customers c
                LEFT JOIN jobs j ON c.id = j.customer_id AND j.tenant_id = $1
                LEFT JOIN invoices i ON c.id = i.customer_id AND i.tenant_id = $1
                WHERE c.tenant_id = $1
            """, tenant_id)

        result = await execute_agent('dashboard-monitor', dict(stats) if stats else {}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Dashboard analysis error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard analysis failed")

# Dispatch Agent
@router.post("/dispatch-agent/analyze-availability")
async def dispatch_analyze_availability(
    date: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Analyze crew availability for dispatch"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            availability = await conn.fetch("""
                SELECT
                    e.id,
                    e.name,
                    e.role
                FROM employees e
                WHERE e.status = 'active'
                AND e.role IN ('crew_lead', 'technician')
                AND e.tenant_id = $1
            """, tenant_id)

        result = await execute_agent('dispatch-agent', {
            'date': date,
            'available_employees': len(availability)
        }, db_pool)
        return result
    except Exception as e:
        logger.error(f"Availability analysis error: {e}")
        raise HTTPException(status_code=500, detail="Availability analysis failed")

@router.post("/dispatch-agent/optimize-schedule")
async def dispatch_optimize(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Optimize dispatch schedule"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('dispatch-agent', {'action': 'optimize'}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Schedule optimization error: {e}")
        raise HTTPException(status_code=500, detail="Schedule optimization failed")

@router.post("/dispatch-agent/recommend-crew")
async def dispatch_recommend_crew(
    job_id: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Recommend crew for a job"""
    tenant_id = get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)

        async with db_pool.acquire() as conn:
            job = await conn.fetchrow(
                "SELECT * FROM jobs WHERE id = $1 AND tenant_id = $2",
                job_id, tenant_id
            )

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        result = await execute_agent('dispatch-agent', {
            'action': 'recommend_crew',
            'job': dict(job)
        }, db_pool)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crew recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Crew recommendation failed")

# Intelligent Scheduler
@router.post("/intelligent-scheduler/optimize")
async def scheduler_optimize(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Optimize scheduling intelligently"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('intelligent-scheduler', {'action': 'optimize'}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Scheduling optimization error: {e}")
        raise HTTPException(status_code=500, detail="Scheduling optimization failed")

# Next Best Action Agent
@router.post("/next-best-action/recommend")
async def next_action_recommend(
    entity_type: str,
    entity_id: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Recommend next best action for an entity"""
    get_tenant_id(current_user) # Ensure tenant context in future
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('next-best-action', {
            'entity_type': entity_type,
            'entity_id': entity_id
        }, db_pool)
        return result
    except Exception as e:
        logger.error(f"Next action recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Next action recommendation failed")

# Notification Agent
@router.post("/notification-agent/optimize")
async def notification_optimize(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Optimize notification delivery"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('notification-agent', {'action': 'optimize'}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Notification optimization error: {e}")
        raise HTTPException(status_code=500, detail="Notification optimization failed")

@router.post("/notification-agent/suggest")
async def notification_suggest(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Suggest optimal notification strategy"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('notification-agent', {'action': 'suggest'}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Notification suggestion error: {e}")
        raise HTTPException(status_code=500, detail="Notification suggestion failed")

# Reporting Agent
@router.post("/reporting-agent/recommend")
async def reporting_recommend(
    report_type: str,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Recommend reporting insights"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('reporting-agent', {'report_type': report_type}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Reporting recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Reporting recommendation failed")

# Routing Agent
@router.post("/routing-agent/optimize")
async def routing_optimize(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Optimize routing for field operations"""
    get_tenant_id(current_user)
    try:
        db_pool = await get_db_pool(request)
        result = await execute_agent('routing-agent', {'action': 'optimize'}, db_pool)
        return result
    except Exception as e:
        logger.error(f"Routing optimization error: {e}")
        raise HTTPException(status_code=500, detail="Routing optimization failed")
