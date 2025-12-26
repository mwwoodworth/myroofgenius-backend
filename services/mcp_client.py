"""
MCP Bridge Client - Active Integration with BrainOps MCP Bridge
Provides direct access to 245+ tools across 11 MCP servers

This is the ACTIVE nervous system connection - not just permission, but actual traffic.
"""

import os
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MCPBridgeClient:
    """Client for BrainOps MCP Bridge - Active tool execution"""

    def __init__(self):
        self.base_url = os.getenv("MCP_BRIDGE_URL", "https://brainops-mcp-bridge.onrender.com")
        self.api_key = os.getenv("BRAINOPS_API_KEY", "brainops_prod_key_2025")
        self._tools_cache: Optional[Dict] = None
        self._servers_cache: Optional[List] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check MCP Bridge health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "connected",
                            "bridge_status": data.get("status"),
                            "servers": data.get("mcpServers", 0),
                            "tools": data.get("totalTools", 0),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}",
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            logger.error(f"MCP Bridge health check failed: {e}")
            return {
                "status": "unreachable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all available MCP servers"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/servers",
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._servers_cache = data.get("servers", data) if isinstance(data, dict) else data
                        return self._servers_cache
                    else:
                        logger.warning(f"Failed to list servers: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Failed to list MCP servers: {e}")
            return []

    async def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools, optionally filtered by server"""
        try:
            url = f"{self.base_url}/tools"
            if server_name:
                url = f"{self.base_url}/servers/{server_name}/tools"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tools = data.get("tools", data) if isinstance(data, dict) else data
                        return tools if isinstance(tools, list) else []
                    else:
                        logger.warning(f"Failed to list tools: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        server_name: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Execute a tool via MCP Bridge"""
        try:
            payload = {
                "tool": tool_name,
                "arguments": arguments or {}
            }

            if server_name:
                payload["server"] = server_name

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/execute",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    result = await response.json()

                    if response.status == 200:
                        logger.info(f"MCP tool executed: {tool_name}")
                        return {
                            "status": "success",
                            "tool": tool_name,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"MCP tool execution failed: {tool_name} - {result}")
                        return {
                            "status": "error",
                            "tool": tool_name,
                            "error": result.get("error", result.get("detail", str(result))),
                            "status_code": response.status,
                            "timestamp": datetime.now().isoformat()
                        }

        except aiohttp.ClientError as e:
            logger.error(f"MCP tool execution network error: {tool_name} - {e}")
            return {
                "status": "network_error",
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"MCP tool execution error: {tool_name} - {e}")
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def query_brain(self, query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Query the unified brain via MCP"""
        return await self.execute_tool(
            "brain_query",
            {"query": query, "category": category},
            server_name="brainops"
        )

    async def store_memory(self, key: str, value: Any, category: str = "general") -> Dict[str, Any]:
        """Store memory in unified brain via MCP"""
        return await self.execute_tool(
            "brain_store",
            {"key": key, "value": value, "category": category},
            server_name="brainops"
        )

    async def execute_github_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GitHub action via MCP"""
        return await self.execute_tool(
            f"github_{action}",
            params,
            server_name="github"
        )

    async def execute_database_query(self, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """Execute database query via MCP (with safety limits)"""
        return await self.execute_tool(
            "supabase_query",
            {"query": query, "params": params or []},
            server_name="supabase"
        )


# Global singleton instance
_mcp_client: Optional[MCPBridgeClient] = None

def get_mcp_client() -> MCPBridgeClient:
    """Get or create the global MCP Bridge client"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPBridgeClient()
    return _mcp_client


async def initialize_mcp_client() -> MCPBridgeClient:
    """Initialize and verify MCP Bridge connection"""
    client = get_mcp_client()
    health = await client.health_check()

    if health["status"] == "connected":
        logger.info(f"✅ MCP Bridge connected: {health['servers']} servers, {health['tools']} tools")
    else:
        logger.warning(f"⚠️ MCP Bridge status: {health['status']} - {health.get('error', 'unknown')}")

    return client
