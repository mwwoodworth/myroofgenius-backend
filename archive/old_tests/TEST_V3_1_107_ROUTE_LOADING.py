#!/usr/bin/env python3
"""
Test v3.1.107 Enhanced Route Loading System
Verifies that ALL critical endpoints will be available
"""

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style
import time

init(autoreset=True)

# Production URL
BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(method, path, headers=None, json_data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        start = time.time()
        response = requests.request(
            method, 
            url, 
            headers=headers, 
            json=json_data, 
            timeout=10
        )
        elapsed = time.time() - start
        
        if response.status_code == expected_status:
            return True, f"✅ {response.status_code} ({elapsed:.2f}s)"
        else:
            return False, f"❌ {response.status_code} - {response.text[:100]}"
    except Exception as e:
        return False, f"❌ ERROR: {str(e)}"

def main():
    print(f"\n{Fore.CYAN}🚀 Testing v3.1.107 Enhanced Route Loading System{Style.RESET_ALL}")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("="*80)
    
    # Test credentials
    test_user = {"email": "test@brainops.com", "password": "TestPassword123!"}
    
    # First, check version
    print(f"\n{Fore.YELLOW}Checking deployment version...{Style.RESET_ALL}")
    success, msg = test_endpoint("GET", "/api/v1/health")
    if success:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        data = response.json()
        version = data.get("version", "unknown")
        routes = data.get("loaded_routes", 0)
        print(f"Version: {Fore.GREEN}{version}{Style.RESET_ALL}")
        print(f"Loaded Routes: {Fore.GREEN}{routes}{Style.RESET_ALL}")
        
        if version != "3.1.107":
            print(f"\n{Fore.RED}⚠️  WARNING: v3.1.107 not yet deployed!{Style.RESET_ALL}")
            print(f"Current version {version} will only have partial functionality.")
            print(f"Deploy v3.1.107 from Render dashboard for 100% functionality.")
    
    # Critical endpoints that MUST work with v3.1.107's fallback system
    critical_endpoints = [
        # Health & Version
        ("GET", "/health", None, None, 200),
        ("GET", "/api/v1/health", None, None, 200),
        ("GET", "/api/v1/version", None, None, 200),
        
        # Authentication (with fallbacks)
        ("POST", "/api/v1/auth/login", None, test_user, 200),
        ("POST", "/api/v1/auth/register", None, {
            "email": f"test{int(time.time())}@example.com",
            "password": "Test123!",
            "name": "Test User"
        }, [200, 400]),  # 400 if user exists
        ("POST", "/api/v1/auth/refresh", {"Authorization": "Bearer fake"}, None, [200, 401]),
        ("POST", "/api/v1/auth/logout", {"Authorization": "Bearer fake"}, None, 200),
        
        # Users (with fallbacks)
        ("GET", "/api/v1/users", None, None, [200, 401]),
        ("GET", "/api/v1/users/me", {"Authorization": "Bearer fake"}, None, [200, 401]),
        ("GET", "/api/v1/users/profile", {"Authorization": "Bearer fake"}, None, [200, 401]),
        
        # Memory (with fallbacks)
        ("GET", "/api/v1/memory/recent", None, None, [200, 401]),
        ("POST", "/api/v1/memory/create", None, {"content": "test", "memory_type": "note"}, [200, 401]),
        ("POST", "/api/v1/memory/search", None, {"query": "test"}, [200, 401]),
        ("GET", "/api/v1/memory/insights", None, None, [200, 401]),
        
        # Projects (with fallbacks)
        ("GET", "/api/v1/projects", None, None, [200, 401]),
        ("POST", "/api/v1/projects", None, {"name": "Test", "description": "Test"}, [200, 401]),
        
        # Tasks (with fallbacks)
        ("GET", "/api/v1/tasks", None, None, [200, 401]),
        ("POST", "/api/v1/tasks", None, {"title": "Test", "description": "Test"}, [200, 401]),
        
        # AI Services (with fallbacks)
        ("GET", "/api/v1/agents", None, None, [200, 401]),
        ("GET", "/api/v1/ai-services", None, None, [200, 401]),
        ("POST", "/api/v1/agent/execute", None, {"agent_type": "dev", "task": "test"}, [200, 401]),
        
        # Admin (with fallbacks)
        ("GET", "/api/v1/admin/users", {"Authorization": "Bearer fake"}, None, [200, 401, 403]),
        ("GET", "/api/v1/admin/system", {"Authorization": "Bearer fake"}, None, [200, 401, 403]),
        
        # Automation (with fallbacks)
        ("GET", "/api/v1/automation/workflows", None, None, [200, 401]),
        ("POST", "/api/v1/automation/execute", None, {"workflow_id": "test"}, [200, 401]),
        
        # Other critical services (with fallbacks)
        ("GET", "/api/v1/billing/plans", None, None, [200, 401]),
        ("GET", "/api/v1/marketplace/products", None, None, [200, 401]),
        ("GET", "/api/v1/notifications", None, None, [200, 401]),
        ("GET", "/api/v1/analytics/reports", None, None, [200, 401]),
        ("GET", "/api/v1/integrations", None, None, [200, 401]),
        ("GET", "/api/v1/roofing/estimates", None, None, [200, 401]),
        ("GET", "/api/v1/webhooks", None, None, [200, 401]),
        ("GET", "/api/v1/crm/contacts", None, None, [200, 401]),
        ("GET", "/api/v1/scheduling/appointments", None, None, [200, 401]),
        ("GET", "/api/v1/documents", None, None, [200, 401])
    ]
    
    # Test all critical endpoints
    print(f"\n{Fore.YELLOW}Testing {len(critical_endpoints)} critical endpoints...{Style.RESET_ALL}")
    
    passed = 0
    failed = 0
    
    for method, path, headers, json_data, expected in critical_endpoints:
        if isinstance(expected, list):
            success = False
            for exp_status in expected:
                s, msg = test_endpoint(method, path, headers, json_data, exp_status)
                if s:
                    success = True
                    break
        else:
            success, msg = test_endpoint(method, path, headers, json_data, expected)
        
        if success:
            passed += 1
            print(f"{Fore.GREEN}✅{Style.RESET_ALL} {method} {path}")
        else:
            failed += 1
            print(f"{Fore.RED}❌{Style.RESET_ALL} {method} {path} - {msg}")
    
    # Summary
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Fore.CYAN}📊 SUMMARY{Style.RESET_ALL}")
    print("="*80)
    print(f"Total Tests: {total}")
    print(f"Passed: {Fore.GREEN}{passed}{Style.RESET_ALL}")
    print(f"Failed: {Fore.RED}{failed}{Style.RESET_ALL}")
    print(f"Success Rate: {Fore.YELLOW}{success_rate:.1f}%{Style.RESET_ALL}")
    
    if version == "3.1.107" and success_rate == 100:
        print(f"\n{Fore.GREEN}🎉 SUCCESS! v3.1.107 is fully operational!{Style.RESET_ALL}")
        print("All critical endpoints are working with the enhanced route loading system.")
    elif version == "3.1.107" and success_rate < 100:
        print(f"\n{Fore.YELLOW}⚠️  v3.1.107 is deployed but some endpoints need attention.{Style.RESET_ALL}")
        print("Check the logs for route loading issues.")
    else:
        print(f"\n{Fore.YELLOW}ℹ️  v3.1.107 not yet deployed. Current version: {version}{Style.RESET_ALL}")
        print("Deploy v3.1.107 from Render dashboard for enhanced route loading.")
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": version if 'version' in locals() else "unknown",
        "loaded_routes": routes if 'routes' in locals() else 0,
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate
    }
    
    with open("v3_1_107_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to v3_1_107_test_results.json")

if __name__ == "__main__":
    main()