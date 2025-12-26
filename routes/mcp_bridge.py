"""
MCP Bridge Routes - Active Integration with BrainOps MCP Bridge
Provides API endpoints for MCP tool discovery and execution
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Bridge"])


class ToolExecutionRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}
    server: Optional[str] = None
    timeout: int = 30


class BrainQueryRequest(BaseModel):
    query: str
    category: Optional[str] = None


class MemoryStoreRequest(BaseModel):
    key: str
    value: Any
    category: str = "general"


@router.get("/health")
async def mcp_health(request: Request):
    """Get MCP Bridge connection status"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        health = await mcp_client.health_check()
        return health
    except Exception as e:
        logger.error(f"MCP health check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/servers")
async def list_mcp_servers(request: Request):
    """List all available MCP servers"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        servers = await mcp_client.list_servers()
        return {
            "servers": servers,
            "count": len(servers)
        }
    except Exception as e:
        logger.error(f"MCP list servers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_mcp_tools(request: Request, server: Optional[str] = None):
    """List all available MCP tools, optionally filtered by server"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        tools = await mcp_client.list_tools(server)
        return {
            "tools": tools,
            "count": len(tools),
            "server_filter": server
        }
    except Exception as e:
        logger.error(f"MCP list tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_mcp_tool(request: Request, body: ToolExecutionRequest):
    """Execute a tool via MCP Bridge"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        result = await mcp_client.execute_tool(
            tool_name=body.tool,
            arguments=body.arguments,
            server_name=body.server,
            timeout=body.timeout
        )
        return result
    except Exception as e:
        logger.error(f"MCP execute tool error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/query")
async def query_brain(request: Request, body: BrainQueryRequest):
    """Query the unified brain via MCP"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        result = await mcp_client.query_brain(body.query, body.category)
        return result
    except Exception as e:
        logger.error(f"MCP brain query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/store")
async def store_memory(request: Request, body: MemoryStoreRequest):
    """Store memory in unified brain via MCP"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        result = await mcp_client.store_memory(body.key, body.value, body.category)
        return result
    except Exception as e:
        logger.error(f"MCP brain store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def mcp_full_status(request: Request):
    """Get comprehensive MCP Bridge status including all servers and tool counts"""
    try:
        mcp_client = getattr(request.app.state, 'mcp_client', None)
        if not mcp_client:
            from services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()

        health = await mcp_client.health_check()
        servers = await mcp_client.list_servers()
        tools = await mcp_client.list_tools()

        return {
            "health": health,
            "servers": {
                "count": len(servers),
                "list": servers
            },
            "tools": {
                "count": len(tools),
                "sample": tools[:10] if tools else []
            },
            "integration_status": "ACTIVE" if health.get("status") == "connected" else "PASSIVE"
        }
    except Exception as e:
        logger.error(f"MCP full status error: {e}")
        return {
            "health": {"status": "error", "error": str(e)},
            "servers": {"count": 0, "list": []},
            "tools": {"count": 0, "sample": []},
            "integration_status": "ERROR"
        }
