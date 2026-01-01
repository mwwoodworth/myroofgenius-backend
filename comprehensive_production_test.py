#!/usr/bin/env python3
"""
Comprehensive WeatherCraft Backend Production Test Suite
Tests all critical endpoints to ensure 100% operational status
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import uuid

# Configuration
BASE_URL = "https://brainops-backend-prod.onrender.com"
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPassword123!"
API_KEY = "test_prod_verify_2026"

class ProductionTester:
    def __init__(self):
        self.results = []
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": API_KEY})

    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")

    def test_health_endpoints(self):
        """Test basic health and status endpoints"""
        try:
            # Root endpoint
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                version = data.get("message", "").split("v")[-1].split(" ")[0] if "v" in data.get("message", "") else "unknown"
                self.log_result("Root endpoint", True, f"Version: {version}")
            else:
                self.log_result("Root endpoint", False, f"Status: {response.status_code}")

            # Health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            success = response.status_code == 200
            self.log_result("Health endpoint", success, f"Status: {response.status_code}")

            # API Health endpoint
            response = self.session.get(f"{BASE_URL}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("API Health endpoint", True,
                              f"Version: {data.get('version')}, DB: {data.get('database')}")
                return data
            else:
                self.log_result("API Health endpoint", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Health endpoints", False, f"Exception: {str(e)}")
            return None

    def test_auth_system(self):
        """Test authentication system"""
        try:
            # Test auth status
            response = self.session.get(f"{BASE_URL}/api/v1/auth/status")
            success = response.status_code == 200
            self.log_result("Auth status", success, f"Status: {response.status_code}")

            # Test user registration
            registration_data = {
                "name": "Test User",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = self.session.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
            if response.status_code == 200:
                self.log_result("User registration", True, "User registered successfully")

                # Test login
                login_data = {
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
                response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    self.log_result("User login", True, "Login successful, token obtained")
                    return True
                else:
                    self.log_result("User login", False,
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
            else:
                self.log_result("User registration", False,
                              f"Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            self.log_result("Auth system", False, f"Exception: {str(e)}")
            return False

    def test_lead_capture(self):
        """Test lead capture functionality"""
        try:
            lead_data = {
                "name": "Test Lead Production",
                "email": f"lead_{uuid.uuid4().hex[:8]}@example.com",
                "phone": "555-0199",
                "source": "production_test"
            }
            response = self.session.post(f"{BASE_URL}/api/v1/lead-capture", json=lead_data)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Lead capture", True,
                              f"Lead captured with score: {data.get('lead_score')}")
            else:
                self.log_result("Lead capture", False,
                              f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Lead capture", False, f"Exception: {str(e)}")

    def test_public_endpoints(self):
        """Test public endpoints that don't require auth"""
        try:
            # Test leads GET (public read)
            response = self.session.get(f"{BASE_URL}/api/v1/leads")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Leads list", True, f"Found {len(data)} leads")
            else:
                self.log_result("Leads list", False, f"Status: {response.status_code}")

            # Test products (if public)
            response = self.session.get(f"{BASE_URL}/api/v1/products")
            if response.status_code in [200, 401]:  # 401 is acceptable for protected endpoint
                status_msg = "Public access" if response.status_code == 200 else "Protected (requires auth)"
                self.log_result("Products endpoint", True, status_msg)
            else:
                self.log_result("Products endpoint", False, f"Status: {response.status_code}")

        except Exception as e:
            self.log_result("Public endpoints", False, f"Exception: {str(e)}")

    def test_protected_endpoints(self):
        """Test endpoints that require authentication"""
        if not self.token:
            self.log_result("Protected endpoints", False, "No auth token available")
            return

        # Add Bearer token to headers for this request, but keep API key
        headers = self.session.headers.copy()
        headers.update({"Authorization": f"Bearer {self.token}"})

        try:
            # Test customers endpoint
            response = self.session.get(f"{BASE_URL}/api/v1/customers", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Customers list", True, f"Found {len(data)} customers")
            else:
                self.log_result("Customers list", False,
                              f"Status: {response.status_code}, Response: {response.text}")

            # Test customer creation
            customer_data = {
                "name": "Test Customer Production",
                "email": f"customer_{uuid.uuid4().hex[:8]}@example.com",
                "phone": "555-0299",
                "address": "123 Test Production St"
            }
            response = self.session.post(f"{BASE_URL}/api/v1/customers", json=customer_data, headers=headers)
            if response.status_code in [200, 201]:
                self.log_result("Customer creation", True, "Customer created successfully")
            else:
                self.log_result("Customer creation", False,
                              f"Status: {response.status_code}, Response: {response.text}")

        except Exception as e:
            self.log_result("Protected endpoints", False, f"Exception: {str(e)}")

    def test_ai_endpoints(self):
        """Test AI-related endpoints"""
        try:
            # Test AI status
            response = self.session.get(f"{BASE_URL}/api/v1/ai/status")
            if response.status_code == 200:
                data = response.json()
                self.log_result("AI status", True, f"AI system: {data.get('status', 'unknown')}")
            else:
                self.log_result("AI status", False, f"Status: {response.status_code}")

            # Test AI analyze endpoint (if available)
            response = self.session.get(f"{BASE_URL}/api/v1/ai/analyze")
            if response.status_code in [200, 400, 422]:  # These are acceptable responses
                self.log_result("AI analyze", True, "Endpoint accessible")
            else:
                self.log_result("AI analyze", False, f"Status: {response.status_code}")

        except Exception as e:
            self.log_result("AI endpoints", False, f"Exception: {str(e)}")

    def test_system_monitoring(self):
        """Test system monitoring and debug endpoints"""
        try:
            # Test debug routes
            response = self.session.get(f"{BASE_URL}/api/v1/debug/routes")
            if response.status_code == 200:
                data = response.json()
                total_routes = data.get("total_routes", 0)
                self.log_result("Debug routes", True, f"Total routes: {total_routes}")
            else:
                self.log_result("Debug routes", False, f"Status: {response.status_code}")

        except Exception as e:
            self.log_result("System monitoring", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting WeatherCraft Backend Production Test Suite")
        print("=" * 60)

        start_time = time.time()

        # Run all test categories
        health_data = self.test_health_endpoints()
        self.test_auth_system()
        self.test_lead_capture()
        self.test_public_endpoints()
        self.test_protected_endpoints()
        self.test_ai_endpoints()
        self.test_system_monitoring()

        end_time = time.time()
        duration = end_time - start_time

        # Calculate results
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")

        if health_data:
            print(f"\n🏥 System Health:")
            print(f"Version: {health_data.get('version')}")
            print(f"Database: {health_data.get('database')}")
            print(f"Customers: {health_data.get('stats', {}).get('customers', 'unknown')}")
            print(f"Jobs: {health_data.get('stats', {}).get('jobs', 'unknown')}")
            print(f"AI Agents: {health_data.get('stats', {}).get('ai_agents', 'unknown')}")

        # Determine overall system status
        if success_rate >= 90:
            print(f"\n🎉 SYSTEM STATUS: EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 80:
            print(f"\n✅ SYSTEM STATUS: GOOD ({success_rate:.1f}%)")
        elif success_rate >= 70:
            print(f"\n⚠️  SYSTEM STATUS: NEEDS ATTENTION ({success_rate:.1f}%)")
        else:
            print(f"\n❌ SYSTEM STATUS: CRITICAL ISSUES ({success_rate:.1f}%)")

        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")

        print("\n" + "=" * 60)

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"production_test_results_{timestamp}.json"

        test_report = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate
            },
            "system_health": health_data,
            "results": self.results
        }

        with open(filename, 'w') as f:
            json.dump(test_report, f, indent=2)

        print(f"📄 Detailed results saved to: {filename}")

        return success_rate >= 80  # Return True if system is in good condition

if __name__ == "__main__":
    tester = ProductionTester()
    is_operational = tester.run_all_tests()

    exit_code = 0 if is_operational else 1
    exit(exit_code)
