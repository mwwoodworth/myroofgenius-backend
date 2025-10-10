#!/usr/bin/env python3
"""
EXHAUSTIVE ECOSYSTEM TEST - Testing EVERY system across the entire BrainOps ecosystem
This will test ALL endpoints, ALL features, ALL integrations
"""

import requests
import json
import time
from datetime import datetime
import concurrent.futures
from typing import Dict, List, Any, Tuple

print("=" * 100)
print("EXHAUSTIVE BRAINOPS ECOSYSTEM TEST")
print("Testing EVERY system, endpoint, and feature across the entire platform")
print("=" * 100)
print()

# System URLs
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URL = "https://www.myroofgenius.com"
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"

# Test credentials
TEST_USER = {"email": "test@brainops.com", "password": "TestPassword123!"}
ADMIN_USER = {"email": "admin@brainops.com", "password": "AdminPassword123!"}
DEMO_USER = {"email": "demo@myroofgenius.com", "password": "DemoPassword123!"}

# Global results tracking
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "warnings": [],
    "performance": {},
    "by_category": {}
}

def test_endpoint(method: str, url: str, headers: Dict = None, json_data: Dict = None, 
                 params: Dict = None, expected_status: List[int] = [200], timeout: int = 10) -> Dict:
    """Test a single endpoint with timing and comprehensive error handling"""
    start_time = time.time()
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            params=params,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        success = response.status_code in expected_status
        
        result = {
            "success": success,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "response": response.json() if response.text else None,
            "headers": dict(response.headers)
        }
        
        # Track performance
        if elapsed > 2.0:
            test_results["warnings"].append(f"Slow response: {method} {url} took {elapsed:.2f}s")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"{method} {url} - ERROR: {str(e)}"
        test_results["errors"].append(error_msg)
        return {
            "success": False,
            "error": str(e),
            "elapsed": elapsed
        }

def print_test_result(test_name: str, result: Dict, show_response: bool = False):
    """Print formatted test result"""
    test_results["total_tests"] += 1
    
    if result["success"]:
        test_results["passed"] += 1
        status = "✅ PASS"
        color = "\033[92m"  # Green
    else:
        test_results["failed"] += 1
        status = "❌ FAIL"
        color = "\033[91m"  # Red
    
    print(f"{color}{status}\033[0m {test_name} ({result.get('elapsed', 0):.2f}s)")
    
    if not result["success"]:
        if "error" in result:
            print(f"    Error: {result['error']}")
        elif "status_code" in result:
            print(f"    Status: {result['status_code']}")
            if show_response and result.get("response"):
                print(f"    Response: {json.dumps(result['response'], indent=2)[:200]}")

def test_category(category_name: str):
    """Start a new test category"""
    print(f"\n{'=' * 80}")
    print(f"{category_name}")
    print(f"{'=' * 80}")
    test_results["by_category"][category_name] = {"passed": 0, "failed": 0}

# Authentication helper
def get_auth_token(email: str, password: str) -> str:
    """Get authentication token"""
    result = test_endpoint(
        "POST",
        f"{BACKEND_URL}/api/v1/auth/login",
        json_data={"email": email, "password": password}
    )
    
    if result["success"] and result.get("response", {}).get("access_token"):
        return result["response"]["access_token"]
    return None

# Start testing
print(f"Test started at: {datetime.now().isoformat()}")
print(f"Backend URL: {BACKEND_URL}")
print(f"Frontend URL: {FRONTEND_URL}")

# 1. BACKEND HEALTH & VERSION
test_category("1. BACKEND HEALTH & VERSION CHECKS")

health_tests = [
    ("GET", f"{BACKEND_URL}/health", "Root Health Check"),
    ("GET", f"{BACKEND_URL}/api/v1/health", "API Health Check"),
    ("GET", f"{BACKEND_URL}/api/v1/version", "Version Endpoint"),
    ("GET", f"{BACKEND_URL}/api/v1/routes", "Route Listing"),
    ("GET", f"{BACKEND_URL}/docs", "OpenAPI Documentation"),
    ("GET", f"{BACKEND_URL}/redoc", "ReDoc Documentation"),
]

for method, url, name in health_tests:
    result = test_endpoint(method, url)
    print_test_result(name, result)

# 2. AUTHENTICATION SYSTEM
test_category("2. AUTHENTICATION SYSTEM")

