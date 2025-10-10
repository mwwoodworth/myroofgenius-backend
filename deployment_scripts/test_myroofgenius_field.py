#!/usr/bin/env python3
"""
MyRoofGenius Field Test Suite
Tests all critical roofing platform features
"""

import requests
import json
from datetime import datetime
import time

FRONTEND_URL = "https://www.myroofgenius.com"
BACKEND_URL = "https://brainops-backend-prod.onrender.com"

class MyRoofGeniusFieldTest:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "platform": "MyRoofGenius",
            "tests": {},
            "field_ready": False
        }
    
    def test_landing_page(self):
        """Test landing page loads with key elements"""
        try:
            resp = self.session.get(FRONTEND_URL)
            if resp.status_code == 200:
                content = resp.text
                checks = {
                    "title_present": "MyRoofGenius" in content,
                    "ai_features": "AI" in content or "artificial intelligence" in content.lower(),
                    "marketplace": "marketplace" in content.lower(),
                    "login_available": "login" in content.lower() or "sign in" in content.lower()
                }
                
                self.results["tests"]["landing_page"] = {
                    "status": "passed" if all(checks.values()) else "partial",
                    "checks": checks
                }
                return all(checks.values())
        except Exception as e:
            self.results["tests"]["landing_page"] = {"status": "failed", "error": str(e)}
        return False
    
    def test_auth_flow(self):
        """Test authentication pages"""
        auth_urls = {
            "login": f"{FRONTEND_URL}/login",
            "register": f"{FRONTEND_URL}/register"
        }
        
        results = {}
        for name, url in auth_urls.items():
            try:
                resp = self.session.get(url, allow_redirects=True)
                results[name] = {
                    "accessible": resp.status_code == 200,
                    "final_url": resp.url
                }
            except Exception as e:
                results[name] = {"error": str(e)}
        
        self.results["tests"]["auth_flow"] = results
        return any(r.get("accessible", False) for r in results.values())
    
    def test_key_pages(self):
        """Test key platform pages"""
        pages = [
            "/features",
            "/pricing", 
            "/marketplace",
            "/about",
            "/contact"
        ]
        
        results = {}
        accessible_count = 0
        
        for page in pages:
            try:
                resp = self.session.get(f"{FRONTEND_URL}{page}", allow_redirects=True)
                is_accessible = resp.status_code == 200
                results[page] = {
                    "status": resp.status_code,
                    "accessible": is_accessible
                }
                if is_accessible:
                    accessible_count += 1
            except Exception as e:
                results[page] = {"error": str(e)}
        
        self.results["tests"]["key_pages"] = {
            "accessible": f"{accessible_count}/{len(pages)}",
            "details": results
        }
        return accessible_count > len(pages) / 2
    
    def test_api_integration(self):
        """Test frontend-backend API integration"""
        # Test if frontend can reach backend
        api_tests = {
            "health_check": f"{BACKEND_URL}/api/v1/health",
            "roofing_materials": f"{BACKEND_URL}/api/v1/roofing/materials"
        }
        
        results = {}
        for name, url in api_tests.items():
            try:
                resp = requests.get(url)
                results[name] = {
                    "status": resp.status_code,
                    "success": resp.status_code in [200, 201]
                }
            except Exception as e:
                results[name] = {"error": str(e)}
        
        self.results["tests"]["api_integration"] = results
        return any(r.get("success", False) for r in results.values())
    
    def test_mobile_responsiveness(self):
        """Test mobile user agent access"""
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        }
        
        try:
            resp = requests.get(FRONTEND_URL, headers=mobile_headers)
            self.results["tests"]["mobile_responsiveness"] = {
                "status": "passed" if resp.status_code == 200 else "failed",
                "code": resp.status_code
            }
            return resp.status_code == 200
        except Exception as e:
            self.results["tests"]["mobile_responsiveness"] = {"status": "failed", "error": str(e)}
        return False
    
    def test_performance(self):
        """Test page load performance"""
        start_time = time.time()
        try:
            resp = requests.get(FRONTEND_URL)
            load_time = time.time() - start_time
            
            self.results["tests"]["performance"] = {
                "load_time": f"{load_time:.2f}s",
                "acceptable": load_time < 5.0  # 5 second threshold
            }
            return load_time < 5.0
        except Exception as e:
            self.results["tests"]["performance"] = {"status": "failed", "error": str(e)}
        return False
    
    def run_all_tests(self):
        """Run all MyRoofGenius field tests"""
        print("🏠 MyRoofGenius Field Test Suite")
        print("=" * 50)
        
        tests = [
            ("Landing Page", self.test_landing_page),
            ("Authentication Flow", self.test_auth_flow),
            ("Key Pages", self.test_key_pages),
            ("API Integration", self.test_api_integration),
            ("Mobile Access", self.test_mobile_responsiveness),
            ("Performance", self.test_performance)
        ]
        
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n🔧 Testing {test_name}...", end=" ", flush=True)
            try:
                passed = test_func()
                if passed:
                    print("✅ PASSED")
                    passed_tests += 1
                else:
                    print("⚠️  PARTIAL")
            except Exception as e:
                print(f"❌ ERROR: {e}")
        
        # Determine field readiness
        total_tests = len(tests)
        pass_rate = (passed_tests / total_tests) * 100
        self.results["field_ready"] = pass_rate >= 80
        self.results["pass_rate"] = f"{pass_rate:.1f}%"
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate field test report"""
        print("\n" + "=" * 50)
        print("📊 MYROOFGENIUS FIELD TEST REPORT")
        print("=" * 50)
        
        print(f"\n📅 Test Date: {self.results['timestamp']}")
        print(f"🎯 Pass Rate: {self.results['pass_rate']}")
        print(f"🚀 Field Ready: {'YES' if self.results['field_ready'] else 'NO'}")
        
        print("\n📋 Test Results:")
        for test_name, result in self.results["tests"].items():
            print(f"\n{test_name.upper()}:")
            if isinstance(result, dict):
                for key, value in result.items():
                    print(f"  - {key}: {value}")
        
        # Save results
        with open("/home/mwwoodworth/code/MYROOFGENIUS_FIELD_TEST.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: MYROOFGENIUS_FIELD_TEST.json")
        
        # Final verdict
        print("\n" + "=" * 50)
        if self.results["field_ready"]:
            print("✅ MYROOFGENIUS IS FIELD-READY!")
        else:
            print("⚠️  MYROOFGENIUS NEEDS ATTENTION BEFORE FIELD USE")
        print("=" * 50)

if __name__ == "__main__":
    tester = MyRoofGeniusFieldTest()
    tester.run_all_tests()