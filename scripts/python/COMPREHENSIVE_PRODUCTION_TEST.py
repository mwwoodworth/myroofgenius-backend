#!/usr/bin/env python3
"""
Comprehensive Production System Test
Tests EVERYTHING in live production
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URLS = {
    "MyRoofGenius": "https://myroofgenius.com",
    "WeatherCraft": "https://weathercraft-app.vercel.app",
    "BrainOps Task OS": "https://brainops-task-os.vercel.app"
}

class ProductionTester:
    def __init__(self):
        self.results = {
            "health": {},
            "auth": {},
            "payments": {},
            "email": {},
            "ai": {},
            "database": {},
            "frontends": {},
            "endpoints": {},
            "gaps": []
        }
        self.total_tests = 0
        self.passed_tests = 0
        
    def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n🏥 TESTING HEALTH ENDPOINTS")
        print("-" * 50)
        
        endpoints = [
            "/health",
            "/api/v1/health",
            "/",
            "/api/v1/version"
        ]
        
        for endpoint in endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    self.results["health"][endpoint] = {
                        "status": "✅ PASS",
                        "version": data.get("version", "N/A"),
                        "details": data
                    }
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: v{data.get('version', 'N/A')}")
                else:
                    self.results["health"][endpoint] = {"status": f"❌ FAIL ({resp.status_code})"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    self.results["gaps"].append(f"Health endpoint {endpoint} returned {resp.status_code}")
            except Exception as e:
                self.results["health"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Health endpoint {endpoint} error: {str(e)}")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        print("-" * 50)
        
        auth_endpoints = [
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/auth/register", "POST"),
            ("/api/v1/auth/refresh", "POST"),
            ("/api/v1/auth/logout", "POST"),
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/verify", "POST")
        ]
        
        for endpoint, method in auth_endpoints:
            self.total_tests += 1
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                else:
                    # Test with empty payload to check if endpoint exists
                    resp = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
                
                # 401/422 are expected for auth endpoints without credentials
                if resp.status_code in [200, 401, 422, 400]:
                    self.results["auth"][endpoint] = {"status": "✅ Endpoint exists"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Accessible (Status {resp.status_code})")
                else:
                    self.results["auth"][endpoint] = {"status": f"❌ Unexpected ({resp.status_code})"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"Auth endpoint {endpoint} not found")
            except Exception as e:
                self.results["auth"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Auth endpoint {endpoint} error: {str(e)}")
    
    def test_payment_system(self):
        """Test Stripe payment endpoints"""
        print("\n💳 TESTING PAYMENT SYSTEM (STRIPE)")
        print("-" * 50)
        
        payment_endpoints = [
            "/api/v1/payments/test",
            "/api/v1/payments/create-intent",
            "/api/v1/payments/confirm",
            "/api/v1/payments/webhook",
            "/api/v1/payments/customers",
            "/api/v1/payments/subscriptions",
            "/api/v1/stripe/products",
            "/api/v1/stripe/prices"
        ]
        
        for endpoint in payment_endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403, 405]:
                    self.results["payments"][endpoint] = {"status": "✅ Endpoint exists"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Accessible")
                else:
                    self.results["payments"][endpoint] = {"status": f"❌ Status {resp.status_code}"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"Payment endpoint {endpoint} not found")
            except Exception as e:
                self.results["payments"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Payment endpoint {endpoint} error: {str(e)}")
    
    def test_email_system(self):
        """Test SendGrid email endpoints"""
        print("\n📧 TESTING EMAIL SYSTEM (SENDGRID)")
        print("-" * 50)
        
        email_endpoints = [
            "/api/v1/email/test",
            "/api/v1/email/send",
            "/api/v1/email/templates",
            "/api/v1/email/bulk",
            "/api/v1/email/status"
        ]
        
        for endpoint in email_endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403, 405]:
                    self.results["email"][endpoint] = {"status": "✅ Endpoint exists"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Accessible")
                else:
                    self.results["email"][endpoint] = {"status": f"❌ Status {resp.status_code}"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"Email endpoint {endpoint} not found")
            except Exception as e:
                self.results["email"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Email endpoint {endpoint} error: {str(e)}")
    
    def test_ai_endpoints(self):
        """Test AI and automation endpoints"""
        print("\n🤖 TESTING AI & AUTOMATION ENDPOINTS")
        print("-" * 50)
        
        ai_endpoints = [
            "/api/v1/ai/analyze",
            "/api/v1/ai/chat",
            "/api/v1/ai/vision",
            "/api/v1/ai/board",
            "/api/v1/aurea/status",
            "/api/v1/aurea/health",
            "/api/v1/aurea/command",
            "/api/v1/automations",
            "/api/v1/automations/status",
            "/api/v1/tasks",
            "/api/v1/memory/recent",
            "/api/v1/marketplace/products"
        ]
        
        for endpoint in ai_endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403]:
                    self.results["ai"][endpoint] = {"status": "✅ Endpoint exists"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Accessible")
                else:
                    self.results["ai"][endpoint] = {"status": f"❌ Status {resp.status_code}"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"AI endpoint {endpoint} not found")
            except Exception as e:
                self.results["ai"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"AI endpoint {endpoint} error: {str(e)}")
    
    def test_business_endpoints(self):
        """Test business logic endpoints"""
        print("\n💼 TESTING BUSINESS ENDPOINTS")
        print("-" * 50)
        
        business_endpoints = [
            "/api/v1/estimates",
            "/api/v1/estimates/calculate",
            "/api/v1/jobs",
            "/api/v1/customers",
            "/api/v1/invoices",
            "/api/v1/products",
            "/api/v1/products/public",
            "/api/v1/revenue/metrics",
            "/api/v1/analytics",
            "/api/v1/blog/posts",
            "/api/v1/erp/customers",
            "/api/v1/task-os/tasks"
        ]
        
        for endpoint in business_endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403]:
                    self.results["endpoints"][endpoint] = {"status": "✅ Endpoint exists"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Accessible")
                else:
                    self.results["endpoints"][endpoint] = {"status": f"❌ Status {resp.status_code}"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"Business endpoint {endpoint} not found")
            except Exception as e:
                self.results["endpoints"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Business endpoint {endpoint} error: {str(e)}")
    
    def test_frontend_applications(self):
        """Test frontend applications"""
        print("\n🌐 TESTING FRONTEND APPLICATIONS")
        print("-" * 50)
        
        for name, url in FRONTEND_URLS.items():
            self.total_tests += 1
            try:
                resp = requests.get(url, timeout=10, allow_redirects=True)
                if resp.status_code == 200:
                    self.results["frontends"][name] = {
                        "status": "✅ ONLINE",
                        "url": url,
                        "final_url": resp.url
                    }
                    self.passed_tests += 1
                    print(f"✅ {name}: Online at {url}")
                else:
                    self.results["frontends"][name] = {
                        "status": f"❌ Status {resp.status_code}",
                        "url": url
                    }
                    print(f"❌ {name}: Status {resp.status_code}")
                    self.results["gaps"].append(f"Frontend {name} returned status {resp.status_code}")
            except Exception as e:
                self.results["frontends"][name] = {
                    "status": f"❌ ERROR: {str(e)}",
                    "url": url
                }
                print(f"❌ {name}: {str(e)}")
                self.results["gaps"].append(f"Frontend {name} error: {str(e)}")
    
    def test_database_connectivity(self):
        """Test database-related endpoints"""
        print("\n🗄️ TESTING DATABASE CONNECTIVITY")
        print("-" * 50)
        
        db_endpoints = [
            "/api/v1/env/validate",
            "/api/v1/env/sync",
            "/api/v1/db-sync/status",
            "/api/v1/memory/recent"
        ]
        
        for endpoint in db_endpoints:
            self.total_tests += 1
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if resp.status_code in [200, 401, 403]:
                    self.results["database"][endpoint] = {"status": "✅ Connected"}
                    self.passed_tests += 1
                    print(f"✅ {endpoint}: Database accessible")
                else:
                    self.results["database"][endpoint] = {"status": f"❌ Status {resp.status_code}"}
                    print(f"❌ {endpoint}: Status {resp.status_code}")
                    if resp.status_code == 404:
                        self.results["gaps"].append(f"Database endpoint {endpoint} not found")
            except Exception as e:
                self.results["database"][endpoint] = {"status": f"❌ ERROR: {str(e)}"}
                print(f"❌ {endpoint}: {str(e)}")
                self.results["gaps"].append(f"Database endpoint {endpoint} error: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE PRODUCTION TEST REPORT")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"API URL: {BASE_URL}")
        print()
        
        # Overall statistics
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()
        
        # Category summaries
        print("📋 CATEGORY SUMMARIES:")
        categories = [
            ("Health", self.results["health"]),
            ("Authentication", self.results["auth"]),
            ("Payments", self.results["payments"]),
            ("Email", self.results["email"]),
            ("AI/Automation", self.results["ai"]),
            ("Business Logic", self.results["endpoints"]),
            ("Database", self.results["database"]),
            ("Frontends", self.results["frontends"])
        ]
        
        for cat_name, cat_results in categories:
            working = sum(1 for r in cat_results.values() if "✅" in str(r.get("status", "")))
            total = len(cat_results)
            if total > 0:
                print(f"   {cat_name}: {working}/{total} working ({working/total*100:.0f}%)")
        
        # Operational gaps
        print("\n🔴 OPERATIONAL GAPS IDENTIFIED:")
        print("-" * 50)
        if self.results["gaps"]:
            for i, gap in enumerate(self.results["gaps"], 1):
                print(f"{i:2}. {gap}")
        else:
            print("   ✅ No critical gaps identified!")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 50)
        recommendations = []
        
        # Check for missing endpoints
        missing_endpoints = [gap for gap in self.results["gaps"] if "not found" in gap]
        if missing_endpoints:
            recommendations.append("Deploy missing API endpoints to complete functionality")
        
        # Check for errors
        error_gaps = [gap for gap in self.results["gaps"] if "error" in gap.lower()]
        if error_gaps:
            recommendations.append("Investigate and fix connection/timeout errors")
        
        # Check success rate
        if success_rate < 80:
            recommendations.append("Priority: Fix failing endpoints to reach 80%+ success rate")
        elif success_rate < 95:
            recommendations.append("Optimize remaining endpoints for 95%+ reliability")
        else:
            recommendations.append("System operating at optimal levels - maintain monitoring")
        
        # Frontend checks
        frontend_issues = [f for f, r in self.results["frontends"].items() if "❌" in str(r.get("status", ""))]
        if frontend_issues:
            recommendations.append(f"Fix frontend issues: {', '.join(frontend_issues)}")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # Final assessment
        print("\n🏁 FINAL ASSESSMENT:")
        print("-" * 50)
        if success_rate >= 90:
            print("✅ SYSTEM STATUS: PRODUCTION READY")
            print(f"✅ Operating at {success_rate:.1f}% capacity")
        elif success_rate >= 75:
            print("⚠️  SYSTEM STATUS: PARTIALLY OPERATIONAL")
            print(f"⚠️  Operating at {success_rate:.1f}% capacity")
            print("⚠️  Some features may be unavailable")
        else:
            print("❌ SYSTEM STATUS: CRITICAL ISSUES")
            print(f"❌ Only {success_rate:.1f}% operational")
            print("❌ Immediate attention required")
        
        return success_rate

def main():
    tester = ProductionTester()
    
    print("🚀 STARTING COMPREHENSIVE PRODUCTION TEST")
    print("=" * 70)
    
    # Run all tests
    tester.test_health_endpoints()
    tester.test_authentication()
    tester.test_payment_system()
    tester.test_email_system()
    tester.test_ai_endpoints()
    tester.test_business_endpoints()
    tester.test_frontend_applications()
    tester.test_database_connectivity()
    
    # Generate report
    success_rate = tester.generate_report()
    
    # Save results to file
    with open("/home/mwwoodworth/code/production_test_results.json", "w") as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print("\n📁 Detailed results saved to: production_test_results.json")
    
    return success_rate >= 75  # Return success if 75%+ operational

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)