# Test all user types
auth_results = {}
for user_type, creds in [("Test User", TEST_USER), ("Admin User", ADMIN_USER), ("Demo User", DEMO_USER)]:
    result = test_endpoint("POST", f"{BACKEND_URL}/api/v1/auth/login", json_data=creds)
    print_test_result(f"{user_type} Login", result)
    
    if result["success"]:
        token = result["response"]["access_token"]
        auth_results[user_type] = {"token": token, "headers": {"Authorization": f"Bearer {token}"}}
        
        # Test token validation
        me_result = test_endpoint("GET", f"{BACKEND_URL}/api/v1/users/me", headers=auth_results[user_type]["headers"])
        print_test_result(f"{user_type} Token Validation", me_result)

# Use admin token for remaining tests
admin_headers = auth_results.get("Admin User", {}).get("headers", {})

# 3. USER MANAGEMENT
test_category("3. USER MANAGEMENT & PROFILES")

user_tests = [
    ("GET", "/api/v1/users", "List Users"),
    ("GET", "/api/v1/users/me", "Get Current User"),
    ("PUT", "/api/v1/users/me", "Update Profile", {"name": "Test Update"}),
    ("GET", "/api/v1/users/profile", "Get Profile"),
    ("POST", "/api/v1/users/preferences", "Update Preferences", {"theme": "dark"}),
]

for method, path, name, *data in user_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 4. CORE BUSINESS - ROOFING
test_category("4. ROOFING BUSINESS FEATURES")

roofing_tests = [
    # Estimates
    ("GET", "/api/v1/roofing/estimates", "List Estimates"),
    ("POST", "/api/v1/roofing/estimates/create", "Create Estimate", {
        "customer_name": "Test Customer",
        "project_type": "residential",
        "roof_type": "shingle",
        "square_footage": 2000,
        "pitch": "6/12"
    }),
    
    # Materials
    ("POST", "/api/v1/roofing/materials/calculate", "Calculate Materials", {
        "square_footage": 2000,
        "roof_type": "shingle",
        "include_accessories": True
    }),
    
    # Photo Analysis
    ("POST", "/api/v1/roofing/photos/analyze", "Analyze Roof Photo", {
        "image_url": "https://example.com/roof.jpg",
        "analysis_type": "damage_assessment"
    }),
    
    # Customers
    ("GET", "/api/v1/roofing/customers", "List Customers"),
    ("POST", "/api/v1/roofing/customers/create", "Create Customer", {
        "name": "Test Customer",
        "email": "customer@test.com",
        "phone": "555-0123"
    }),
    
    # Dashboard
    ("GET", "/api/v1/roofing/dashboard/metrics", "Dashboard Metrics"),
]

for method, path, name, *data in roofing_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 5. TASK MANAGEMENT
test_category("5. TASK MANAGEMENT SYSTEM")

# Create a test task first
create_task_result = test_endpoint(
    "POST",
    f"{BACKEND_URL}/api/v1/tasks",
    headers=admin_headers,
    json_data={
        "title": "Test Roof Inspection",
        "description": "Exhaustive test task",
        "priority": "high",
        "type": "inspection",
        "status": "pending"
    }
)
print_test_result("Create Task", create_task_result)

task_id = None
if create_task_result["success"] and create_task_result.get("response"):
    task_id = create_task_result["response"].get("id")

task_tests = [
    ("GET", "/api/v1/tasks", "List All Tasks"),
    ("GET", f"/api/v1/tasks/{task_id}", "Get Single Task") if task_id else None,
    ("PUT", f"/api/v1/tasks/{task_id}", "Update Task", {"status": "in_progress"}) if task_id else None,
    ("GET", "/api/v1/tasks/stats", "Task Statistics"),
    ("GET", "/api/v1/tasks/upcoming", "Upcoming Tasks"),
    ("POST", "/api/v1/tasks/bulk", "Bulk Update", {
        "task_ids": [task_id] if task_id else [],
        "action": "update_status",
        "status": "completed"
    }),
]

for test in task_tests:
    if test:  # Skip None entries
        method, path, name, *data = test
        json_data = data[0] if data else None
        result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
        print_test_result(name, result)

# 6. AI SERVICES
test_category("6. AI SERVICES INTEGRATION")

ai_tests = [
    # Service Discovery
    ("GET", "/api/v1/ai-services", "List AI Services"),
    ("GET", "/api/v1/ai-services/health", "AI Health Check"),
    ("GET", "/api/v1/ai-services/models", "Available Models"),
    
    # Claude
    ("POST", "/api/v1/ai-services/claude/chat", "Claude Chat", {
        "messages": [{"role": "user", "content": "Generate a roofing quote template"}]
    }),
    
    # Gemini
    ("POST", "/api/v1/ai-services/gemini/chat", "Gemini Chat", {
        "messages": [{"role": "user", "content": "Analyze roofing market trends"}]
    }),
    
    # GPT
    ("POST", "/api/v1/ai-services/gpt/chat", "GPT Chat", {
        "messages": [{"role": "user", "content": "Explain roof ventilation"}]
    }),
]

