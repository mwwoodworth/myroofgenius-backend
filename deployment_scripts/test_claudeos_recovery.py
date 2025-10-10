#!/usr/bin/env python3
"""
ClaudeOS Full System Recovery Test Suite
Tests all critical endpoints and features for production verification
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple
import time

# Base URLs
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URL = "https://www.myroofgenius.com"

# Test credentials
TEST_USERS = {
    "admin": {"email": "admin@brainops.com", "password": "AdminPassword123!"},
    "test": {"email": "test@brainops.com", "password": "TestPassword123!"},
    "demo": {"email": "demo@myroofgenius.com", "password": "DemoPassword123!"}
}

class SystemVerifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "backend_version": None,
            "tests_passed": 0,
            "tests_failed": 0,
            "critical_issues": [],
            "test_results": {}
        }
        self.session = requests.Session()
        self.auth_token = None
    
    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            resp = self.session.get(f"{BACKEND_URL}/api/v1/health")
            if resp.status_code == 200:
                data = resp.json()
                self.results["backend_version"] = data.get("version")
                self.results["test_results"]["backend_health"] = {
                    "status": "passed",
                    "details": data
                }
                return True
        except Exception as e:
            self.results["test_results"]["backend_health"] = {
                "status": "failed",
                "error": str(e)
            }
        return False
    
    def test_authentication(self) -> bool:
        """Test authentication system"""
        try:
            # Test login
            resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={
                "email": TEST_USERS["test"]["email"],
                "password": TEST_USERS["test"]["password"]
            })
            
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Test protected endpoint
                resp2 = self.session.get(f"{BACKEND_URL}/api/v1/users/me")
                if resp2.status_code == 200:
                    self.results["test_results"]["authentication"] = {
                        "status": "passed",
                        "details": "Login and protected endpoints working"
                    }
                    return True
        except Exception as e:
            self.results["test_results"]["authentication"] = {
                "status": "failed",
                "error": str(e)
            }
        return False
    
    def test_aurea_endpoints(self) -> bool:
        """Test AUREA AI assistant endpoints"""
        aurea_tests = {
            "status": f"{BACKEND_URL}/api/v1/aurea/status",
            "health": f"{BACKEND_URL}/api/v1/aurea/health",
            "chat": f"{BACKEND_URL}/api/v1/aurea/chat"
        }
        
        all_passed = True
        results = {}
        
        for name, url in aurea_tests.items():
            try:
                if name == "chat":
                    # POST request for chat
                    resp = self.session.post(url, json={
                        "message": "Hello AUREA, what is the system status?"
                    })
                else:
                    resp = self.session.get(url)
                
                if resp.status_code in [200, 201]:
                    results[name] = "passed"
                else:
                    results[name] = f"failed (status: {resp.status_code})"
                    all_passed = False
            except Exception as e:
                results[name] = f"failed (error: {str(e)})"
                all_passed = False
        
        self.results["test_results"]["aurea_endpoints"] = {
            "status": "passed" if all_passed else "failed",
            "details": results
        }
        return all_passed
    
    def test_memory_system(self) -> bool:
        """Test persistent memory endpoints"""
        try:
            # Create memory
            resp = self.session.post(f"{BACKEND_URL}/api/v1/memory/create", json={
                "content": "Test memory entry from ClaudeOS recovery",
                "memory_type": "test",
                "metadata": {"test": True}
            })
            
            if resp.status_code in [200, 201]:
                # Search memory
                resp2 = self.session.post(f"{BACKEND_URL}/api/v1/memory/search", json={
                    "query": "ClaudeOS recovery"
                })
                
                if resp2.status_code == 200:
                    self.results["test_results"]["memory_system"] = {
                        "status": "passed",
                        "details": "Memory creation and search working"
                    }
                    return True
        except Exception as e:
            self.results["test_results"]["memory_system"] = {
                "status": "failed",
                "error": str(e)
            }
        return False
    
    def test_ai_services(self) -> bool:
        """Test AI service endpoints"""
        ai_tests = {
            "claude": f"{BACKEND_URL}/api/v1/ai/claude",
            "gemini": f"{BACKEND_URL}/api/v1/ai/gemini",
            "openai": f"{BACKEND_URL}/api/v1/ai/openai"
        }
        
        results = {}
        any_passed = False
        
        for name, url in ai_tests.items():
            try:
                resp = self.session.post(url, json={
                    "messages": [{"role": "user", "content": "Test message"}]
                })
                
                if resp.status_code in [200, 201]:
                    results[name] = "passed"
                    any_passed = True
                else:
                    results[name] = f"status: {resp.status_code}"
            except Exception as e:
                results[name] = f"error: {str(e)}"
        
        self.results["test_results"]["ai_services"] = {
            "status": "passed" if any_passed else "failed",
            "details": results
        }
        return any_passed
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend is accessible"""
        try:
            resp = requests.get(FRONTEND_URL, allow_redirects=True)
            if resp.status_code == 200 and "MyRoofGenius" in resp.text:
                self.results["test_results"]["frontend"] = {
                    "status": "passed",
                    "details": "Frontend accessible and loading"
                }
                return True
        except Exception as e:
            self.results["test_results"]["frontend"] = {
                "status": "failed",
                "error": str(e)
            }
        return False
    
    def test_webhook_endpoints(self) -> bool:
        """Test webhook endpoints are configured"""
        webhook_tests = {
            "render": f"{BACKEND_URL}/api/v1/webhooks/render",
            "vercel": f"{BACKEND_URL}/api/v1/webhooks/vercel"
        }
        
        results = {}
        all_exist = True
        
        for name, url in webhook_tests.items():
            try:
                # OPTIONS request to check if endpoint exists
                resp = requests.options(url)
                if resp.status_code in [200, 204, 405]:  # 405 means endpoint exists but method not allowed
                    results[name] = "exists"
                else:
                    results[name] = f"not found (status: {resp.status_code})"
                    all_exist = False
            except Exception as e:
                results[name] = f"error: {str(e)}"
                all_exist = False
        
        self.results["test_results"]["webhooks"] = {
            "status": "passed" if all_exist else "failed",
            "details": results
        }
        return all_exist
    
    def test_monitoring_endpoints(self) -> bool:
        """Test monitoring and health dashboard endpoints"""
        monitoring_tests = {
            "alerts": f"{BACKEND_URL}/api/v1/alerts",
            "health_dashboard": f"{BACKEND_URL}/api/v1/aurea/health/ui",
            "system_resources": f"{BACKEND_URL}/api/v1/admin/system/resources"
        }
        
        results = {}
        any_passed = False
        
        for name, url in monitoring_tests.items():
            try:
                resp = self.session.get(url)
                if resp.status_code in [200, 201]:
                    results[name] = "passed"
                    any_passed = True
                else:
                    results[name] = f"status: {resp.status_code}"
            except Exception as e:
                results[name] = f"error: {str(e)}"
        
        self.results["test_results"]["monitoring"] = {
            "status": "passed" if any_passed else "partial",
            "details": results
        }
        return any_passed
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🔍 ClaudeOS System Recovery Verification")
        print("=" * 50)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Authentication", self.test_authentication),
            ("AUREA Endpoints", self.test_aurea_endpoints),
            ("Memory System", self.test_memory_system),
            ("AI Services", self.test_ai_services),
            ("Frontend Access", self.test_frontend_accessibility),
            ("Webhook Config", self.test_webhook_endpoints),
            ("Monitoring", self.test_monitoring_endpoints)
        ]
        
        for test_name, test_func in tests:
            print(f"\n⚡ Testing {test_name}...", end=" ", flush=True)
            try:
                passed = test_func()
                if passed:
                    print("✅ PASSED")
                    self.results["tests_passed"] += 1
                else:
                    print("❌ FAILED")
                    self.results["tests_failed"] += 1
                    self.results["critical_issues"].append(test_name)
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.results["tests_failed"] += 1
                self.results["critical_issues"].append(f"{test_name}: {str(e)}")
        
        # Calculate system health
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        if total_tests > 0:
            health_percentage = (self.results["tests_passed"] / total_tests) * 100
            self.results["system_health"] = f"{health_percentage:.1f}%"
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate final summary report"""
        print("\n" + "=" * 50)
        print("📊 CLAUDEOS SYSTEM VERIFICATION SUMMARY")
        print("=" * 50)
        
        print(f"\n🏷️  Backend Version: {self.results['backend_version']}")
        print(f"📅 Test Date: {self.results['timestamp']}")
        print(f"\n✅ Tests Passed: {self.results['tests_passed']}")
        print(f"❌ Tests Failed: {self.results['tests_failed']}")
        print(f"💯 System Health: {self.results.get('system_health', 'N/A')}")
        
        if self.results["critical_issues"]:
            print("\n⚠️  Critical Issues:")
            for issue in self.results["critical_issues"]:
                print(f"   - {issue}")
        
        print("\n📋 Detailed Results:")
        for test_name, result in self.results["test_results"].items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"\n{status_icon} {test_name.upper()}:")
            if "details" in result:
                if isinstance(result["details"], dict):
                    for key, value in result["details"].items():
                        print(f"   - {key}: {value}")
                else:
                    print(f"   - {result['details']}")
            if "error" in result:
                print(f"   - Error: {result['error']}")
        
        # Save results to file
        with open("/home/mwwoodworth/code/CLAUDEOS_RECOVERY_RESULTS.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: CLAUDEOS_RECOVERY_RESULTS.json")
        
        # Final verdict
        print("\n" + "=" * 50)
        if self.results["tests_failed"] == 0:
            print("🎉 SYSTEM FULLY OPERATIONAL - Ready for production!")
        elif self.results["tests_passed"] > self.results["tests_failed"]:
            print("⚠️  SYSTEM PARTIALLY OPERATIONAL - Some issues need attention")
        else:
            print("🚨 SYSTEM CRITICAL - Major issues detected")
        print("=" * 50)

if __name__ == "__main__":
    verifier = SystemVerifier()
    verifier.run_all_tests()