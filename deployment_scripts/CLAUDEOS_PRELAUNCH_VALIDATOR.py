#!/usr/bin/env python3
"""
CLAUDEOS PRE-LAUNCH VALIDATION SYSTEM
Complete validation of all BrainOps systems before launch
v3.1.224
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
import sys

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URL = "https://myroofgenius.com"
API_VERSION = "v1"

# Test credentials
TEST_USERS = {
    "admin": {"email": "admin@brainops.com", "password": "AdminPassword123!"},
    "user": {"email": "test@brainops.com", "password": "TestPassword123!"},
    "demo": {"email": "demo@myroofgenius.com", "password": "DemoPassword123!"}
}

class ValidationResult:
    def __init__(self, category: str, test: str):
        self.category = category
        self.test = test
        self.status = "PENDING"
        self.message = ""
        self.details = {}
        self.timestamp = datetime.now(timezone.utc)
    
    def pass_test(self, message: str = "", details: Dict = None):
        self.status = "PASS"
        self.message = message
        self.details = details or {}
        
    def fail_test(self, message: str, details: Dict = None):
        self.status = "FAIL"
        self.message = message
        self.details = details or {}

class PreLaunchValidator:
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.session = None
        self.tokens = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def add_result(self, result: ValidationResult):
        self.results.append(result)
        
    async def test_endpoint(self, method: str, url: str, **kwargs) -> Tuple[int, Dict]:
        """Test an API endpoint"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                data = {}
                try:
                    if response.content_type and 'application/json' in response.content_type:
                        data = await response.json()
                    else:
                        text = await response.text()
                        data = {"text": text}
                except:
                    data = {}
                return response.status, data
        except Exception as e:
            return 0, {"error": str(e)}
            
    async def authenticate(self, user_type: str) -> bool:
        """Authenticate and get token"""
        result = ValidationResult("Authentication", f"Login as {user_type}")
        
        creds = TEST_USERS[user_type]
        status, data = await self.test_endpoint(
            "POST",
            f"{BACKEND_URL}/api/{API_VERSION}/auth/login",
            json={"email": creds["email"], "password": creds["password"]}
        )
        
        if status == 200 and data and "access_token" in data:
            self.tokens[user_type] = data["access_token"]
            result.pass_test(f"Successfully authenticated as {user_type}", data)
        else:
            result.fail_test(f"Failed to authenticate: {data}")
            
        self.add_result(result)
        return result.status == "PASS"
        
    async def validate_backend_health(self):
        """Validate backend health and core systems"""
        print("\n🔍 VALIDATING BACKEND HEALTH...")
        
        # Test main health endpoint
        result = ValidationResult("Backend", "Health Check")
        status, data = await self.test_endpoint("GET", f"{BACKEND_URL}/api/{API_VERSION}/health")
        
        if status == 200:
            result.pass_test("Backend is healthy", data)
        else:
            result.fail_test(f"Backend unhealthy: {data}")
        self.add_result(result)
        
        # Test database connectivity
        result = ValidationResult("Backend", "Database Connection")
        if self.tokens.get("admin"):
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            status, data = await self.test_endpoint(
                "GET", 
                f"{BACKEND_URL}/api/{API_VERSION}/system/database/status",
                headers=headers
            )
            
            if status == 200:
                result.pass_test("Database connected", data)
            else:
                result.fail_test(f"Database issue: {data}")
        else:
            result.fail_test("No admin token available")
        self.add_result(result)
        
    async def validate_memory_system(self):
        """Validate persistent memory system"""
        print("\n🧠 VALIDATING MEMORY SYSTEM...")
        
        if not self.tokens.get("user"):
            return
            
        headers = {"Authorization": f"Bearer {self.tokens['user']}"}
        
        # Test memory creation
        result = ValidationResult("Memory", "Create Memory")
        status, data = await self.test_endpoint(
            "POST",
            f"{BACKEND_URL}/api/{API_VERSION}/memory/create",
            headers=headers,
            json={
                "title": "Pre-launch validation test",
                "content": {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()},
                "memory_type": "validation"
            }
        )
        
        if status in [200, 201]:
            result.pass_test("Memory created successfully", data)
        else:
            result.fail_test(f"Failed to create memory: {data}")
        self.add_result(result)
        
        # Test memory retrieval
        result = ValidationResult("Memory", "Retrieve Memories")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/memory/recent?limit=5",
            headers=headers
        )
        
        if status == 200:
            result.pass_test(f"Retrieved {len(data.get('memories', []))} memories", data)
        else:
            result.fail_test(f"Failed to retrieve memories: {data}")
        self.add_result(result)
        
    async def validate_aurea(self):
        """Validate AUREA AI system"""
        print("\n🤖 VALIDATING AUREA AI SYSTEM...")
        
        # Test AUREA status
        result = ValidationResult("AUREA", "System Status")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/aurea/status"
        )
        
        if status == 200 and data.get("status") == "operational":
            result.pass_test("AUREA is operational", data)
        else:
            result.fail_test(f"AUREA not operational: {data}")
        self.add_result(result)
        
        # Test AUREA chat
        if self.tokens.get("user"):
            result = ValidationResult("AUREA", "Chat Response")
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            status, data = await self.test_endpoint(
                "POST",
                f"{BACKEND_URL}/api/{API_VERSION}/aurea/chat",
                headers=headers,
                json={"message": "Hello AUREA, are you ready for launch?"}
            )
            
            if status == 200 and "response" in data:
                result.pass_test("AUREA responded successfully", data)
            else:
                result.fail_test(f"AUREA chat failed: {data}")
            self.add_result(result)
            
    async def validate_langgraphos(self):
        """Validate LangGraphOS system"""
        print("\n🔧 VALIDATING LANGGRAPHOS...")
        
        # Test public status endpoint
        result = ValidationResult("LangGraphOS", "Public Status")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/langgraphos/status"
        )
        
        if status == 200:
            result.pass_test("LangGraphOS status accessible", data)
        else:
            result.fail_test(f"LangGraphOS status failed: {data}")
        self.add_result(result)
        
        # Test workflows with auth
        if self.tokens.get("user"):
            result = ValidationResult("LangGraphOS", "Workflow List")
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            status, data = await self.test_endpoint(
                "GET",
                f"{BACKEND_URL}/api/{API_VERSION}/langgraphos/workflows",
                headers=headers
            )
            
            if status == 200:
                result.pass_test(f"Found {len(data.get('workflows', {}))} workflows", data)
            else:
                result.fail_test(f"Failed to get workflows: {data}")
            self.add_result(result)
            
    async def validate_marketplace(self):
        """Validate marketplace functionality"""
        print("\n🛒 VALIDATING MARKETPLACE...")
        
        # Test public products endpoint
        result = ValidationResult("Marketplace", "Public Products")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/marketplace/products?limit=5"
        )
        
        if status == 200 and isinstance(data, list):
            result.pass_test(f"Found {len(data)} products", {"count": len(data)})
        else:
            result.fail_test(f"Products endpoint failed: {data}")
        self.add_result(result)
        
        # Test categories
        result = ValidationResult("Marketplace", "Categories")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/marketplace/categories"
        )
        
        if status == 200:
            result.pass_test("Categories accessible", data)
        else:
            result.fail_test(f"Categories failed: {data}")
        self.add_result(result)
        
    async def validate_admin_features(self):
        """Validate admin-only features"""
        print("\n👮 VALIDATING ADMIN FEATURES...")
        
        if not self.tokens.get("admin"):
            return
            
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test audit logs
        result = ValidationResult("Admin", "Audit Logs")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/admin/audit-logs?limit=5",
            headers=headers
        )
        
        if status == 200:
            result.pass_test(f"Audit logs accessible", data)
        else:
            result.fail_test(f"Audit logs failed: {data}")
        self.add_result(result)
        
        # Test system status
        result = ValidationResult("Admin", "System Status")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/system/status",
            headers=headers
        )
        
        if status == 200:
            result.pass_test("System status accessible", data)
        else:
            result.fail_test(f"System status failed: {data}")
        self.add_result(result)
        
    async def validate_automations(self):
        """Validate automation systems"""
        print("\n⚡ VALIDATING AUTOMATIONS...")
        
        # Test automation status
        result = ValidationResult("Automations", "System Status")
        status, data = await self.test_endpoint(
            "GET",
            f"{BACKEND_URL}/api/{API_VERSION}/automations/status"
        )
        
        if status == 200:
            result.pass_test("Automation system accessible", data)
        else:
            result.fail_test(f"Automation status failed: {data}")
        self.add_result(result)
        
    async def validate_frontend(self):
        """Validate frontend availability"""
        print("\n🌐 VALIDATING FRONTEND...")
        
        result = ValidationResult("Frontend", "Homepage")
        status, _ = await self.test_endpoint("GET", FRONTEND_URL)
        
        if status == 200:
            result.pass_test("Frontend is accessible")
        else:
            result.fail_test(f"Frontend returned status {status}")
        self.add_result(result)
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {"pass": 0, "fail": 0, "tests": []}
            
            if result.status == "PASS":
                categories[result.category]["pass"] += 1
            else:
                categories[result.category]["fail"] += 1
                
            categories[result.category]["tests"].append({
                "test": result.test,
                "status": result.status,
                "message": result.message,
                "timestamp": result.timestamp.isoformat()
            })
            
        return {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "categories": categories,
            "all_tests": [
                {
                    "category": r.category,
                    "test": r.test,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*60)
        print("CLAUDEOS PRE-LAUNCH VALIDATION RESULTS")
        print("="*60)
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
            
        # Print each category
        for category, results in categories.items():
            print(f"\n{category}:")
            for result in results:
                icon = "✅" if result.status == "PASS" else "❌"
                print(f"  {icon} {result.test}: {result.message}")
                
        # Overall summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        
        print("\n" + "-"*60)
        print(f"TOTAL TESTS: {total}")
        print(f"PASSED: {passed} ({passed/total*100:.1f}%)")
        print(f"FAILED: {failed} ({failed/total*100:.1f}%)")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! SYSTEM IS READY FOR LAUNCH!")
        else:
            print("\n⚠️  SOME TESTS FAILED - REVIEW AND FIX BEFORE LAUNCH")
            
    async def run_validation(self):
        """Run complete validation suite"""
        print("🚀 STARTING CLAUDEOS PRE-LAUNCH VALIDATION...")
        print(f"Backend: {BACKEND_URL}")
        print(f"Frontend: {FRONTEND_URL}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        
        # 1. Authentication
        print("\n📋 PHASE 1: AUTHENTICATION")
        await self.authenticate("user")
        await self.authenticate("admin")
        
        # 2. Backend Systems
        print("\n📋 PHASE 2: BACKEND SYSTEMS")
        await self.validate_backend_health()
        await self.validate_memory_system()
        
        # 3. AI Systems
        print("\n📋 PHASE 3: AI SYSTEMS")
        await self.validate_aurea()
        await self.validate_langgraphos()
        
        # 4. Business Features
        print("\n📋 PHASE 4: BUSINESS FEATURES")
        await self.validate_marketplace()
        await self.validate_automations()
        
        # 5. Admin Features
        print("\n📋 PHASE 5: ADMIN FEATURES")
        await self.validate_admin_features()
        
        # 6. Frontend
        print("\n📋 PHASE 6: FRONTEND")
        await self.validate_frontend()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        with open("PRELAUNCH_VALIDATION_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        self.print_summary()
        
        # Return success status
        return report["summary"]["failed"] == 0

async def main():
    """Main entry point"""
    async with PreLaunchValidator() as validator:
        success = await validator.run_validation()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())