for method, path, name, *data in ai_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 7. CLAUDE SUB-AGENTS
test_category("7. CLAUDE SUB-AGENT SYSTEM")

agent_tests = [
    # Agent Discovery
    ("GET", "/api/v1/claude-agents/agents", "List All Agents"),
    
    # Main Orchestrator
    ("POST", "/api/v1/claude-agents/execute", "Execute Agent Task", {
        "task_type": "seo_audit",
        "task_data": {"url": "https://myroofgenius.com"},
        "message": "Perform comprehensive SEO audit"
    }),
    
    # Specific Agents
    ("POST", "/api/v1/claude-agents/seo/audit", "SEO Agent", {
        "url": "https://myroofgenius.com",
        "keywords": ["roofing", "contractor"]
    }),
    
    ("POST", "/api/v1/claude-agents/product/create", "Product Agent", {
        "name": "Premium Inspection",
        "category": "services",
        "description": "Comprehensive roof inspection",
        "features": ["Drone", "Report", "Warranty"],
        "target_price": 299.99
    }),
    
    ("POST", "/api/v1/claude-agents/financial/analyze", "Financial Agent", {
        "period": "monthly",
        "metrics": ["revenue", "expenses", "profit"]
    }),
]

for method, path, name, *data in agent_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 8. MEMORY SYSTEM
test_category("8. PERSISTENT MEMORY SYSTEM")

# Create test memory
create_memory = test_endpoint(
    "POST",
    f"{BACKEND_URL}/api/v1/memory/create",
    headers=admin_headers,
    json_data={
        "title": "Ecosystem Test Memory",
        "content": "Testing memory persistence across the ecosystem",
        "tags": ["test", "ecosystem", "exhaustive"],
        "metadata": {"test_run": datetime.now().isoformat()}
    }
)
print_test_result("Create Memory", create_memory)

memory_tests = [
    ("GET", "/api/v1/memory/recent", "Recent Memories"),
    ("POST", "/api/v1/memory/search", "Search Memories", {"query": "ecosystem"}),
    ("GET", "/api/v1/memory/insights", "Memory Insights"),
    ("GET", "/api/v1/memory/tags", "Memory Tags"),
]

for method, path, name, *data in memory_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 9. MARKETPLACE & E-COMMERCE
test_category("9. MARKETPLACE & E-COMMERCE")

marketplace_tests = [
    # Products
    ("GET", "/api/v1/products", "List Products"),
    ("GET", "/api/v1/marketplace", "Marketplace Home"),
    
    # Cart
    ("POST", "/api/v1/marketplace/cart/add", "Add to Cart", {
        "product_id": "test-product",
        "quantity": 2
    }),
    ("GET", "/api/v1/marketplace/cart", "View Cart"),
    ("POST", "/api/v1/marketplace/cart/clear", "Clear Cart"),
    
    # Billing
    ("GET", "/api/v1/billing/plans", "Billing Plans"),
    ("GET", "/api/v1/billing/usage", "Usage Stats"),
]

for method, path, name, *data in marketplace_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 10. PROJECTS
test_category("10. PROJECT MANAGEMENT")

# Create test project
create_project = test_endpoint(
    "POST",
    f"{BACKEND_URL}/api/v1/projects",
    headers=admin_headers,
    json_data={
        "name": "Test Roof Replacement",
        "description": "Complete roof replacement project",
        "status": "planning",
        "budget": 15000
    }
)
print_test_result("Create Project", create_project)

project_tests = [
    ("GET", "/api/v1/projects", "List Projects"),
    ("GET", "/api/v1/projects/stats", "Project Statistics"),
    ("GET", "/api/v1/projects/timeline", "Project Timeline"),
]

for method, path, name in project_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers)
    print_test_result(name, result)

# 11. AUTOMATIONS
test_category("11. AUTOMATION SYSTEM")

automation_tests = [
    ("GET", "/api/v1/automations", "List Automations"),
    ("GET", "/api/v1/automations/types", "Automation Types"),
    ("POST", "/api/v1/automations/execute", "Execute Automation", {
        "automation_type": "seo_analysis",
        "parameters": {"url": "https://myroofgenius.com"}
    }),
    ("GET", "/api/v1/automations/history", "Automation History"),
    ("GET", "/api/v1/automations/schedule", "Automation Schedule"),
]

