#!/usr/bin/env python3
"""
Test MyRoofGenius with CORRECT route paths
Based on actual routes loaded in the system
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("MYROOFGENIUS TEST WITH CORRECT ROUTES")
print("=" * 80)
print()

BASE_URL = "https://brainops-backend-prod.onrender.com"

# Test credentials
TEST_EMAIL = "test@brainops.com"
TEST_PASSWORD = "TestPassword123!"
ADMIN_EMAIL = "admin@brainops.com"
ADMIN_PASSWORD = "AdminPassword123!"

def test_endpoint(method, path, headers=None, json_data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        response = requests.request(method, url, headers=headers, json=json_data, timeout=10)
        success = response.status_code == expected_status
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {path}: {response.status_code}")
        
        if not success and response.text:
            print(f"   Response: {response.text[:100]}")
        
        return {
            "success": success,
            "status": response.status_code,
            "data": response.json() if response.text else {}
        }
    except Exception as e:
        print(f"❌ {method} {path}: ERROR - {str(e)}")
        return {"success": False, "error": str(e)}

# Get auth token
print("1. AUTHENTICATION")
print("-" * 40)
result = test_endpoint("POST", "/api/v1/auth/login", json_data={"email": TEST_EMAIL, "password": TEST_PASSWORD})
if result["success"] and "access_token" in result["data"]:
    user_token = result["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("✅ Authentication successful")
else:
    print("❌ Authentication failed")
    user_headers = {}

print("\n2. CORRECTED ROOFING ROUTES")
print("-" * 40)

# Test with correct roofing routes
roofing_tests = [
    ("GET", "/api/v1/roofing/estimates", None),
    ("POST", "/api/v1/roofing/estimates/create", {
        "project_type": "residential",
        "roof_type": "shingle",
        "square_footage": 2000
    }),
    ("POST", "/api/v1/roofing/photos/analyze", {
        "image_url": "https://example.com/roof.jpg"
    }),
    ("POST", "/api/v1/roofing/materials/calculate", {
        "square_footage": 2000,
        "roof_type": "shingle"
    }),
    ("GET", "/api/v1/roofing/customers", None),
    ("GET", "/api/v1/roofing/dashboard/metrics", None)
]

for method, path, data in roofing_tests:
    test_endpoint(method, path, user_headers, data)

print("\n3. CORRECTED AI SERVICES ROUTES")
print("-" * 40)

ai_tests = [
    ("POST", "/api/v1/ai-services/claude/chat", {
        "message": "Generate a roofing estimate template"
    }),
    ("POST", "/api/v1/ai-services/gemini/chat", {
        "message": "Analyze roofing market trends"
    }),
    ("GET", "/api/v1/ai-services/health", None),
    ("GET", "/api/v1/ai-services/models", None),
    ("GET", "/api/v1/ai-services", None)
]

for method, path, data in ai_tests:
    test_endpoint(method, path, user_headers, data)

print("\n4. CLAUDE SUB-AGENTS (CORRECT PARAMS)")
print("-" * 40)

# Test with both 'message' and 'task' fields as the v3.1.103 fix implemented
agent_tests = [
    ("POST", "/api/v1/claude-agents/execute", {
        "task_type": "seo_audit",
        "task_data": {"url": "https://myroofgenius.com"},
        "message": "Perform SEO audit"  # Added based on v3.1.103 fix
    }),
    ("POST", "/api/v1/claude-agents/seo/audit", {
        "url": "https://myroofgenius.com",
        "keywords": ["roofing", "contractor"],
        "message": "Audit this site"  # Added field
    }),
    ("POST", "/api/v1/claude-agents/product/create", {
        "name": "Premium Roof Inspection",
        "category": "services",
        "description": "Comprehensive inspection",
        "features": ["Drone", "Report"],
        "target_price": 299.99,
        "message": "Create this product"  # Added field
    })
]

for method, path, data in agent_tests:
    test_endpoint(method, path, user_headers, data)

print("\n5. ADMIN ROUTES (ACTUAL PATHS)")
print("-" * 40)

admin_tests = [
    ("GET", "/api/v1/admin/health", None),
    ("GET", "/api/v1/admin/health/public", None),
    ("GET", "/api/v1/admin/system-status", None),
    ("GET", "/api/v1/admin/system-status/public", None)
]

for method, path, data in admin_tests:
    test_endpoint(method, path, user_headers, data)

print("\n6. AUTOMATION ROUTES")
print("-" * 40)

automation_tests = [
    ("GET", "/api/v1/automations", None),
    ("GET", "/api/v1/automations/public", None),
    ("POST", "/api/v1/automations/execute", {
        "automation_type": "seo_analysis"
    })
]

for method, path, data in automation_tests:
    test_endpoint(method, path, user_headers, data)

# Summary
print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nThis test uses the ACTUAL routes that exist in the system.")
print("Many previous '404' errors were due to incorrect paths in the test.")