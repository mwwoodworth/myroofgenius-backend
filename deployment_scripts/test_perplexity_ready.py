#!/usr/bin/env python3
"""
Perplexity-Ready Validation Script
Comprehensive testing for all critical features
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

BASE_URL = "https://myroofgenius.com"
API_URL = "https://brainops-backend-prod.onrender.com"

class PerplexityValidator:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.access_token = None
        self.test_user = None
    
    def add_result(self, category: str, test: str, passed: bool, details: str):
        """Add test result"""
        self.results.append({
            "category": category,
            "test": test,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_backend_health(self) -> bool:
        """Test backend API health"""
        try:
            resp = requests.get(f"{API_URL}/api/v1/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                version = data.get("version", "unknown")
                self.add_result("Backend", "API Health", True, f"Healthy - v{version}")
                return True
            else:
                self.add_result("Backend", "API Health", False, f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("Backend", "API Health", False, str(e))
            return False
    
    def test_registration(self) -> bool:
        """Test user registration"""
        try:
            test_email = f"perplexity_test_{int(time.time())}@example.com"
            data = {
                "email": test_email,
                "password": "SecurePassword123!",
                "full_name": "Perplexity Test User"
            }
            
            resp = requests.post(
                f"{API_URL}/api/v1/auth/register",
                json=data,
                timeout=10
            )
            
            if resp.status_code in [200, 201]:
                result = resp.json()
                self.access_token = result.get("access_token")
                self.test_user = result.get("user", {})
                self.add_result("Authentication", "User Registration", True, 
                               f"User created: {test_email}")
                return True
            else:
                self.add_result("Authentication", "User Registration", False, 
                               f"Status {resp.status_code}: {resp.text[:100]}")
                return False
        except Exception as e:
            self.add_result("Authentication", "User Registration", False, str(e))
            return False
    
    def test_login(self) -> bool:
        """Test user login"""
        try:
            # Use known test credentials
            data = {
                "email": "test@brainops.com",
                "password": "TestPassword123!"
            }
            
            resp = requests.post(
                f"{API_URL}/api/v1/auth/login",
                json=data,
                timeout=10
            )
            
            if resp.status_code == 200:
                result = resp.json()
                if not self.access_token:
                    self.access_token = result.get("access_token")
                self.add_result("Authentication", "User Login", True, 
                               "Login successful with test account")
                return True
            else:
                self.add_result("Authentication", "User Login", False, 
                               f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("Authentication", "User Login", False, str(e))
            return False
    
    def test_protected_routes(self) -> bool:
        """Test protected API routes"""
        if not self.access_token:
            self.add_result("Protected Routes", "API Access", False, 
                           "No access token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test user profile endpoint
        try:
            resp = requests.get(
                f"{API_URL}/api/v1/users/me",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                self.add_result("Protected Routes", "User Profile", True, 
                               "Protected route accessible")
                return True
            else:
                self.add_result("Protected Routes", "User Profile", False, 
                               f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("Protected Routes", "User Profile", False, str(e))
            return False
    
    def test_frontend_routes(self) -> Tuple[int, List[str]]:
        """Test all critical frontend routes"""
        routes = [
            ("/", "Homepage"),
            ("/login", "Login Page"),
            ("/signup", "Signup Page"),
            ("/dashboard", "User Dashboard"),
            ("/admin", "Admin Panel"),
            ("/blog", "Blog"),
            ("/material-calculator", "Material Calculator"),
            ("/labor-estimator", "Labor Estimator"),
            ("/marketplace", "Marketplace"),
            ("/tools", "Tools"),
            ("/forgot-password", "Forgot Password"),
            ("/profile", "User Profile")
        ]
        
        working = 0
        broken = []
        
        for route, name in routes:
            try:
                resp = requests.get(f"{BASE_URL}{route}", 
                                  allow_redirects=True, 
                                  timeout=10)
                
                # Check if it's accessible or redirects to login (protected)
                if resp.status_code == 200 or "/login" in resp.url:
                    working += 1
                    self.add_result("Frontend Routes", name, True, 
                                   f"Accessible at {route}")
                else:
                    broken.append(f"{name} ({route}): {resp.status_code}")
                    self.add_result("Frontend Routes", name, False, 
                                   f"Status {resp.status_code}")
            except Exception as e:
                broken.append(f"{name} ({route}): {str(e)}")
                self.add_result("Frontend Routes", name, False, str(e))
        
        return working, broken
    
    def test_aurea_ai(self) -> bool:
        """Test AUREA AI functionality"""
        if not self.access_token:
            # Try without auth first
            try:
                resp = requests.get(f"{API_URL}/api/v1/aurea/status", timeout=10)
                if resp.status_code in [200, 401]:
                    self.add_result("AUREA AI", "Status Endpoint", True, 
                                   "AUREA endpoint exists")
                    return True
                else:
                    self.add_result("AUREA AI", "Status Endpoint", False, 
                                   f"Status {resp.status_code}")
                    return False
            except Exception as e:
                self.add_result("AUREA AI", "Status Endpoint", False, str(e))
                return False
        
        # Test with auth
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # Test AUREA chat
            data = {
                "message": "What roofing materials are best for Colorado weather?"
            }
            
            resp = requests.post(
                f"{API_URL}/api/v1/aurea/chat",
                json=data,
                headers=headers,
                timeout=15
            )
            
            if resp.status_code == 200:
                result = resp.json()
                response = result.get("response", "")
                
                # Check if response is real AI or template
                if len(response) > 100 and "colorado" in response.lower():
                    self.add_result("AUREA AI", "Chat Response", True, 
                                   "Real AI response received")
                    return True
                else:
                    self.add_result("AUREA AI", "Chat Response", False, 
                                   "Template or short response")
                    return False
            else:
                self.add_result("AUREA AI", "Chat Response", False, 
                               f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("AUREA AI", "Chat Response", False, str(e))
            return False
    
    def test_calculators(self) -> bool:
        """Test calculator functionality"""
        # Test material calculator API
        try:
            if self.access_token:
                headers = {"Authorization": f"Bearer {self.access_token}"}
            else:
                headers = {}
            
            data = {
                "roof_area": 2000,
                "roof_type": "asphalt_shingle",
                "pitch": "6/12"
            }
            
            resp = requests.post(
                f"{API_URL}/api/v1/calculators/material",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code in [200, 401]:
                if resp.status_code == 200:
                    self.add_result("Calculators", "Material Calculator API", True, 
                                   "Calculator working")
                else:
                    self.add_result("Calculators", "Material Calculator API", True, 
                                   "Calculator exists (auth required)")
                return True
            else:
                self.add_result("Calculators", "Material Calculator API", False, 
                               f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("Calculators", "Material Calculator API", False, str(e))
            return False
    
    def test_persistent_memory(self) -> bool:
        """Test persistent memory system"""
        if not self.access_token:
            self.add_result("Persistent Memory", "Memory API", False, 
                           "No access token")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # Create memory entry
            data = {
                "content": f"Perplexity validation test at {datetime.now()}",
                "owner_type": "user",
                "owner_id": self.test_user.get("id", "test"),
                "memory_type": "test"
            }
            
            resp = requests.post(
                f"{API_URL}/api/v1/memory/create",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code in [200, 201]:
                self.add_result("Persistent Memory", "Create Memory", True, 
                               "Memory system operational")
                return True
            else:
                self.add_result("Persistent Memory", "Create Memory", False, 
                               f"Status {resp.status_code}")
                return False
        except Exception as e:
            self.add_result("Persistent Memory", "Create Memory", False, str(e))
            return False
    
    def generate_audit_dashboard(self) -> str:
        """Generate audit dashboard HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MyRoofGenius - Perplexity Audit Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .category {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .passed {{ color: #10b981; font-weight: bold; }}
        .failed {{ color: #ef4444; font-weight: bold; }}
        .test-item {{ padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .test-item:last-child {{ border-bottom: none; }}
        .progress {{ background: #e5e7eb; height: 30px; border-radius: 15px; overflow: hidden; }}
        .progress-bar {{ background: #10b981; height: 100%; text-align: center; line-height: 30px; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 MyRoofGenius - Perplexity Audit Dashboard</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Overall Status</h2>
        <div class="progress">
            <div class="progress-bar" style="width: {(self.passed / (self.passed + self.failed) * 100):.0f}%">
                {(self.passed / (self.passed + self.failed) * 100):.0f}% Passed
            </div>
        </div>
        <p>✅ Passed: <span class="passed">{self.passed}</span> | 
           ❌ Failed: <span class="failed">{self.failed}</span> | 
           📊 Total: {self.passed + self.failed}</p>
    </div>
"""
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Add each category
        for cat, tests in categories.items():
            passed_count = sum(1 for t in tests if t["passed"])
            total_count = len(tests)
            
            html += f"""
    <div class="category">
        <h3>{cat} ({passed_count}/{total_count})</h3>
"""
            
            for test in tests:
                status = "✅" if test["passed"] else "❌"
                css_class = "passed" if test["passed"] else "failed"
                html += f"""
        <div class="test-item">
            {status} <span class="{css_class}">{test['test']}</span>: {test['details']}
        </div>
"""
            
            html += "    </div>\n"
        
        # Add critical issues summary
        critical_issues = [r for r in self.results if not r["passed"] and 
                          r["category"] in ["Authentication", "Backend", "AUREA AI"]]
        
        if critical_issues:
            html += """
    <div class="category" style="background: #fef2f2; border: 2px solid #ef4444;">
        <h3>🚨 Critical Issues Requiring Immediate Attention</h3>
"""
            for issue in critical_issues:
                html += f"""
        <div class="test-item">
            ❌ <span class="failed">{issue['category']} - {issue['test']}</span>: {issue['details']}
        </div>
"""
            html += "    </div>\n"
        
        # Add recommendation
        if self.failed == 0:
            recommendation = "✅ READY FOR PERPLEXITY AUDIT - All systems operational!"
            rec_style = "background: #d1fae5; border: 2px solid #10b981;"
        elif len(critical_issues) > 0:
            recommendation = "❌ NOT READY - Critical issues must be resolved first"
            rec_style = "background: #fef2f2; border: 2px solid #ef4444;"
        else:
            recommendation = "⚠️ MOSTLY READY - Minor issues should be addressed"
            rec_style = "background: #fef3c7; border: 2px solid #f59e0b;"
        
        html += f"""
    <div class="category" style="{rec_style}">
        <h3>📋 Final Recommendation</h3>
        <p style="font-size: 18px; margin: 10px 0;">{recommendation}</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def run_full_validation(self):
        """Run complete validation suite"""
        print("\n🔍 PERPLEXITY-READY VALIDATION SUITE")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Frontend: {BASE_URL}")
        print(f"Backend: {API_URL}")
        print("=" * 60)
        
        # Run all tests
        print("\n1️⃣ Testing Backend Health...")
        self.test_backend_health()
        
        print("\n2️⃣ Testing User Registration...")
        self.test_registration()
        
        print("\n3️⃣ Testing User Login...")
        self.test_login()
        
        print("\n4️⃣ Testing Protected Routes...")
        self.test_protected_routes()
        
        print("\n5️⃣ Testing Frontend Routes...")
        working, broken = self.test_frontend_routes()
        
        print("\n6️⃣ Testing AUREA AI...")
        self.test_aurea_ai()
        
        print("\n7️⃣ Testing Calculators...")
        self.test_calculators()
        
        print("\n8️⃣ Testing Persistent Memory...")
        self.test_persistent_memory()
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        # Critical issues
        critical = [r for r in self.results if not r["passed"] and 
                   r["category"] in ["Authentication", "Backend", "AUREA AI"]]
        
        if critical:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in critical:
                print(f"  - {issue['category']}: {issue['test']} - {issue['details']}")
        
        # Generate audit dashboard
        dashboard_html = self.generate_audit_dashboard()
        with open("perplexity_audit_dashboard.html", "w") as f:
            f.write(dashboard_html)
        
        print("\n📄 Audit dashboard saved to: perplexity_audit_dashboard.html")
        
        # Final verdict
        if self.failed == 0:
            print("\n✅ READY FOR PERPLEXITY AUDIT - All tests passed!")
        elif len(critical) > 0:
            print("\n❌ NOT READY - Critical issues must be resolved")
        else:
            print("\n⚠️  MOSTLY READY - Minor issues should be addressed")
        
        print("=" * 60)

if __name__ == "__main__":
    validator = PerplexityValidator()
    validator.run_full_validation()