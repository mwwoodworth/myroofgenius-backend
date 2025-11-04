"""
MCP Service Layer - Communication with MCP Servers
Handles connections to MCP servers on ports 5001-5006
"""
import asyncio
import httpx
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MCPServer(BaseModel):
    """MCP Server configuration"""
    name: str
    port: int
    url: str
    capabilities: List[str]
    status: str = "unknown"
    last_check: Optional[datetime] = None

class MCPRequest(BaseModel):
    """MCP Request model"""
    server: str
    method: str
    params: Dict[str, Any] = {}
    timeout: int = 30

class MCPResponse(BaseModel):
    """MCP Response model"""
    server: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: datetime
    execution_time: float

class MCPService:
    """Service for communicating with MCP servers"""
    
    def __init__(self):
        self.servers = {
            "filesystem": MCPServer(
                name="filesystem",
                port=5001,
                url="http://localhost:5001",
                capabilities=["read_file", "write_file", "list_directory", "create_directory"]
            ),
            "postgres": MCPServer(
                name="postgres", 
                port=5002,
                url="http://localhost:5002",
                capabilities=["query", "execute", "schema", "backup"]
            ),
            "github": MCPServer(
                name="github",
                port=5003, 
                url="http://localhost:5003",
                capabilities=["create_repo", "commit", "push", "pull_request", "issue"]
            ),
            "fetch": MCPServer(
                name="fetch",
                port=5004,
                url="http://localhost:5004", 
                capabilities=["http_get", "http_post", "scrape", "api_call"]
            ),
            "automation": MCPServer(
                name="automation",
                port=5005,
                url="http://localhost:5005",
                capabilities=["webhook", "schedule", "trigger", "workflow"]
            ),
            "analytics": MCPServer(
                name="analytics",
                port=5006,
                url="http://localhost:5006",
                capabilities=["metrics", "events", "reports", "dashboards"]
            )
        }
        
    async def check_server_health(self, server_name: str) -> Dict[str, Any]:
        """Check health of a specific MCP server"""
        if server_name not in self.servers:
            return {"error": f"Unknown server: {server_name}"}
        
        server = self.servers[server_name]
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{server.url}/health")
                
                if response.status_code == 200:
                    server.status = "healthy"
                    server.last_check = datetime.now()
                    return {
                        "server": server_name,
                        "status": "healthy",
                        "response_time": (datetime.now() - start_time).total_seconds(),
                        "capabilities": server.capabilities,
                        "url": server.url
                    }
                else:
                    server.status = "unhealthy"
                    return {
                        "server": server_name,
                        "status": "unhealthy", 
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            server.status = "offline"
            logger.error(f"Health check failed for {server_name}: {e}")
            return {
                "server": server_name,
                "status": "offline",
                "error": str(e)
            }
    
    async def check_all_servers(self) -> Dict[str, Any]:
        """Check health of all MCP servers"""
        results = {}
        tasks = []
        
        for server_name in self.servers.keys():
            task = self.check_server_health(server_name)
            tasks.append((server_name, task))
        
        for server_name, task in tasks:
            results[server_name] = await task
            
        return {
            "timestamp": datetime.now().isoformat(),
            "servers": results,
            "summary": {
                "total": len(self.servers),
                "healthy": len([r for r in results.values() if r.get("status") == "healthy"]),
                "unhealthy": len([r for r in results.values() if r.get("status") == "unhealthy"]),
                "offline": len([r for r in results.values() if r.get("status") == "offline"])
            }
        }
    
    async def call_mcp_server(self, request: MCPRequest) -> MCPResponse:
        """Make a call to an MCP server"""
        start_time = datetime.now()
        
        if request.server not in self.servers:
            return MCPResponse(
                server=request.server,
                success=False,
                error=f"Unknown server: {request.server}",
                timestamp=datetime.now(),
                execution_time=0.0
            )
        
        server = self.servers[request.server]
        
        try:
            async with httpx.AsyncClient(timeout=request.timeout) as client:
                payload = {
                    "method": request.method,
                    "params": request.params
                }
                
                response = await client.post(
                    f"{server.url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    return MCPResponse(
                        server=request.server,
                        success=True,
                        data=data,
                        timestamp=datetime.now(),
                        execution_time=execution_time
                    )
                else:
                    return MCPResponse(
                        server=request.server,
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                        timestamp=datetime.now(),
                        execution_time=execution_time
                    )
                    
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"MCP call failed to {request.server}: {e}")
            return MCPResponse(
                server=request.server,
                success=False,
                error=str(e),
                timestamp=datetime.now(),
                execution_time=execution_time
            )
    
    async def filesystem_operation(self, operation: str, path: str, content: str = None) -> MCPResponse:
        """Perform filesystem operations via MCP"""
        params = {"path": path}
        if content:
            params["content"] = content
            
        request = MCPRequest(
            server="filesystem",
            method=operation,
            params=params
        )
        
        return await self.call_mcp_server(request)
    
    async def database_query(self, query: str, params: Dict[str, Any] = None) -> MCPResponse:
        """Execute database query via MCP"""
        request = MCPRequest(
            server="postgres",
            method="query",
            params={"query": query, "params": params or {}}
        )
        
        return await self.call_mcp_server(request)
    
    async def github_operation(self, operation: str, repo: str, **kwargs) -> MCPResponse:
        """Perform GitHub operations via MCP"""
        params = {"repo": repo, **kwargs}
        
        request = MCPRequest(
            server="github", 
            method=operation,
            params=params
        )
        
        return await self.call_mcp_server(request)
    
    async def fetch_data(self, url: str, method: str = "GET", **kwargs) -> MCPResponse:
        """Fetch data from external APIs via MCP"""
        params = {"url": url, "method": method, **kwargs}
        
        request = MCPRequest(
            server="fetch",
            method="http_request",
            params=params
        )
        
        return await self.call_mcp_server(request)
    
    async def trigger_automation(self, automation_id: str, context: Dict[str, Any] = None) -> MCPResponse:
        """Trigger automation workflow via MCP"""
        params = {"automation_id": automation_id, "context": context or {}}
        
        request = MCPRequest(
            server="automation",
            method="trigger",
            params=params
        )
        
        return await self.call_mcp_server(request)
    
    async def get_analytics(self, metric: str, timeframe: str = "24h", filters: Dict[str, Any] = None) -> MCPResponse:
        """Get analytics data via MCP"""
        params = {"metric": metric, "timeframe": timeframe, "filters": filters or {}}
        
        request = MCPRequest(
            server="analytics",
            method="get_metrics",
            params=params
        )
        
        return await self.call_mcp_server(request)
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current status of all servers"""
        return {
            "servers": {
                name: {
                    "name": server.name,
                    "port": server.port,
                    "url": server.url,
                    "status": server.status,
                    "capabilities": server.capabilities,
                    "last_check": server.last_check.isoformat() if server.last_check else None
                }
                for name, server in self.servers.items()
            },
            "timestamp": datetime.now().isoformat()
        }

# Global MCP service instance
mcp_service = MCPService()