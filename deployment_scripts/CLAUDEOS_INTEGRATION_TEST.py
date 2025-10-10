#!/usr/bin/env python3
"""
CLAUDEOS Full Stack Integration Test Suite
Tests every integration point, API endpoint, and workflow
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URL = "https://myroofgenius.com"
TEST_EMAIL = "integration_test@brainops.com"
TEST_PASSWORD = "IntegrationTest123!"

class IntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        self.critical_failures = []
        
    def log_result(self, test_name: str, status: str, details: str = "", critical: bool = False):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "FAIL" and critical:
            self.critical_failures.append(result)
            
        # Print live
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {test_name}: {status}")
        if details:
            print(f"   → {details}")
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            resp = self.session.get(f"{BACKEND_URL}/api/v1/health")
            if resp.status_code == 200:
                data = resp.json()
                self.log_result(
                    "Backend Health", 
                    "PASS", 
                    f"Version: {data.get('version')}, Routes: {data.get('routes_loaded')}"
                )
                return True
            else:
                self.log_result("Backend Health", "FAIL", f"Status: {resp.status_code}", critical=True)
                return False
        except Exception as e:
            self.log_result("Backend Health", "FAIL", str(e), critical=True)
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication flow"""
        # First try with test account
        try:
            login_data = {
                "username": "test@brainops.com",  # Try username field
                "password": "TestPassword123!"
            }
            resp = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access_token")
                self.log_result("Authentication", "PASS", "Login successful")
                return True
            else:
                # Try with email field
                login_data = {
                    "email": "test@brainops.com",
                    "password": "TestPassword123!"
                }
                resp = self.session.post(
                    f"{BACKEND_URL}/api/v1/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    self.access_token = data.get("access_token")
                    self.log_result("Authentication", "PASS", "Login successful (email field)")
                    return True
                else:
                    self.log_result("Authentication", "FAIL", f"Status: {resp.status_code}, Response: {resp.text[:200]}")
                    return False
                    
        except Exception as e:
            self.log_result("Authentication", "FAIL", str(e))
            return False
    
    def test_ai_endpoints(self) -> Dict[str, bool]:
        """Test all AI service endpoints"""
        results = {}
        
        # Test AUREA chat
        try:
            resp = self.session.post(
                f"{BACKEND_URL}/api/v1/aurea/chat",
                json={"message": "Test integration message"},
                headers=self._get_auth_headers()
            )
            if resp.status_code == 200:
                self.log_result("AUREA Chat", "PASS", "AI response received")
                results["aurea_chat"] = True
            else:
                self.log_result("AUREA Chat", "FAIL", f"Status: {resp.status_code}")
                results["aurea_chat"] = False
        except Exception as e:
            self.log_result("AUREA Chat", "FAIL", str(e))
            results["aurea_chat"] = False
            
        # Test AUREA status
        try:
            resp = self.session.get(f"{BACKEND_URL}/api/v1/aurea/status")
            if resp.status_code == 200:
                self.log_result("AUREA Status", "PASS")
                results["aurea_status"] = True
            else:
                self.log_result("AUREA Status", "FAIL", f"Status: {resp.status_code}")
                results["aurea_status"] = False
        except Exception as e:
            self.log_result("AUREA Status", "FAIL", str(e))
            results["aurea_status"] = False
            
        return results
    
    def test_memory_system(self) -> bool:
        """Test persistent memory system"""
        try:
            # Test memory creation
            memory_data = {
                "title": "Integration Test Memory",
                "content": f"Test memory created at {datetime.now().isoformat()}",
                "tags": ["test", "integration"],
                "memory_type": "test"
            }
            
            resp = self.session.post(
                f"{BACKEND_URL}/api/v1/memory/create",
                json=memory_data,
                headers=self._get_auth_headers()
            )
            
            if resp.status_code in [200, 201]:
                self.log_result("Memory Create", "PASS")
                
                # Test memory retrieval
                resp = self.session.get(
                    f"{BACKEND_URL}/api/v1/memory/recent?limit=5",
                    headers=self._get_auth_headers()
                )
                
                if resp.status_code == 200:
                    self.log_result("Memory Retrieval", "PASS", "Recent memories accessible")
                    return True
                else:
                    self.log_result("Memory Retrieval", "FAIL", f"Status: {resp.status_code}")
                    return False
            else:
                self.log_result("Memory Create", "FAIL", f"Status: {resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Memory System", "FAIL", str(e))
            return False
    
    def test_calculator_endpoints(self) -> Dict[str, bool]:
        """Test calculator endpoints"""
        results = {}
        
        calculators = [
            ("material", {"area": 2500, "roofType": "asphalt-shingle", "pitch": "5/12", "wasteFactorPercent": 10}),
            ("labor", {"area": 2500, "roofType": "asphalt-shingle", "complexity": "moderate", "workers": 4}),
            ("cost", {"area": 2500, "roofType": "asphalt-shingle", "quality": "mid", "location": "suburban"})
        ]
        
        for calc_type, data in calculators:
            try:
                resp = self.session.post(
                    f"{BACKEND_URL}/api/v1/roofing/calculator/{calc_type}",
                    json=data,
                    headers=self._get_auth_headers()
                )
                
                if resp.status_code == 200:
                    self.log_result(f"{calc_type.title()} Calculator", "PASS")
                    results[calc_type] = True
                else:
                    self.log_result(f"{calc_type.title()} Calculator", "FAIL", f"Status: {resp.status_code}")
                    results[calc_type] = False
                    
            except Exception as e:
                self.log_result(f"{calc_type.title()} Calculator", "FAIL", str(e))
                results[calc_type] = False
                
        return results
    
    def test_marketplace(self) -> bool:
        """Test marketplace endpoints"""
        try:
            # Test product listing
            resp = self.session.get(f"{BACKEND_URL}/api/v1/marketplace/products")
            
            if resp.status_code == 200:
                self.log_result("Marketplace Products", "PASS")
                
                # Test cart operations
                cart_data = {"product_id": "1", "quantity": 1}
                resp = self.session.post(
                    f"{BACKEND_URL}/api/v1/marketplace/cart/add",
                    json=cart_data,
                    headers=self._get_auth_headers()
                )
                
                if resp.status_code in [200, 201]:
                    self.log_result("Marketplace Cart", "PASS")
                    return True
                else:
                    self.log_result("Marketplace Cart", "FAIL", f"Status: {resp.status_code}")
                    return False
            else:
                self.log_result("Marketplace Products", "FAIL", f"Status: {resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Marketplace", "FAIL", str(e))
            return False
    
    def test_langgraphos(self) -> bool:
        """Test LangGraphOS automation orchestration"""
        try:
            # Test automation status
            resp = self.session.get(
                f"{BACKEND_URL}/api/v1/automations/status",
                headers=self._get_auth_headers()
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.log_result("LangGraphOS Status", "PASS", f"Active automations: {data.get('active_count', 0)}")
                
                # Test automation execution
                automation_data = {
                    "workflow": "test_integration",
                    "params": {"test": True}
                }
                
                resp = self.session.post(
                    f"{BACKEND_URL}/api/v1/automations/execute",
                    json=automation_data,
                    headers=self._get_auth_headers()
                )
                
                if resp.status_code in [200, 201]:
                    self.log_result("LangGraphOS Execution", "PASS")
                    return True
                else:
                    self.log_result("LangGraphOS Execution", "FAIL", f"Status: {resp.status_code}")
                    return False
            else:
                self.log_result("LangGraphOS Status", "FAIL", f"Status: {resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("LangGraphOS", "FAIL", str(e))
            return False
    
    def test_admin_endpoints(self) -> bool:
        """Test admin dashboard endpoints"""
        try:
            # Test admin stats
            resp = self.session.get(
                f"{BACKEND_URL}/api/v1/admin/stats",
                headers=self._get_auth_headers()
            )
            
            if resp.status_code == 200:
                self.log_result("Admin Stats", "PASS")
                
                # Test audit logs
                resp = self.session.get(
                    f"{BACKEND_URL}/api/v1/admin/audit/recent",
                    headers=self._get_auth_headers()
                )
                
                if resp.status_code == 200:
                    self.log_result("Admin Audit Logs", "PASS")
                    return True
                else:
                    self.log_result("Admin Audit Logs", "FAIL", f"Status: {resp.status_code}")
                    return False
            else:
                self.log_result("Admin Stats", "FAIL", f"Status: {resp.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Admin Endpoints", "FAIL", str(e))
            return False
    
    def test_frontend_routes(self) -> Dict[str, bool]:
        """Test key frontend routes"""
        results = {}
        
        routes = [
            "/",
            "/login",
            "/roofbuddy",
            "/aurea-dashboard",
            "/fieldgenius",
            "/marketplace",
            "/marketplace/cart",
            "/tools/material-calculator",
            "/tools/labor-estimator",
            "/profile"
        ]
        
        for route in routes:
            try:
                resp = requests.get(f"{FRONTEND_URL}{route}", timeout=10)
                if resp.status_code == 200:
                    self.log_result(f"Frontend {route}", "PASS")
                    results[route] = True
                else:
                    self.log_result(f"Frontend {route}", "FAIL", f"Status: {resp.status_code}")
                    results[route] = False
                    
            except Exception as e:
                self.log_result(f"Frontend {route}", "FAIL", str(e))
                results[route] = False
                
        return results
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def generate_report(self):
        """Generate final integration report"""
        print("\n" + "="*80)
        print("CLAUDEOS INTEGRATION TEST REPORT")
        print("="*80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print("\n")
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "FAIL")
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        if self.critical_failures:
            print(f"\n⚠️  CRITICAL FAILURES: {len(self.critical_failures)}")
            for failure in self.critical_failures:
                print(f"   - {failure['test']}: {failure['details']}")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        print("-"*80)
        
        for result in self.test_results:
            symbol = "✅" if result["status"] == "PASS" else "❌"
            print(f"{symbol} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"   Details: {result['details']}")
        
        print("\n" + "="*80)
        
        # Final verdict
        if failed_tests == 0:
            print("✅ ALL SYSTEMS OPERATIONAL - READY FOR LAUNCH")
        elif len(self.critical_failures) > 0:
            print("❌ CRITICAL FAILURES DETECTED - NOT READY FOR LAUNCH")
        else:
            print("⚠️  MINOR ISSUES DETECTED - REVIEW BEFORE LAUNCH")
        
        print("="*80)

def main():
    """Run full integration test suite"""
    print("Starting CLAUDEOS Full Stack Integration Tests...")
    print("="*80)
    
    tester = IntegrationTester()
    
    # 1. Test backend health
    print("\n1. BACKEND HEALTH CHECK")
    print("-"*40)
    backend_ok = tester.test_backend_health()
    
    if not backend_ok:
        print("\n❌ CRITICAL: Backend is not healthy. Aborting tests.")
        tester.generate_report()
        return
    
    # 2. Test authentication
    print("\n2. AUTHENTICATION SYSTEM")
    print("-"*40)
    auth_ok = tester.test_authentication()
    
    # 3. Test AI endpoints
    print("\n3. AI SERVICE ENDPOINTS")
    print("-"*40)
    ai_results = tester.test_ai_endpoints()
    
    # 4. Test memory system
    print("\n4. PERSISTENT MEMORY SYSTEM")
    print("-"*40)
    memory_ok = tester.test_memory_system()
    
    # 5. Test calculators
    print("\n5. CALCULATOR ENDPOINTS")
    print("-"*40)
    calc_results = tester.test_calculator_endpoints()
    
    # 6. Test marketplace
    print("\n6. MARKETPLACE SYSTEM")
    print("-"*40)
    marketplace_ok = tester.test_marketplace()
    
    # 7. Test LangGraphOS
    print("\n7. LANGGRAPHOS ORCHESTRATION")
    print("-"*40)
    langgraphos_ok = tester.test_langgraphos()
    
    # 8. Test admin endpoints
    print("\n8. ADMIN DASHBOARD")
    print("-"*40)
    admin_ok = tester.test_admin_endpoints()
    
    # 9. Test frontend routes
    print("\n9. FRONTEND ROUTES")
    print("-"*40)
    frontend_results = tester.test_frontend_routes()
    
    # Generate final report
    tester.generate_report()

if __name__ == "__main__":
    main()