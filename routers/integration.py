"""
Integration Router - MCP and AI Agent Communication Endpoints
Provides unified API for MCP servers and AI agent orchestration
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

from services.mcp_service import mcp_service, MCPRequest
from services.ai_agent_service import ai_agent_service, TaskRequest, WorkflowRequest, TaskPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integration", tags=["Integration"])

# ============================================================================
# MCP SERVER ENDPOINTS
# ============================================================================

@router.get("/mcp/health")
async def check_mcp_health():
    """Check health status of all MCP servers"""
    try:
        health_status = await mcp_service.check_all_servers()
        return health_status
    except Exception as e:
        logger.error(f"Error checking MCP health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/health/{server_name}")
async def check_mcp_server_health(server_name: str):
    """Check health status of a specific MCP server"""
    try:
        health_status = await mcp_service.check_server_health(server_name)
        if "error" in health_status:
            raise HTTPException(status_code=404, detail=health_status["error"])
        return health_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking MCP server {server_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/status")
async def get_mcp_status():
    """Get current status of all MCP servers"""
    try:
        return mcp_service.get_server_status()
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/call")
async def call_mcp_server(request: MCPRequest):
    """Make a direct call to an MCP server"""
    try:
        response = await mcp_service.call_mcp_server(request)
        
        if not response.success:
            # Return error details but don't raise exception to allow client to handle
            return {
                "success": False,
                "server": response.server,
                "error": response.error,
                "timestamp": response.timestamp.isoformat(),
                "execution_time": response.execution_time
            }
        
        return {
            "success": True,
            "server": response.server,
            "data": response.data,
            "timestamp": response.timestamp.isoformat(),
            "execution_time": response.execution_time
        }
    except Exception as e:
        logger.error(f"Error calling MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/filesystem/{operation}")
async def filesystem_operation(operation: str, request: Dict[str, Any]):
    """Perform filesystem operations via MCP"""
    try:
        path = request.get("path")
        content = request.get("content")
        
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        
        response = await mcp_service.filesystem_operation(operation, path, content)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "operation": operation,
            "path": path,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in filesystem operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/database/query")
async def database_query(request: Dict[str, Any]):
    """Execute database query via MCP"""
    try:
        query = request.get("query")
        params = request.get("params", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        response = await mcp_service.database_query(query, params)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "query": query,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in database query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/github/{operation}")
async def github_operation(operation: str, request: Dict[str, Any]):
    """Perform GitHub operations via MCP"""
    try:
        repo = request.get("repo")
        if not repo:
            raise HTTPException(status_code=400, detail="Repository is required")
        
        # Remove repo from request to avoid duplicate in kwargs
        operation_params = {k: v for k, v in request.items() if k != "repo"}
        
        response = await mcp_service.github_operation(operation, repo, **operation_params)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "operation": operation,
            "repo": repo,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GitHub operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/fetch")
async def fetch_data(request: Dict[str, Any]):
    """Fetch data from external APIs via MCP"""
    try:
        url = request.get("url")
        method = request.get("method", "GET")
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Remove url and method from request to avoid duplicate in kwargs
        fetch_params = {k: v for k, v in request.items() if k not in ["url", "method"]}
        
        response = await mcp_service.fetch_data(url, method, **fetch_params)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "url": url,
            "method": method,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/automation/trigger")
async def trigger_automation(request: Dict[str, Any]):
    """Trigger automation workflow via MCP"""
    try:
        automation_id = request.get("automation_id")
        context = request.get("context", {})
        
        if not automation_id:
            raise HTTPException(status_code=400, detail="Automation ID is required")
        
        response = await mcp_service.trigger_automation(automation_id, context)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "automation_id": automation_id,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/analytics/{metric}")
async def get_analytics(metric: str, timeframe: str = "24h", filters: Optional[str] = None):
    """Get analytics data via MCP"""
    try:
        filter_dict = json.loads(filters) if filters else {}
        response = await mcp_service.get_analytics(metric, timeframe, filter_dict)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "success": True,
            "metric": metric,
            "timeframe": timeframe,
            "result": response.data,
            "execution_time": response.execution_time
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AI AGENT ENDPOINTS
# ============================================================================

@router.get("/agents/health")
async def check_agents_health():
    """Check health status of all AI agents"""
    try:
        health_status = await ai_agent_service.check_all_agents()
        return health_status
    except Exception as e:
        logger.error(f"Error checking AI agents health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/health/{agent_name}")
async def check_agent_health(agent_name: str):
    """Check health status of a specific AI agent"""
    try:
        health_status = await ai_agent_service.check_agent_health(agent_name)
        if "error" in health_status:
            raise HTTPException(status_code=404, detail=health_status["error"])
        return health_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking AI agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/status")
async def get_agents_status():
    """Get current status of all AI agents"""
    try:
        return ai_agent_service.get_agent_status()
    except Exception as e:
        logger.error(f"Error getting AI agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/delegate")
async def delegate_task(request: TaskRequest):
    """Delegate a task to an AI agent"""
    try:
        response = await ai_agent_service.delegate_task(request)
        
        if not response.success:
            # Return error details but don't raise exception to allow client to handle
            return {
                "success": False,
                "task_id": response.task_id,
                "agent": response.agent_name,
                "error": response.error,
                "timestamp": response.timestamp.isoformat(),
                "execution_time": response.execution_time
            }
        
        return {
            "success": True,
            "task_id": response.task_id,
            "agent": response.agent_name,
            "result": response.result,
            "metadata": response.metadata,
            "timestamp": response.timestamp.isoformat(),
            "execution_time": response.execution_time
        }
    except Exception as e:
        logger.error(f"Error delegating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/workflow")
async def execute_workflow(workflow: WorkflowRequest, background_tasks: BackgroundTasks):
    """Execute a multi-step workflow across multiple AI agents"""
    try:
        # For long-running workflows, execute in background
        if len(workflow.steps) > 5:
            background_tasks.add_task(ai_agent_service.execute_workflow, workflow)
            return {
                "workflow_id": workflow.workflow_id,
                "status": "started",
                "message": "Workflow execution started in background",
                "steps": len(workflow.steps),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Execute immediately for smaller workflows
            result = await ai_agent_service.execute_workflow(workflow)
            return result
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a specific workflow execution"""
    try:
        status = ai_agent_service.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/capabilities")
