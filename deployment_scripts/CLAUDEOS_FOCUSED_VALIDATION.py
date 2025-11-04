#!/usr/bin/env python3
"""
CLAUDEOS FOCUSED VALIDATION
===========================
Testing actual working endpoints with proper authentication
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FocusedValidation:
    def __init__(self):
        self.backend_url = "https://brainops-backend-prod.onrender.com"
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        self.token = None
        
    async def run_validation(self):
        """Run focused validation on working endpoints"""
        logger.info("=" * 80)
        logger.info("CLAUDEOS FOCUSED VALIDATION - TESTING WORKING ENDPOINTS")
        logger.info("=" * 80)
        
        # Wait for rate limit to reset
        logger.info("Waiting 30 seconds for rate limit reset...")
        await asyncio.sleep(30)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Test core health endpoints
            await self.test_health_endpoints(client)
            
            # 2. Test authentication with correct endpoint
            await self.test_authentication(client)
            
            # 3. Test protected endpoints with auth
            if self.token:
                await self.test_protected_endpoints(client)
                
                # 4. Test AUREA system
                await self.test_aurea(client)
                
                # 5. Test calculators
                await self.test_calculators(client)
                
                # 6. Test memory system
                await self.test_memory_system(client)
                
                # 7. Test blog API
                await self.test_blog(client)
                
                # 8. Test automations
                await self.test_automations(client)
                
        # Generate report
        self.generate_report()
        
    async def test_health_endpoints(self, client: httpx.AsyncClient):
        """Test core health endpoints"""
        logger.info("\n1. Testing Health Endpoints...")
        
        endpoints = [
            ("/health", "Backend Health"),
            ("/api/v1/health", "API Health"),
            ("/api/v1/version", "Version"),
            ("/api/v1/routes", "Routes List"),
            ("/api/v1/aurea/status", "AUREA Status")
        ]
        
        for endpoint, name in endpoints:
            result = await self.test_endpoint(
                client, name, f"{self.backend_url}{endpoint}"
            )
            self.log_result(name, result)
            
    async def test_authentication(self, client: httpx.AsyncClient):
        """Test authentication with correct endpoints"""
        logger.info("\n2. Testing Authentication...")
        
        # Register new user
        timestamp = int(time.time())
        test_email = f"focused_test_{timestamp}@example.com"
        
        register_result = await self.test_endpoint(
            client,
            "User Registration",
            f"{self.backend_url}/api/v1/auth/register",
            method="POST",
            json_data={
                "email": test_email,
                "password": "TestPassword123!",
                "full_name": "Focused Test User"
            }
        )
        self.log_result("User Registration", register_result)
        
        if register_result["passed"]:
            # Login with correct endpoint
            login_result = await self.test_endpoint(
                client,
                "User Login",
                f"{self.backend_url}/api/v1/auth/login",
                method="POST",
                json_data={
                    "email": test_email,
                    "password": "TestPassword123!"
                }
            )
            self.log_result("User Login", login_result)
            
            if login_result["passed"] and "response" in login_result:
                self.token = login_result["response"].get("access_token")
                logger.info(f"✅ Got auth token: {self.token[:20]}...")
                
    async def test_protected_endpoints(self, client: httpx.AsyncClient):
        """Test protected endpoints with authentication"""
        logger.info("\n3. Testing Protected Endpoints...")
        
        endpoints = [
            ("/api/v1/users/me", "User Profile"),
            ("/api/v1/memory/recent", "Recent Memories"),
            ("/api/v1/projects", "Projects List"),
            ("/api/v1/tasks", "Tasks List")
        ]
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        for endpoint, name in endpoints:
            result = await self.test_endpoint(
                client, name, f"{self.backend_url}{endpoint}",
                headers=headers
            )
            self.log_result(name, result)
            
    async def test_aurea(self, client: httpx.AsyncClient):
        """Test AUREA AI system"""
        logger.info("\n4. Testing AUREA AI...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test AUREA chat
        chat_result = await self.test_endpoint(
            client,
            "AUREA Chat",
            f"{self.backend_url}/api/v1/aurea/chat",
            method="POST",
            json_data={
                "message": "Hello AUREA, are you working properly?",
                "context": {}
            },
            headers=headers
        )
        self.log_result("AUREA Chat", chat_result)
        
        # Test AUREA sessions
        sessions_result = await self.test_endpoint(
            client,
            "AUREA Sessions",
            f"{self.backend_url}/api/v1/aurea/sessions",
            headers=headers
        )
        self.log_result("AUREA Sessions", sessions_result)
        
    async def test_calculators(self, client: httpx.AsyncClient):
        """Test calculator endpoints"""
        logger.info("\n5. Testing Calculators...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Material calculator
        material_result = await self.test_endpoint(
            client,
            "Material Calculator",
            f"{self.backend_url}/api/v1/calculators/materials",
            method="POST",
            json_data={
                "roof_area": 2000,
                "roof_type": "shingle",
                "pitch": 6
            },
            headers=headers
        )
        self.log_result("Material Calculator", material_result)
        
        # Labor calculator
        labor_result = await self.test_endpoint(
            client,
            "Labor Calculator",
            f"{self.backend_url}/api/v1/calculators/labor",
            method="POST",
            json_data={
                "roof_area": 2000,
                "complexity": "medium",
                "crew_size": 4
            },
            headers=headers
        )
        self.log_result("Labor Calculator", labor_result)
        
    async def test_memory_system(self, client: httpx.AsyncClient):
        """Test memory system"""
        logger.info("\n6. Testing Memory System...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create memory
        create_result = await self.test_endpoint(
            client,
            "Create Memory",
            f"{self.backend_url}/api/v1/memory/create",
            method="POST",
            json_data={
                "title": "Focused Validation Test",
                "content": "Testing memory system in focused validation",
                "memory_type": "test"
            },
            headers=headers
        )
        self.log_result("Create Memory", create_result)
        
        # Search memory
        search_result = await self.test_endpoint(
            client,
            "Search Memory",
            f"{self.backend_url}/api/v1/memory/search",
            method="POST",
            json_data={"query": "validation"},
            headers=headers
        )
        self.log_result("Search Memory", search_result)
        
        # Get insights
        insights_result = await self.test_endpoint(
            client,
            "Memory Insights",
            f"{self.backend_url}/api/v1/memory/insights",
            headers=headers
        )
        self.log_result("Memory Insights", insights_result)
        
    async def test_blog(self, client: httpx.AsyncClient):
        """Test blog API"""
        logger.info("\n7. Testing Blog API...")
        
        # Public endpoint - no auth needed
        blog_result = await self.test_endpoint(
            client,
            "Blog Posts",
            f"{self.backend_url}/api/v1/blog/posts"
        )
        self.log_result("Blog Posts", blog_result)
        
    async def test_automations(self, client: httpx.AsyncClient):
        """Test automation system"""
        logger.info("\n8. Testing Automations...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # List automations
        list_result = await self.test_endpoint(
            client,
            "List Automations",
            f"{self.backend_url}/api/v1/automations",
            headers=headers
        )
        self.log_result("List Automations", list_result)
        
        # Automation status
        status_result = await self.test_endpoint(
            client,
            "Automation Status",
            f"{self.backend_url}/api/v1/automations/status",
            headers=headers
        )
        self.log_result("Automation Status", status_result)
        
    async def test_endpoint(self, client: httpx.AsyncClient, name: str, url: str,
                          method: str = "GET", headers: Dict = None,
                          json_data: Dict = None) -> Dict:
        """Test a single endpoint"""
        try:
            # Add delay to avoid rate limiting
            await asyncio.sleep(0.5)
            
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data)
                
            result = {
                "name": name,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "passed": response.status_code in [200, 201],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if response.status_code == 200:
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text[:200]
                    
            return result
            
        except Exception as e:
            return {
                "name": name,
                "url": url,
                "method": method,
                "error": str(e),
                "passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    def log_result(self, name: str, result: Dict):
        """Log test result"""
        self.results["tests"][name] = result
        self.results["summary"]["total"] += 1
        
        if result["passed"]:
            self.results["summary"]["passed"] += 1
            logger.info(f"✅ {name}: PASSED")
        else:
            self.results["summary"]["failed"] += 1
            error = result.get("error") or f"Status {result.get('status_code', 'unknown')}"
            logger.error(f"❌ {name}: FAILED - {error}")
            
    def generate_report(self):
        """Generate validation report"""
        success_rate = (self.results["summary"]["passed"] / self.results["summary"]["total"] * 100) if self.results["summary"]["total"] > 0 else 0
        
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.results['summary']['total']}")
        logger.info(f"Passed: {self.results['summary']['passed']}")
        logger.info(f"Failed: {self.results['summary']['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Save detailed report
        with open("CLAUDEOS_FOCUSED_VALIDATION_REPORT.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Create actionable report
        self.create_action_report(success_rate)
        
    def create_action_report(self, success_rate: float):
        """Create actionable report for fixes"""
        report = f"""
