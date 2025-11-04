#!/usr/bin/env python3
"""
BrainOps E2E Test Suite
Comprehensive end-to-end testing of all system components
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://brainops-backend-prod.onrender.com"
ADMIN_CREDS = {"email": "admin@brainops.com", "password": "AdminPassword123!"}
TEST_CREDS = {"email": "test@brainops.com", "password": "TestPassword123!"}

class E2ETestSuite:
    """End-to-end test suite"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0
            }
        }
        self.auth_token = None
        self.headers = {}
    
    def run_all_tests(self):
        """Run complete E2E test suite"""
        print("=" * 80)
        print("🧪 BrainOps E2E Test Suite")
        print(f"📅 {datetime.utcnow().isoformat()}")
        print(f"🌐 Target: {BASE_URL}")
        print("=" * 80)
        
        # Test categories
        test_categories = [
            ("System Health", self.test_system_health),
            ("Authentication", self.test_authentication),
            ("Memory System", self.test_memory_system),
            ("AI Services", self.test_ai_services),
            ("Integrations", self.test_integrations),
            ("Automations", self.test_automations),
            ("AUREA Voice", self.test_aurea_voice),
            ("Roofing Features", self.test_roofing_features),
            ("Admin Functions", self.test_admin_functions),
            ("Full Workflow", self.test_full_workflow)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n📋 Testing {category_name}...")
            try:
                test_func()
            except Exception as e:
                print(f"❌ {category_name} tests failed: {e}")
                self.record_test(f"{category_name} Suite", False, str(e))
        
        # Calculate summary
        self.calculate_summary()
        
        # Print results
        self.print_results()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def test_system_health(self):
        """Test system health endpoints"""
        # Basic health
        self.run_test(
            "Basic Health Check",
            "GET", "/health",
            expected_status=200,
            validate_response=lambda r: r.get("status") == "healthy"
        )
        
        # API health
        self.run_test(
            "API Health Check",
            "GET", "/api/v1/health",
            expected_status=200,
            validate_response=lambda r: r.get("status") == "healthy"
        )
        
        # Version check
        self.run_test(
            "Version Check",
            "GET", "/api/v1/version",
            expected_status=200,
            validate_response=lambda r: "version" in r
        )
        
        # Routes check
        self.run_test(
            "Routes Loaded",
            "GET", "/api/v1/routes",
            expected_status=200,
            validate_response=lambda r: r.get("total_routes", 0) > 100
        )
    
    def test_authentication(self):
        """Test authentication system"""
        # Login
        response = self.run_test(
            "Admin Login",
            "POST", "/api/v1/auth/login",
            data=ADMIN_CREDS,
            expected_status=200,
            validate_response=lambda r: "access_token" in r
        )
        
        if response and response.get("success"):
            self.auth_token = response["data"].get("access_token")
            self.headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Get current user
        self.run_test(
            "Get Current User",
            "GET", "/api/v1/users/me",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: r.get("email") == "admin@brainops.com"
        )
        
        # Token refresh
        self.run_test(
            "Token Refresh",
            "POST", "/api/v1/auth/refresh",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "access_token" in r
        )
    
    def test_memory_system(self):
        """Test memory persistence system"""
        # Create memory
        memory_data = {
            "memory_type": "test_event",
            "content": "E2E test memory entry",
            "metadata": {
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        create_response = self.run_test(
            "Create Memory",
            "POST", "/api/v1/memory/create",
            data=memory_data,
            headers=self.headers,
            expected_status=201,
            validate_response=lambda r: "id" in r
        )
        
        # Get recent memories
        self.run_test(
            "Get Recent Memories",
            "GET", "/api/v1/memory/recent",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: isinstance(r.get("memories"), list)
        )
        
        # Search memories
        self.run_test(
            "Search Memories",
            "POST", "/api/v1/memory/search",
            data={"query": "test"},
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "results" in r
        )
        
        # Memory insights
        self.run_test(
            "Memory Insights",
            "GET", "/api/v1/memory/insights",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "insights" in r
        )
    
    def test_ai_services(self):
        """Test AI service endpoints"""
        # Claude agent
        self.run_test(
            "Claude Agent",
            "POST", "/api/v1/ai-services/claude/agent",
            data={
                "task": "What is 2+2?",
                "context": {"test": True}
            },
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "response" in r
        )
        
        # AI insights
        self.run_test(
            "AI Insights",
            "GET", "/api/v1/ai-insights/performance",
            headers=self.headers,
            expected_status=200
        )
        
        # AUREA status
        self.run_test(
            "AUREA Status",
            "GET", "/api/v1/aurea/status",
            expected_status=200,
            validate_response=lambda r: r.get("status") == "operational"
        )
    
    def test_integrations(self):
        """Test integration endpoints"""
        integrations = [
            "github", "slack", "stripe", "clickup", "elevenlabs"
        ]
        
        for integration in integrations:
            self.run_test(
                f"{integration.title()} Status",
                "GET", f"/api/v1/integrations/{integration}/status",
                headers=self.headers,
                expected_status=200,
                validate_response=lambda r: "connected" in r
            )
    
    def test_automations(self):
        """Test automation endpoints"""
        # Automation types
        self.run_test(
            "Automation Types",
            "GET", "/api/v1/automations/types",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "automation_types" in r
        )
        
        # Automation history
        self.run_test(
            "Automation History",
            "GET", "/api/v1/automations/history",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "history" in r
        )
        
        # Specific automation
        self.run_test(
            "SEO Analysis Automation",
            "GET", "/api/v1/automations/types/daily_seo_analysis",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: r.get("type") == "daily_seo_analysis"
        )
    
    def test_aurea_voice(self):
        """Test AUREA voice capabilities"""
        # Voice status
        self.run_test(
            "Voice Status",
            "GET", "/api/v1/aurea/voice/status",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "voice_enabled" in r
        )
        
        # Available voices
        self.run_test(
            "Available Voices",
            "GET", "/api/v1/aurea/voice/voices",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: isinstance(r.get("voices"), list)
        )
        
        # Voice synthesis
        self.run_test(
            "Voice Synthesis",
            "POST", "/api/v1/aurea/voice/synthesize",
            data={
                "text": "Hello from E2E test suite",
                "voice": "elevenlabs-conversational"
            },
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "audio_base64" in r or "error" in r
        )
    
    def test_roofing_features(self):
        """Test roofing-specific features"""
        # Roof analysis
        self.run_test(
            "Roof Analysis Status",
            "GET", "/api/v1/roofing/analysis/status",
            headers=self.headers,
            expected_status=200
        )
        
        # Materials database
        self.run_test(
            "Materials List",
            "GET", "/api/v1/roofing/materials",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: isinstance(r.get("materials"), list)
        )
        
        # Projects
        self.run_test(
            "Roofing Projects",
            "GET", "/api/v1/projects",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "projects" in r
        )
    
    def test_admin_functions(self):
        """Test admin functionality"""
        # Admin status
        self.run_test(
            "Admin Status",
            "GET", "/api/v1/admin/status",
            headers=self.headers,
            expected_status=200
        )
        
        # System resources
        self.run_test(
            "System Resources",
            "GET", "/api/v1/admin/system/resources",
            headers=self.headers,
            expected_status=200,
            validate_response=lambda r: "cpu" in r or "memory" in r
        )
        
        # Database status
        self.run_test(
            "Database Status",
            "GET", "/api/v1/admin/database/status",
            headers=self.headers,
            expected_status=200
        )
    
    def test_full_workflow(self):
        """Test complete user workflow"""
        print("\n🔄 Testing full workflow...")
        
        # 1. Create a project
        project_data = {
            "name": "E2E Test Project",
            "description": "Automated test project",
            "type": "roofing",
            "status": "planning"
        }
        
        project_response = self.run_test(
            "Create Project",
            "POST", "/api/v1/projects",
            data=project_data,
            headers=self.headers,
            expected_status=201,
            validate_response=lambda r: "id" in r
        )
        
        if project_response and project_response.get("success"):
            project_id = project_response["data"].get("id")
            
            # 2. Add AI analysis
            self.run_test(
                "AI Project Analysis",
                "POST", f"/api/v1/projects/{project_id}/analyze",
                data={"analysis_type": "feasibility"},
                headers=self.headers,
                expected_status=200
            )
            
            # 3. Create memory for project
            self.run_test(
                "Project Memory",
                "POST", "/api/v1/memory/create",
                data={
                    "memory_type": "project_event",
                    "content": "E2E test project created",
                    "owner_id": project_id,
                    "owner_type": "project"
                },
                headers=self.headers,
                expected_status=201
            )
    
    def run_test(self, name: str, method: str, endpoint: str, 
                 data: Dict = None, headers: Dict = None, 
                 expected_status: int = 200,
                 validate_response = None) -> Dict[str, Any]:
        """Run a single test"""
        url = f"{BASE_URL}{endpoint}"
        test_headers = headers or {}
        
        try:
            # Make request
            if method == "GET":
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=test_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check status
            status_ok = response.status_code == expected_status
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}
            
            # Validate response
            validation_ok = True
            if validate_response and status_ok:
                try:
                    validation_ok = validate_response(response_data)
                except Exception as e:
                    validation_ok = False
                    response_data["validation_error"] = str(e)
            
            success = status_ok and validation_ok
            
            # Record result
            self.record_test(
                name,
                success,
                f"Status: {response.status_code}" if not success else None,
                {
                    "method": method,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "response": response_data
                }
            )
            
            # Print result
            if success:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} - Status: {response.status_code}")
                if not status_ok:
                    print(f"     Expected: {expected_status}, Got: {response.status_code}")
                if not validation_ok:
                    print(f"     Validation failed")
            
            return {"success": success, "data": response_data}
            
        except Exception as e:
            self.record_test(name, False, str(e))
            print(f"  ❌ {name} - Error: {e}")
            return {"success": False, "error": str(e)}
    
    def record_test(self, name: str, success: bool, error: str = None, details: Dict = None):
        """Record test result"""
        self.results["tests"].append({
            "name": name,
            "success": success,
            "error": error,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def calculate_summary(self):
        """Calculate test summary"""
        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["success"])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(success_rate, 2)
        }
    
    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS")
        print("=" * 80)
        
        summary = self.results["summary"]
        print(f"Total Tests: {summary['total']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']}%")
        
        if summary['failed'] > 0:
            print("\n❌ Failed Tests:")
            for test in self.results["tests"]:
                if not test["success"]:
                    print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        
        # Overall status
        if summary['success_rate'] >= 90:
            print("🎉 EXCELLENT - System is fully operational!")
        elif summary['success_rate'] >= 70:
            print("✅ GOOD - System is mostly operational")
        elif summary['success_rate'] >= 50:
            print("⚠️  WARNING - System has significant issues")
        else:
            print("❌ CRITICAL - System is largely non-functional")
        
        print("=" * 80)
    
    def save_results(self):
        """Save test results to file"""
        filename = f"e2e_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Run E2E test suite"""
    suite = E2ETestSuite()
    results = suite.run_all_tests()
    
    # Exit with appropriate code
    if results["summary"]["success_rate"] >= 90:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()