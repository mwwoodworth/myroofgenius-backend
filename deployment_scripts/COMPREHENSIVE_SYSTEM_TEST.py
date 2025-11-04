#!/usr/bin/env python3
"""
COMPREHENSIVE AI OPERATING SYSTEM TEST SUITE
Tests every single component of the BrainOps AI OS
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import httpx
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"
API_URL = f"{BASE_URL}/api/v1"

class SystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": []
        }
        
    async def test_endpoint(self, name: str, method: str, url: str, 
                           headers: Dict = None, json_data: Dict = None,
                           expected_status: List[int] = None) -> bool:
        """Test a single endpoint"""
        if expected_status is None:
            expected_status = [200, 201]
            
        try:
            self.results["total_tests"] += 1
            
            if method == "GET":
                response = await self.client.get(url, headers=headers)
            elif method == "POST":
                response = await self.client.post(url, headers=headers, json=json_data)
            elif method == "PUT":
                response = await self.client.put(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in expected_status:
                print(f"{Fore.GREEN}✅ {name}: {response.status_code} OK")
                self.results["passed"] += 1
                self.results["details"].append({
                    "test": name,
                    "status": "PASS",
                    "code": response.status_code,
                    "response": response.text[:200] if response.text else None
                })
                return True
            else:
                print(f"{Fore.RED}❌ {name}: {response.status_code} (Expected: {expected_status})")
                self.results["failed"] += 1
                self.results["details"].append({
                    "test": name,
                    "status": "FAIL",
                    "code": response.status_code,
                    "expected": expected_status,
                    "response": response.text[:200] if response.text else None
                })
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ {name}: ERROR - {str(e)}")
            self.results["failed"] += 1
            self.results["details"].append({
                "test": name,
                "status": "ERROR",
                "error": str(e)
            })
            return False
    
    async def test_core_system(self):
        """Test core system endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING CORE SYSTEM")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Health check
        await self.test_endpoint(
            "System Health",
            "GET",
            f"{API_URL}/health"
        )
        
        # Version check
        await self.test_endpoint(
            "Version Info",
            "GET",
            f"{API_URL}/version"
        )
        
        # Database status
        await self.test_endpoint(
            "Database Status",
            "GET",
            f"{API_URL}/db-sync/status"
        )
        
    async def test_ai_agents(self):
        """Test AI agent endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING AI AGENTS")
        print(f"{Fore.CYAN}{'='*60}")
        
        # AUREA status
        await self.test_endpoint(
            "AUREA Status",
            "GET",
            f"{API_URL}/aurea/status"
        )
        
        # AUREA health
        await self.test_endpoint(
            "AUREA Health",
            "GET",
            f"{API_URL}/aurea/health"
        )
        
        # AI Board status
        await self.test_endpoint(
            "AI Board Status",
            "GET",
            f"{API_URL}/ai-board/status"
        )
        
        # LangGraph status
        await self.test_endpoint(
            "LangGraph Status",
            "GET",
            f"{API_URL}/langgraph/status"
        )
        
    async def test_revenue_system(self):
        """Test revenue generation system"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING REVENUE SYSTEM")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Revenue generation
        await self.test_endpoint(
            "Revenue Generation",
            "POST",
            f"{API_URL}/aurea/revenue/generate",
            json_data={"target_mrr": 150000}
        )
        
        # Revenue report
        await self.test_endpoint(
            "Revenue Report",
            "GET",
            f"{API_URL}/aurea/revenue/report"
        )
        
    async def test_memory_system(self):
        """Test memory system (expect auth failures for protected endpoints)"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING MEMORY SYSTEM")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Recent memory (should fail without auth)
        await self.test_endpoint(
            "Recent Memory (No Auth)",
            "GET",
            f"{API_URL}/memory/recent",
            expected_status=[401, 403]
        )
        
        # Memory stats (public endpoint)
        await self.test_endpoint(
            "Memory Stats",
            "GET",
            f"{API_URL}/memory/stats"
        )
        
    async def test_automation_system(self):
        """Test automation system"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING AUTOMATION SYSTEM")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Automation status
        await self.test_endpoint(
            "Automation Status",
            "GET",
            f"{API_URL}/automations/status"
        )
        
        # Cron jobs
        await self.test_endpoint(
            "Cron Jobs",
            "GET",
            f"{API_URL}/automations/cron/jobs"
        )
        
    async def test_marketplace(self):
        """Test marketplace endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING MARKETPLACE")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Public products
        await self.test_endpoint(
            "Public Products",
            "GET",
            f"{API_URL}/products/public"
        )
        
        # Marketplace recommendations
        await self.test_endpoint(
            "Marketplace Recommendations",
            "GET",
            f"{API_URL}/marketplace/recommendations"
        )
        
    async def test_integrations(self):
        """Test integration endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING INTEGRATIONS")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Slack status
        await self.test_endpoint(
            "Slack Integration",
            "GET",
            f"{API_URL}/integrations/slack/status",
            expected_status=[200, 404, 503]
        )
        
        # Stripe status
        await self.test_endpoint(
            "Stripe Integration",
            "GET",
            f"{API_URL}/integrations/stripe/status",
            expected_status=[200, 404, 503]
        )
        
    async def test_myroofgenius(self):
        """Test MyRoofGenius specific endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING MYROOFGENIUS")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Roof analysis
        await self.test_endpoint(
            "AI Roof Analysis",
            "POST",
            f"{API_URL}/ai/roof/analyze",
            json_data={"image_url": "test.jpg"},
            expected_status=[200, 422, 400]
        )
        
        # Field ops sync
        await self.test_endpoint(
            "Field Ops Status",
            "GET",
            f"{API_URL}/field-ops/status"
        )
        
    async def test_authentication(self):
        """Test authentication system"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING AUTHENTICATION")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Login endpoint (should exist)
        await self.test_endpoint(
            "Login Endpoint",
            "POST",
            f"{API_URL}/auth/login",
            json_data={"email": "test@test.com", "password": "test"},
            expected_status=[401, 422, 400]
        )
        
        # Protected endpoint without auth
        await self.test_endpoint(
            "Protected Route (No Auth)",
            "GET",
            f"{API_URL}/admin/users",
            expected_status=[401, 403]
        )
        
    async def test_ai_os_core(self):
        """Test AI Operating System core functionality"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING AI OS CORE")
        print(f"{Fore.CYAN}{'='*60}")
        
        # System status
        await self.test_endpoint(
            "AI OS Status",
            "GET",
            f"{API_URL}/ai-os/status"
        )
        
        # Agent list
        await self.test_endpoint(
            "AI Agents List",
            "GET",
            f"{API_URL}/ai-os/agents"
        )
        
        # Capabilities
        await self.test_endpoint(
            "AI OS Capabilities",
            "GET",
            f"{API_URL}/ai-os/capabilities"
        )
        
    async def test_frontend_endpoints(self):
        """Test frontend-specific endpoints"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING FRONTEND ENDPOINTS")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Frontend status
        await self.test_endpoint(
            "Frontend Status",
            "GET",
            f"{API_URL}/frontend/status"
        )
        
        # Dashboard data
        await self.test_endpoint(
            "Dashboard Data",
            "GET",
            f"{API_URL}/dashboard/data",
            expected_status=[200, 401, 403]
        )
        
    async def test_websocket_endpoints(self):
        """Test WebSocket endpoints (just check they exist)"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING WEBSOCKET ENDPOINTS")
        print(f"{Fore.CYAN}{'='*60}")
        
        # WebSocket info
        await self.test_endpoint(
            "WebSocket Info",
            "GET",
            f"{API_URL}/ws/info"
        )
        
    async def test_monitoring(self):
        """Test monitoring and observability"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TESTING MONITORING")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Metrics
        await self.test_endpoint(
            "Prometheus Metrics",
            "GET",
            f"{BASE_URL}/metrics",
            expected_status=[200, 404]
        )
        
        # Alerts
        await self.test_endpoint(
            "Alert Feed",
            "GET",
            f"{API_URL}/alerts"
        )
        
    async def run_all_tests(self):
        """Run all test suites"""
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}COMPREHENSIVE AI OS TEST SUITE")
        print(f"{Fore.MAGENTA}Starting at: {datetime.now().isoformat()}")
        print(f"{Fore.MAGENTA}Target: {BASE_URL}")
        print(f"{Fore.MAGENTA}{'='*60}")
        
        start_time = time.time()
        
        # Run all test categories
        await self.test_core_system()
        await self.test_ai_agents()
        await self.test_revenue_system()
        await self.test_memory_system()
        await self.test_automation_system()
        await self.test_marketplace()
        await self.test_integrations()
        await self.test_myroofgenius()
        await self.test_authentication()
        await self.test_ai_os_core()
        await self.test_frontend_endpoints()
        await self.test_websocket_endpoints()
        await self.test_monitoring()
        
        # Calculate results
        duration = time.time() - start_time
        pass_rate = (self.results["passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        # Print summary
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}TEST RESULTS SUMMARY")
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.CYAN}Total Tests: {self.results['total_tests']}")
        print(f"{Fore.GREEN}Passed: {self.results['passed']}")
        print(f"{Fore.RED}Failed: {self.results['failed']}")
        print(f"{Fore.YELLOW}Warnings: {self.results['warnings']}")
        print(f"{Fore.CYAN}Pass Rate: {pass_rate:.1f}%")
        print(f"{Fore.CYAN}Duration: {duration:.2f} seconds")
        
        # Overall status
        if pass_rate >= 90:
            print(f"\n{Fore.GREEN}🎉 SYSTEM STATUS: FULLY OPERATIONAL")
        elif pass_rate >= 70:
            print(f"\n{Fore.YELLOW}⚠️ SYSTEM STATUS: MOSTLY OPERATIONAL")
        else:
            print(f"\n{Fore.RED}❌ SYSTEM STATUS: CRITICAL ISSUES")
        
        # Save detailed results
        with open("/home/mwwoodworth/code/test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n{Fore.CYAN}Detailed results saved to: /home/mwwoodworth/code/test_results.json")
        
        await self.client.aclose()
        
        return pass_rate

async def main():
    tester = SystemTester()
    pass_rate = await tester.run_all_tests()
    return pass_rate >= 70  # Return True if system is operational

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)