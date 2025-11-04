#!/usr/bin/env python3
"""
AI Agent Coordinator - Manages all agents
"""

import asyncio
import httpx
from typing import Dict, List

AGENTS = {
    "orchestrator": "http://localhost:6001",
    "analyst": "http://localhost:6002",
    "automation": "http://localhost:6003",
    "customer_service": "http://localhost:6004",
    "monitoring": "http://localhost:6005",
    "revenue": "http://localhost:6006"
}

async def check_all_agents():
    """Check health of all agents"""
    async with httpx.AsyncClient() as client:
        results = {}
        for name, url in AGENTS.items():
            try:
                response = await client.get(f"{url}/health")
                results[name] = response.json()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

async def delegate_task(agent_name: str, task: Dict):
    """Delegate a task to a specific agent"""
    if agent_name not in AGENTS:
        return {"error": f"Unknown agent: {agent_name}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AGENTS[agent_name]}/process",
                json=task
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

async def main():
    print("AI Agent Coordinator")
    print("=" * 50)
    
    # Check all agents
    print("Checking agent health...")
    health = await check_all_agents()
    for agent, status in health.items():
        if isinstance(status, dict) and status.get("status") == "healthy":
            print(f"✅ {agent}: HEALTHY")
        else:
            print(f"❌ {agent}: DOWN")
    
    print("\nCoordinator ready for tasks!")

if __name__ == "__main__":
    asyncio.run(main())
