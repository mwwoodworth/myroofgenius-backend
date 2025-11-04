#!/usr/bin/env python3
"""
THOROUGH BACKEND TEST SUITE
Tests all backend endpoints comprehensively
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"

class BackendTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.endpoints_tested = []
        
    def test_endpoint(self, method: str, path: str, expected_status: List[int] = [200], 
                      json_data: Dict = None, check_keys: List[str] = None) -> bool:
        """Test a single endpoint"""
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=json_data or {}, timeout=10)
            else:
                response = requests.request(method, url, json=json_data, timeout=10)
            
            # Check status code
            if response.status_code not in expected_status:
                print(f"{Fore.RED}❌ {method} {path} - Status: {response.status_code} (expected {expected_status})")
                print(f"   Response: {response.text[:200]}")
                self.failed += 1
                return False
            
            # Check response keys if specified
            if check_keys and response.status_code == 200:
                try:
                    data = response.json()
                    missing_keys = [k for k in check_keys if k not in data]
                    if missing_keys:
                        print(f"{Fore.YELLOW}⚠️  {method} {path} - Missing keys: {missing_keys}")
                        self.failed += 1
                        return False
                except:
                    print(f"{Fore.YELLOW}⚠️  {method} {path} - Invalid JSON response")
                    self.failed += 1
                    return False
            
            print(f"{Fore.GREEN}✅ {method} {path} - Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Print key info
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        print(f"   Keys: {keys}")
                        # Print specific values for important endpoints
                        if "version" in data:
                            print(f"   Version: {data['version']}")
                        if "status" in data:
                            print(f"   Status: {data['status']}")
                        if "metrics" in data and isinstance(data["metrics"], dict):
                            print(f"   Metrics: {list(data['metrics'].keys())}")
                except:
                    pass
            
            self.passed += 1
            self.endpoints_tested.append(path)
            return True
            
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ {method} {path} - TIMEOUT")
            self.failed += 1
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ {method} {path} - ERROR: {str(e)}")
            self.failed += 1
            return False
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}TEST SUMMARY")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Passed: {self.passed}")
        print(f"{Fore.RED}Failed: {self.failed}")
        print(f"{Fore.CYAN}Total: {total}")
        print(f"{Fore.CYAN}Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"\n{Fore.GREEN}🎉 BACKEND STATUS: EXCELLENT")
        elif success_rate >= 70:
            print(f"\n{Fore.YELLOW}⚠️  BACKEND STATUS: GOOD (Some issues)")
        else:
            print(f"\n{Fore.RED}❌ BACKEND STATUS: POOR (Multiple failures)")
        
        return success_rate

def main():
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}THOROUGH BACKEND TEST SUITE")
    print(f"{Fore.MAGENTA}Testing: {BASE_URL}")
    print(f"{Fore.MAGENTA}Time: {datetime.now().isoformat()}")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    tester = BackendTester()
    
    # Core Health Endpoints
    print(f"{Fore.CYAN}=== CORE HEALTH ENDPOINTS ===")
    tester.test_endpoint("GET", "/health", check_keys=["status", "version"])
    tester.test_endpoint("GET", "/api/v1/health", check_keys=["status", "version"])
    
    # AI System Endpoints
    print(f"\n{Fore.CYAN}=== AI SYSTEM ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/ai/status", check_keys=["status"])
    tester.test_endpoint("GET", "/api/v1/ai/revenue/analysis", check_keys=["analysis"])
    tester.test_endpoint("GET", "/api/v1/ai/system/health", check_keys=["health"])
    tester.test_endpoint("GET", "/api/v1/ai/patterns")
    
    # Test AI Command
    command_data = {
        "command": "Test command from thorough test suite",
        "context": {"test": True, "timestamp": datetime.now().isoformat()},
        "priority": 5
    }
    tester.test_endpoint("POST", "/api/v1/ai/command", json_data=command_data)
    
    # Test Self-Healing
    tester.test_endpoint("POST", "/api/v1/ai/system/heal")
    
    # AUREA Endpoints
    print(f"\n{Fore.CYAN}=== AUREA AI ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/aurea/status", check_keys=["status"])
    tester.test_endpoint("GET", "/api/v1/aurea/health", check_keys=["healthy"])
    tester.test_endpoint("POST", "/api/v1/aurea/command", json_data={"command": "test"})
    
    # Task OS Endpoints
    print(f"\n{Fore.CYAN}=== TASK OS ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/task-os/status")
    tester.test_endpoint("GET", "/api/v1/task-os/tasks")
    tester.test_endpoint("GET", "/api/v1/task-os/metrics")
    
    # Blog Endpoints
    print(f"\n{Fore.CYAN}=== BLOG ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/blog/posts", check_keys=["posts"])
    tester.test_endpoint("GET", "/api/v1/blog/stats")
    
    # Analytics Endpoints
    print(f"\n{Fore.CYAN}=== ANALYTICS ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/analytics/dashboard")
    tester.test_endpoint("GET", "/api/v1/analytics/metrics")
    
    # Products Endpoints
    print(f"\n{Fore.CYAN}=== PRODUCTS ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/products")
    tester.test_endpoint("GET", "/api/v1/products/categories")
    
    # Authentication Endpoints (expect 422 without proper data)
    print(f"\n{Fore.CYAN}=== AUTH ENDPOINTS ===")
    tester.test_endpoint("POST", "/api/v1/auth/login", expected_status=[422, 401])
    tester.test_endpoint("POST", "/api/v1/auth/register", expected_status=[422, 400])
    tester.test_endpoint("POST", "/api/v1/auth/refresh", expected_status=[422, 401])
    
    # Revenue Endpoints
    print(f"\n{Fore.CYAN}=== REVENUE ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/revenue/status")
    tester.test_endpoint("GET", "/api/v1/revenue/metrics")
    
    # Estimates Endpoints
    print(f"\n{Fore.CYAN}=== ESTIMATES ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/estimates/summary")
    tester.test_endpoint("GET", "/api/v1/estimates/recent")
    
    # Job Management Endpoints
    print(f"\n{Fore.CYAN}=== JOB MANAGEMENT ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/jobs/summary")
    tester.test_endpoint("GET", "/api/v1/jobs/active")
    
    # AI Chat Endpoints
    print(f"\n{Fore.CYAN}=== AI CHAT ENDPOINTS ===")
    tester.test_endpoint("GET", "/api/v1/ai-chat/models")
    tester.test_endpoint("POST", "/api/v1/ai-chat/message", 
                        json_data={"message": "test", "model": "claude"}, 
                        expected_status=[200, 422])
    
    # Check for WebSocket support
    print(f"\n{Fore.CYAN}=== WEBSOCKET ENDPOINTS ===")
    print(f"{Fore.YELLOW}⚠️  WebSocket endpoints require special client (not tested via HTTP)")
    
    # Print summary
    success_rate = tester.print_summary()
    
    # List working endpoints
    if tester.endpoints_tested:
        print(f"\n{Fore.GREEN}WORKING ENDPOINTS:")
        for endpoint in tester.endpoints_tested[:10]:
            print(f"  • {endpoint}")
        if len(tester.endpoints_tested) > 10:
            print(f"  ... and {len(tester.endpoints_tested) - 10} more")
    
    return success_rate >= 70

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted")
        exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test failed: {e}")
        exit(1)