async def get_agent_capabilities():
    """Get capabilities of all AI agents"""
    try:
        capabilities = {}
        for agent_name, agent in ai_agent_service.agents.items():
            capabilities[agent_name] = {
                "specialization": agent.specialization,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "input_schema": cap.input_schema,
                        "output_schema": cap.output_schema
                    }
                    for cap in agent.capabilities
                ],
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "current_tasks": agent.current_tasks
            }
        return capabilities
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# UNIFIED STATUS AND MONITORING
# ============================================================================

@router.get("/status")
async def get_integration_status():
    """Get unified status of all MCP servers and AI agents"""
    try:
        mcp_status = await mcp_service.check_all_servers()
        agents_status = await ai_agent_service.check_all_agents()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "mcp_servers": mcp_status,
            "ai_agents": agents_status,
            "system_health": {
                "mcp_healthy": mcp_status["summary"]["healthy"],
                "mcp_total": mcp_status["summary"]["total"],
                "agents_healthy": agents_status["summary"]["healthy"],
                "agents_total": agents_status["summary"]["total"],
                "overall_health": "healthy" if (
                    mcp_status["summary"]["healthy"] > 0 and 
                    agents_status["summary"]["healthy"] > 0
                ) else "degraded"
            }
        }
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# QUICK ACTION ENDPOINTS
# ============================================================================

@router.post("/quick/analyze-revenue")
async def quick_analyze_revenue(request: Dict[str, Any]):
    """Quick revenue analysis using data analyst agent"""
    try:
        task_request = TaskRequest(
            agent_name="data_analyst",
            task_type="analyze_revenue",
            context=request,
            priority=TaskPriority.NORMAL
        )
        
        response = await ai_agent_service.delegate_task(task_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "analysis": response.result,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick revenue analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick/generate-proposal")
async def quick_generate_proposal(request: Dict[str, Any]):
    """Quick proposal generation using content creator agent"""
    try:
        task_request = TaskRequest(
            agent_name="content_creator",
            task_type="generate_proposal",
            context=request,
            priority=TaskPriority.HIGH
        )
        
        response = await ai_agent_service.delegate_task(task_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "proposal": response.result,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick proposal generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick/optimize-schedule")
async def quick_optimize_schedule(request: Dict[str, Any]):
    """Quick schedule optimization using operations manager agent"""
    try:
        task_request = TaskRequest(
            agent_name="operations_manager",
            task_type="schedule_optimization",
            context=request,
            priority=TaskPriority.HIGH
        )
        
        response = await ai_agent_service.delegate_task(task_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "optimized_schedule": response.result,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick schedule optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick/customer-support")
async def quick_customer_support(request: Dict[str, Any]):
    """Quick customer support response using customer success agent"""
    try:
        task_request = TaskRequest(
            agent_name="customer_success",
            task_type="generate_support_response",
            context=request,
            priority=TaskPriority.HIGH
        )
        
        response = await ai_agent_service.delegate_task(task_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)
        
        return {
            "support_response": response.result,
            "execution_time": response.execution_time,
            "timestamp": response.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick customer support: {e}")
        raise HTTPException(status_code=500, detail=str(e))