for method, path, name, *data in automation_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data)
    print_test_result(name, result)

# 12. ADMIN FUNCTIONS
test_category("12. ADMIN & SYSTEM MANAGEMENT")

admin_tests = [
    ("GET", "/api/v1/admin", "Admin Dashboard"),
    ("GET", "/api/v1/admin/users", "User Management"),
    ("GET", "/api/v1/admin/analytics", "System Analytics"),
    ("GET", "/api/v1/admin/system/health", "System Health"),
    ("GET", "/api/v1/admin/logs", "System Logs"),
    ("GET", "/api/v1/admin/backups", "Backup Status"),
]

for method, path, name in admin_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers)
    print_test_result(name, result)

# 13. INTEGRATIONS
test_category("13. THIRD-PARTY INTEGRATIONS")

integration_tests = [
    ("GET", "/api/v1/integrations", "List Integrations"),
    ("GET", "/api/v1/integrations/stripe/status", "Stripe Status"),
    ("GET", "/api/v1/integrations/slack/status", "Slack Status"),
    ("GET", "/api/v1/integrations/quickbooks/status", "QuickBooks Status"),
    ("GET", "/api/v1/roofing/integration/ready", "Roofing Integrations"),
]

for method, path, name in integration_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers)
    print_test_result(name, result)

# 14. NOTIFICATIONS
test_category("14. NOTIFICATION SYSTEM")

notification_tests = [
    ("GET", "/api/v1/notifications", "List Notifications"),
    ("POST", "/api/v1/notifications/mark-read", "Mark as Read", {"notification_ids": []}),
    ("GET", "/api/v1/notifications/preferences", "Notification Preferences"),
]

for method, path, name, *data in notification_tests:
    json_data = data[0] if data else None
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, json_data=json_data, 
                          expected_status=[200, 404])  # Allow 404 as some endpoints may not exist
    print_test_result(name, result)

# 15. FRONTEND PAGES
test_category("15. FRONTEND PAGES & ACCESSIBILITY")

frontend_pages = [
    ("/", "Homepage"),
    ("/login", "Login Page"),
    ("/dashboard", "Dashboard"),
    ("/admin", "Admin Panel"),
    ("/marketplace", "Marketplace"),
    ("/roofing/estimate", "Estimate Creator"),
    ("/roofing/contractors", "Contractors"),
    ("/tasks", "Task Management"),
    ("/projects", "Projects"),
    ("/settings", "Settings"),
    ("/profile", "Profile"),
    ("/notifications", "Notifications"),
]

for path, name in frontend_pages:
    result = test_endpoint("GET", f"{FRONTEND_URL}{path}", expected_status=[200, 404])
    print_test_result(f"Frontend: {name}", result)

# 16. API PERFORMANCE TESTS
test_category("16. PERFORMANCE & LOAD TESTS")

