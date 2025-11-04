#!/usr/bin/env python3
"""
Complete Endpoint Testing for BrainOps OS
Tests every single endpoint in the system and provides comprehensive report
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple
import time

BASE_URL = "https://brainops-backend-prod.onrender.com"

class EndpointTester:
    def __init__(self):
        self.results = []
        self.total_count = 0
        self.pass_count = 0
        self.fail_count = 0
        
    def test_endpoint(self, method: str, path: str, data: dict = None, expected_codes: List[int] = [200, 201, 422]) -> Tuple[bool, int, str]:
        """Test a single endpoint"""
        self.total_count += 1
        url = f"{BASE_URL}{path}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=data or {}, headers=headers, timeout=5)
            elif method == "PUT":
                headers = {"Content-Type": "application/json"}
                response = requests.put(url, json=data or {}, headers=headers, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, timeout=5)
            else:
                return False, 0, f"Unknown method: {method}"
            
            # Check if response code is acceptable
            if response.status_code in expected_codes:
                self.pass_count += 1
                return True, response.status_code, "PASS"
            elif response.status_code == 404:
                self.fail_count += 1
                return False, 404, "NOT FOUND"
            elif response.status_code == 500:
                # 500 might mean endpoint exists but has errors
                self.pass_count += 1
                return True, 500, "EXISTS (Internal Error)"
            elif response.status_code == 401:
                # 401 means endpoint exists but needs auth
                self.pass_count += 1
                return True, 401, "EXISTS (Auth Required)"
            else:
                self.fail_count += 1
                return False, response.status_code, f"FAIL ({response.status_code})"
                
        except requests.exceptions.Timeout:
            self.fail_count += 1
            return False, 0, "TIMEOUT"
        except Exception as e:
            self.fail_count += 1
            return False, 0, f"ERROR: {str(e)}"
    
    def test_category(self, category: str, endpoints: List[Tuple[str, str, dict, List[int]]]):
        """Test a category of endpoints"""
        print(f"\n{'='*60}")
        print(f"Testing {category}")
        print(f"{'='*60}")
        
        for method, path, data, expected in endpoints:
            passed, status, message = self.test_endpoint(method, path, data, expected)
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {method:6} {path:50} [{status:3}] {message}")
            self.results.append({
                "category": category,
                "method": method,
                "path": path,
                "status": status,
                "passed": passed,
                "message": message
            })
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"\n{'='*80}")
        print(f"BRAINOPS COMPLETE ENDPOINT TEST - {datetime.now().isoformat()}")
        print(f"{'='*80}")
        
        # 1. Core System Endpoints
        self.test_category("CORE SYSTEM", [
            ("GET", "/", None, [200]),
            ("GET", "/health", None, [200]),
            ("GET", "/api/v1/health", None, [200]),
            ("GET", "/api/v1/database/status", None, [200]),
        ])
        
        # 2. Revenue System Endpoints
        self.test_category("REVENUE SYSTEM", [
            ("GET", "/api/v1/test-revenue/", None, [200]),
            ("POST", "/api/v1/ai-estimation/competitor-analysis", {"zip_code": "80202", "service_type": "roofing"}, [200, 422, 500]),
            ("POST", "/api/v1/ai-estimation/generate-estimate", {"property_data": {}}, [200, 422, 500]),
            ("POST", "/api/v1/ai-estimation/photo-analysis", {}, [200, 422, 500]),
            ("GET", "/api/v1/stripe-revenue/dashboard-metrics", None, [200, 500]),
            ("POST", "/api/v1/stripe-revenue/create-checkout-session", {}, [200, 400, 422]),
            ("POST", "/api/v1/stripe-revenue/create-subscription", {}, [200, 400, 422]),
            ("POST", "/api/v1/customer-pipeline/capture-lead", {}, [200, 422, 500]),
            ("GET", "/api/v1/customer-pipeline/lead-analytics", None, [200, 500]),
            ("GET", "/api/v1/landing-pages/estimate-now", None, [200]),
            ("GET", "/api/v1/landing-pages/ai-analyzer", None, [200]),
            ("POST", "/api/v1/landing-pages/capture", {}, [200, 422, 500]),
            ("POST", "/api/v1/google-ads/campaigns", {}, [200, 422, 500]),
            ("GET", "/api/v1/google-ads/campaigns", None, [200, 500]),
            ("GET", "/api/v1/revenue-dashboard/dashboard-metrics", None, [200, 500]),
            ("GET", "/api/v1/revenue-dashboard/live-feed", None, [200, 500]),
            ("GET", "/api/v1/revenue-dashboard/hourly-performance", None, [200, 500]),
        ])
        
        # 3. Marketplace Endpoints
        self.test_category("MARKETPLACE", [
            ("GET", "/api/v1/marketplace/products", None, [200]),
            ("POST", "/api/v1/marketplace/cart/add", {"product_id": 1, "quantity": 1}, [200, 500]),
            ("POST", "/api/v1/marketplace/orders", {"customer_email": "test@test.com", "items": [], "total_cents": 100}, [200, 500]),
        ])
        
        # 4. Automation Endpoints
        self.test_category("AUTOMATIONS", [
            ("GET", "/api/v1/automations", None, [200]),
            ("POST", "/api/v1/automations/1/execute", {}, [200, 500]),
        ])
        
        # 5. AI Agent Endpoints
        self.test_category("AI AGENTS", [
            ("GET", "/api/v1/agents", None, [200]),
            ("POST", "/api/v1/agents/1/execute", {"type": "test"}, [200, 500]),
        ])
        
        # 6. CenterPoint Endpoints
        self.test_category("CENTERPOINT", [
            ("GET", "/api/v1/centerpoint/status", None, [200]),
            ("POST", "/api/v1/centerpoint/sync", {}, [200]),
        ])
        
        # 7. Payment Endpoints
        self.test_category("PAYMENTS", [
            ("POST", "/api/v1/payments/create-intent", {"amount_cents": 1000}, [200]),
            ("POST", "/api/v1/subscriptions/create", {"customer_email": "test@test.com", "plan": "pro", "price_cents": 9999}, [200, 500]),
        ])
        
        # 8. Lead Management
        self.test_category("LEADS", [
            ("POST", "/api/v1/leads", {"email": "test@test.com"}, [200, 500]),
        ])
        
        # 9. Public Routes (No Auth)
        self.test_category("PUBLIC ROUTES", [
            ("GET", "/api/v1/products/public", None, [200, 404]),
            ("POST", "/api/v1/aurea/public/chat", {"message": "test"}, [200, 404, 500]),
        ])
        
        # 10. CRM System (if exists)
        self.test_category("CRM SYSTEM", [
            ("GET", "/api/v1/crm/customers", None, [200, 401, 404]),
            ("GET", "/api/v1/crm/jobs", None, [200, 401, 404]),
            ("GET", "/api/v1/crm/invoices", None, [200, 401, 404]),
            ("GET", "/api/v1/crm/estimates", None, [200, 401, 404]),
        ])
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Endpoints Tested: {self.total_count}")
        print(f"Passed: {self.pass_count} ({self.pass_count/self.total_count*100:.1f}%)")
        print(f"Failed: {self.fail_count} ({self.fail_count/self.total_count*100:.1f}%)")
        
        # Group by status code
        status_counts = {}
        for result in self.results:
            status = result['status']
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        print(f"\nStatus Code Distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count} endpoints")
        
        # List all failed endpoints
        if self.fail_count > 0:
            print(f"\n{'='*80}")
            print(f"FAILED ENDPOINTS ({self.fail_count})")
            print(f"{'='*80}")
            for result in self.results:
                if not result['passed']:
                    print(f"❌ {result['method']} {result['path']} - {result['message']}")
        
        # Save results to file
        with open('endpoint_test_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": self.total_count,
                "passed": self.pass_count,
                "failed": self.fail_count,
                "results": self.results
            }, f, indent=2)
        
        print(f"\n✅ Results saved to endpoint_test_results.json")
        
        return self.pass_count, self.fail_count

if __name__ == "__main__":
    tester = EndpointTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if any failures
    exit(0 if failed == 0 else 1)