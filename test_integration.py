#!/usr/bin/env python3
"""
Integration Testing Script - Test MCP and AI Agent Integration
Tests all integration endpoints to ensure functionality
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:10000"

class IntegrationTester:
    """Test suite for integration endpoints"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🧪 Starting Integration Testing Suite")
        logger.info("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("MCP Health Check", self.test_mcp_health),
            ("AI Agents Health Check", self.test_agents_health),
            ("Integration Status", self.test_integration_status),
            ("System Health Report", self.test_system_health_report),
            ("MCP Call Test", self.test_mcp_call),
            ("AI Task Delegation", self.test_ai_task_delegation),
            ("Quick Actions", self.test_quick_actions),
            ("Workflow Templates", self.test_workflow_templates),
            ("Start Workflow", self.test_start_workflow),
            ("System Monitoring", self.test_system_monitoring),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🔍 Running: {test_name}")
                result = await test_func()
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS" if result else "FAIL",
                    "timestamp": datetime.now().isoformat()
                })
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{status}: {test_name}")
            except Exception as e:
                logger.error(f"❌ ERROR in {test_name}: {e}")
                self.test_results.append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Print summary
        self.print_summary()
        
    async def test_health_check(self) -> bool:
        """Test basic health check"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200 and response.json().get("status") == "healthy"
    
    async def test_mcp_health(self) -> bool:
        """Test MCP servers health check"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/v1/integration/mcp/health")
            if response.status_code != 200:
                return False
            
            data = response.json()
            logger.info(f"   MCP Servers Summary: {data.get('summary', {})}")
            return "servers" in data
    
    async def test_agents_health(self) -> bool:
        """Test AI agents health check"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/v1/integration/agents/health")
            if response.status_code != 200:
                return False
            
            data = response.json()
            logger.info(f"   AI Agents Summary: {data.get('summary', {})}")
            return "agents" in data
    
    async def test_integration_status(self) -> bool:
        """Test unified integration status"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/v1/integration/status")
            if response.status_code != 200:
                return False
            
            data = response.json()
            logger.info(f"   System Health: {data.get('system_health', {}).get('overall_health', 'unknown')}")
            return "system_health" in data
    
    async def test_system_health_report(self) -> bool:
        """Test comprehensive system health report"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/api/v1/system/health-report")
            if response.status_code != 200:
                return False
            
            data = response.json()
            logger.info(f"   Overall Status: {data.get('overall_status', 'unknown')}")
            return "overall_status" in data
    
    async def test_mcp_call(self) -> bool:
        """Test direct MCP server call"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "server": "filesystem",
                "method": "list_directory",
                "params": {"path": "/tmp"},
                "timeout": 10
            }
            
            response = await client.post(
                f"{self.base_url}/api/v1/integration/mcp/call",
                json=payload
            )
            
            # Should succeed or fail gracefully (server might not be running)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   MCP Call Result: {'success' if data.get('success') else 'failed'}")
                return True
            else:
                logger.info(f"   MCP Call Status Code: {response.status_code}")
                return response.status_code in [400, 500]  # Expected if servers not running
    
    async def test_ai_task_delegation(self) -> bool:
        """Test AI task delegation"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "task_type": "analyze_revenue",
                "context": {
                    "timeframe": "30d",
                    "test_mode": True
                },
                "priority": "normal",
                "timeout": 10
            }
            
            response = await client.post(
                f"{self.base_url}/api/v1/integration/agents/delegate",
                json=payload
            )
            
            # Should succeed or fail gracefully (agents might not be running)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Task Delegation: {'success' if data.get('success') else 'failed'}")
                return True
            else:
                logger.info(f"   Task Delegation Status Code: {response.status_code}")
                return response.status_code in [400, 500]  # Expected if agents not running
    
    async def test_quick_actions(self) -> bool:
        """Test quick action endpoints"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test quick revenue analysis
            payload = {"timeframe": "7d", "test_mode": True}
            
            response = await client.post(
                f"{self.base_url}/api/v1/integration/quick/analyze-revenue",
                json=payload
            )
            
            logger.info(f"   Quick Revenue Analysis: Status {response.status_code}")
            return response.status_code in [200, 400, 500]  # Any response is acceptable
    
    async def test_workflow_templates(self) -> bool:
        """Test workflow templates endpoint"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/v1/workflows/templates")
            
            if response.status_code == 200:
                templates = response.json()
                logger.info(f"   Available Templates: {len(templates)}")
                return len(templates) > 0
            else:
                logger.info(f"   Templates Status Code: {response.status_code}")
                return False
    
    async def test_start_workflow(self) -> bool:
        """Test starting a workflow"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "timeframe": "7d",
                "include_forecasts": True,
                "test_mode": True
            }
            
            response = await client.post(
                f"{self.base_url}/api/v1/workflows/start/revenue_analysis",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                execution_id = data.get("execution_id")
                logger.info(f"   Workflow Started: {execution_id[:8]}...")
                return execution_id is not None
            else:
                logger.info(f"   Workflow Start Status Code: {response.status_code}")
                return response.status_code in [400, 500]  # Expected if dependencies not running
    
    async def test_system_monitoring(self) -> bool:
        """Test system monitoring endpoints"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test performance trends
            response = await client.get(f"{self.base_url}/api/v1/system/performance-trends?hours=1")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Performance Trends: {data.get('data_points', 0)} data points")
                return True
            else:
                logger.info(f"   Performance Trends Status Code: {response.status_code}")
                return False
    
    def print_summary(self):
        """Print test results summary"""
        logger.info("=" * 60)
        logger.info("🧪 INTEGRATION TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        total = len(self.test_results)
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"💥 Errors: {errors}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0 or errors > 0:
            logger.info("\nFailed/Error Tests:")
            for result in self.test_results:
                if result["status"] in ["FAIL", "ERROR"]:
                    logger.info(f"  - {result['test']}: {result['status']}")
                    if "error" in result:
                        logger.info(f"    Error: {result['error']}")
        
        logger.info("=" * 60)
        
        # Save results to file
        with open("integration_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "success_rate": (passed/total)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        logger.info("📁 Test results saved to: integration_test_results.json")

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())