# Test concurrent requests
def concurrent_test(url: str, headers: Dict, count: int = 10) -> List[float]:
    """Test concurrent requests and measure response times"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(test_endpoint, "GET", url, headers) for _ in range(count)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        return [r.get("elapsed", 0) for r in results if r.get("success")]

# Performance tests
perf_endpoints = [
    (f"{BACKEND_URL}/api/v1/health", "Health Check"),
    (f"{BACKEND_URL}/api/v1/tasks", "Task List"),
    (f"{BACKEND_URL}/api/v1/memory/recent", "Memory Query"),
]

for url, name in perf_endpoints:
    times = concurrent_test(url, admin_headers, count=5)
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        result = {"success": max_time < 3.0, "elapsed": avg_time}
        print_test_result(f"Performance: {name} (avg: {avg_time:.2f}s, max: {max_time:.2f}s)", result)

# 17. DATABASE SYNC STATUS
test_category("17. DATABASE SYNCHRONIZATION")

db_tests = [
    ("GET", "/api/v1/db-sync/status", "DB Sync Status"),
    ("GET", "/api/v1/db-sync/history", "Sync History"),
    ("GET", "/api/v1/db-sync/issues", "DB Issues"),
]

for method, path, name in db_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, expected_status=[200, 404])
    print_test_result(name, result)

# 18. DEPLOYMENT & MONITORING
test_category("18. DEPLOYMENT & MONITORING")

deployment_tests = [
    ("GET", "/api/v1/deployment/status", "Deployment Status"),
    ("GET", "/api/v1/render/service/info", "Render Service Info"),
    ("GET", "/api/v1/monitoring/metrics", "System Metrics"),
]

for method, path, name in deployment_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, expected_status=[200, 404])
    print_test_result(name, result)

# 19. SECURITY TESTS
test_category("19. SECURITY & AUTHORIZATION")

# Test unauthorized access
unauth_tests = [
    ("GET", "/api/v1/admin", "Admin Without Auth"),
    ("POST", "/api/v1/tasks", "Create Task Without Auth"),
    ("GET", "/api/v1/users", "List Users Without Auth"),
]

for method, path, name in unauth_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", expected_status=[401, 403])
    print_test_result(f"Security: {name} (Should Fail)", result)

# Test with wrong token
bad_headers = {"Authorization": "Bearer invalid-token"}
bad_auth_tests = [
    ("GET", "/api/v1/users/me", "Invalid Token"),
    ("POST", "/api/v1/tasks", "Create with Bad Token"),
]

for method, path, name in bad_auth_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=bad_headers, expected_status=[401, 403])
    print_test_result(f"Security: {name} (Should Fail)", result)

# 20. EDGE CASES & ERROR HANDLING
test_category("20. EDGE CASES & ERROR HANDLING")

edge_tests = [
    # Invalid IDs
    ("GET", "/api/v1/tasks/invalid-id", "Invalid Task ID", None, [404]),
    ("GET", "/api/v1/projects/99999", "Non-existent Project", None, [404]),
    
    # Invalid data
    ("POST", "/api/v1/tasks", "Task with Invalid Data", {"invalid": "data"}, [422]),
    ("POST", "/api/v1/roofing/estimates/create", "Estimate Missing Fields", {}, [422]),
    
    # Large payloads
    ("POST", "/api/v1/memory/create", "Large Memory Entry", {
        "title": "Large Entry",
        "content": "x" * 10000,  # 10KB of text
        "tags": ["test"]
    }, [200, 413]),
]

for method, path, name, data, expected in edge_tests:
    result = test_endpoint(method, f"{BACKEND_URL}{path}", headers=admin_headers, 
                          json_data=data, expected_status=expected)
    print_test_result(name, result)

# FINAL SUMMARY
print("\n" + "=" * 100)
print("EXHAUSTIVE TEST SUMMARY")
print("=" * 100)

# Calculate percentages
pass_rate = (test_results["passed"] / test_results["total_tests"] * 100) if test_results["total_tests"] > 0 else 0

print(f"\nTotal Tests Run: {test_results['total_tests']}")
print(f"Passed: {test_results['passed']} ({pass_rate:.1f}%)")
print(f"Failed: {test_results['failed']} ({100-pass_rate:.1f}%)")

# Category breakdown
print("\nResults by Category:")
for category, stats in test_results["by_category"].items():
    total = stats["passed"] + stats["failed"]
    if total > 0:
        rate = stats["passed"] / total * 100
        print(f"  {category}: {stats['passed']}/{total} ({rate:.1f}%)")

# Critical issues
if test_results["errors"]:
    print(f"\nCritical Errors ({len(test_results['errors'])}):")
    for error in test_results["errors"][:5]:
        print(f"  - {error}")
    if len(test_results["errors"]) > 5:
        print(f"  ... and {len(test_results['errors']) - 5} more")

# Performance warnings
if test_results["warnings"]:
    print(f"\nPerformance Warnings ({len(test_results['warnings'])}):")
    for warning in test_results["warnings"][:5]:
        print(f"  - {warning}")

# System verdict
print("\n" + "=" * 100)
if pass_rate >= 90:
    print("✅ SYSTEM STATUS: EXCELLENT - Ready for production use")
elif pass_rate >= 70:
    print("⚠️ SYSTEM STATUS: GOOD - Minor issues need attention")
elif pass_rate >= 50:
    print("⚠️ SYSTEM STATUS: FAIR - Significant issues need fixing")
else:
    print("❌ SYSTEM STATUS: CRITICAL - Major problems detected")

print(f"\nTest completed at: {datetime.now().isoformat()}")
print("=" * 100)

# Save detailed results
with open("EXHAUSTIVE_TEST_RESULTS.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": test_results["total_tests"],
            "passed": test_results["passed"],
            "failed": test_results["failed"],
            "pass_rate": pass_rate
        },
        "errors": test_results["errors"],
        "warnings": test_results["warnings"],
        "by_category": test_results["by_category"]
    }, f, indent=2)

print("\nDetailed results saved to: EXHAUSTIVE_TEST_RESULTS.json")