# CLAUDEOS VALIDATION ACTION REPORT
Generated: {datetime.utcnow().isoformat()}
Success Rate: {success_rate:.1f}%

## CRITICAL ISSUES FOUND

### 1. Authentication System
"""
        
        # Analyze authentication issues
        if "User Login" in self.results["tests"] and not self.results["tests"]["User Login"]["passed"]:
            report += "- ❌ Login endpoint broken - needs immediate fix\n"
        elif self.token:
            report += "- ✅ Authentication working\n"
            
        # Analyze protected endpoints
        report += "\n### 2. Protected Endpoints\n"
        for test_name, result in self.results["tests"].items():
            if "Protected" in test_name or test_name in ["User Profile", "Recent Memories", "Projects List", "Tasks List"]:
                if not result["passed"]:
                    report += f"- ❌ {test_name}: {result.get('status_code', 'Error')}\n"
                else:
                    report += f"- ✅ {test_name}: Working\n"
                    
        # Analyze AUREA
        report += "\n### 3. AUREA AI System\n"
        aurea_tests = [name for name in self.results["tests"] if "AUREA" in name]
        for test_name in aurea_tests:
            result = self.results["tests"][test_name]
            if not result["passed"]:
                report += f"- ❌ {test_name}: {result.get('status_code', 'Error')}\n"
            else:
                report += f"- ✅ {test_name}: Working\n"
                
        # Memory system
        report += "\n### 4. Memory System\n"
        memory_tests = [name for name in self.results["tests"] if "Memory" in name]
        for test_name in memory_tests:
            result = self.results["tests"][test_name]
            if not result["passed"]:
                report += f"- ❌ {test_name}: {result.get('status_code', 'Error')}\n"
            else:
                report += f"- ✅ {test_name}: Working\n"
                
        # Recommendations
        report += f"""

## RECOMMENDATIONS

1. **Rate Limiting**: Implement proper rate limit handling or increase limits
2. **Authentication**: Ensure all endpoints use consistent auth
3. **Error Handling**: Return proper error messages instead of generic 403/404
4. **Documentation**: Update API docs to reflect actual endpoints

## NEXT STEPS

"""
        
        if success_rate >= 95:
            report += "✅ System is ready for launch with minor fixes\n"
        elif success_rate >= 80:
            report += "⚠️ System needs some fixes before launch\n"
        else:
            report += "❌ System requires significant fixes before launch\n"
            
        with open("CLAUDEOS_ACTION_REPORT.md", "w") as f:
            f.write(report)
            
        logger.info(f"\nAction report saved to: CLAUDEOS_ACTION_REPORT.md")


async def main():
    validator = FocusedValidation()
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main())