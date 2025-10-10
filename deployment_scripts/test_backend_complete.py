#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

# Backend API URL
base_url = "https://brainops-backend-prod.onrender.com"

# Test credentials
test_accounts = [
    {"email": "admin@brainops.com", "password": "AdminPassword123!"},
    {"email": "test@brainops.com", "password": "TestPassword123!"},
    {"email": "demo@myroofgenius.com", "password": "DemoPassword123!"}
]

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def test_endpoint(method, endpoint, headers=None, data=None, auth_token=None):
    """Test a single endpoint and return results"""
    url = f"{base_url}{endpoint}"
    if auth_token:
        headers = headers or {}
        headers['Authorization'] = f'Bearer {auth_token}'
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        else:
            return None, "Unsupported method"
        
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return None, str(e)

def main():
    print_section("BRAINOPS BACKEND COMPLETE TEST SUITE")
    print(f"Testing against: {base_url}")
    print(f"Started at: {datetime.now()}")
    
    # 1. Health Check
    print_section("1. HEALTH & VERSION CHECK")
    status, data = test_endpoint("GET", "/api/v1/health")
    if status == 200:
        print(f"✅ API is healthy!")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Routes loaded: {data.get('routes_loaded', 0)}")
        print(f"   Total endpoints: {data.get('total_endpoints', 0)}")
    else:
        print(f"❌ Health check failed: {status} - {data}")
        return
    
    # 2. Authentication Test
    print_section("2. AUTHENTICATION TEST")
    auth_token = None
    for account in test_accounts:
        status, data = test_endpoint("POST", "/api/v1/auth/login", data=account)
        if status == 200:
            print(f"✅ Login successful: {account['email']}")
            auth_token = data.get('access_token')
            break
        else:
            print(f"❌ Login failed for {account['email']}: {status}")
    
    if not auth_token:
        print("❌ No successful login - cannot continue with authenticated tests")
        return
    
    # 3. Core APIs Test
    print_section("3. CORE API ENDPOINTS")
    core_endpoints = [
        ("GET", "/api/v1/users/me"),
        ("GET", "/api/v1/memory/recent"),
        ("GET", "/api/v1/memory/insights"),
        ("GET", "/api/v1/tasks"),
        ("GET", "/api/v1/projects"),
        ("GET", "/api/v1/ai-services/status"),
        ("GET", "/api/v1/automations"),
        ("GET", "/api/v1/notifications")
    ]
    
    for method, endpoint in core_endpoints:
        status, data = test_endpoint(method, endpoint, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # 4. Automation System Test
    print_section("4. AUTOMATION SYSTEM")
    automation_endpoints = [
        ("GET", "/api/v1/automations/types"),
        ("GET", "/api/v1/automations/status"),
        ("GET", "/api/v1/automations/history"),
        ("POST", "/api/v1/automations/execute", {
            "automation_type": "daily_seo_analysis",
            "parameters": {"test": True}
        })
    ]
    
    for method, endpoint, *args in automation_endpoints:
        data = args[0] if args else None
        status, response = test_endpoint(method, endpoint, data=data, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201, 202] else '❌'}")
    
    # 5. AI Services Test
    print_section("5. AI SERVICES")
    ai_endpoints = [
        ("POST", "/api/v1/ai-services/claude/chat", {
            "messages": [{"role": "user", "content": "Hello, test message"}]
        }),
        ("POST", "/api/v1/ai-services/gemini/generate", {
            "prompt": "Test prompt"
        }),
        ("GET", "/api/v1/ai-services/status")
    ]
    
    for method, endpoint, *args in ai_endpoints:
        data = args[0] if args else None
        status, response = test_endpoint(method, endpoint, data=data, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # 6. AUREA System Test
    print_section("6. AUREA EXECUTIVE AI")
    aurea_endpoints = [
        ("GET", "/api/v1/aurea/status"),
        ("POST", "/api/v1/aurea/chat", {
            "message": "Test AUREA connection"
        }),
        ("GET", "/api/v1/aurea/health"),
        ("GET", "/api/v1/aurea/capabilities")
    ]
    
    for method, endpoint, *args in aurea_endpoints:
        data = args[0] if args else None
        status, response = test_endpoint(method, endpoint, data=data, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # 7. Memory System Test
    print_section("7. MEMORY SYSTEM")
    memory_test = {
        "memory_type": "test",
        "content": f"Test memory entry created at {datetime.now()}",
        "metadata": {
            "test": True,
            "source": "backend_complete_test"
        }
    }
    
    # Create memory
    status, response = test_endpoint("POST", "/api/v1/memory/create", data=memory_test, auth_token=auth_token)
    print(f"Create memory: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # Search memory
    search_data = {"query": "test memory", "limit": 5}
    status, response = test_endpoint("POST", "/api/v1/memory/search", data=search_data, auth_token=auth_token)
    print(f"Search memory: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # 8. Integration Tests
    print_section("8. INTEGRATIONS")
    integration_endpoints = [
        ("GET", "/api/v1/integrations/github/status"),
        ("GET", "/api/v1/integrations/slack/status"),
        ("GET", "/api/v1/integrations/stripe/status"),
        ("GET", "/api/v1/integrations/clickup/status")
    ]
    
    for method, endpoint in integration_endpoints:
        status, response = test_endpoint(method, endpoint, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # 9. Roofing-Specific Features
    print_section("9. ROOFING FEATURES")
    roofing_endpoints = [
        ("POST", "/api/v1/roofing/estimate", {
            "square_feet": 2000,
            "roof_type": "shingle",
            "complexity": "medium"
        }),
        ("POST", "/api/v1/roofing/materials/calculate", {
            "area": 2000,
            "material_type": "asphalt_shingle"
        }),
        ("GET", "/api/v1/roofing/projects")
    ]
    
    for method, endpoint, *args in roofing_endpoints:
        data = args[0] if args else None
        status, response = test_endpoint(method, endpoint, data=data, auth_token=auth_token)
        print(f"{endpoint}: {status} {'✅' if status in [200, 201] else '❌'}")
    
    # Summary
    print_section("TEST COMPLETE")
    print(f"Completed at: {datetime.now()}")
    print("\n✅ Backend API test suite complete!")

if __name__ == "__main__":
    main()