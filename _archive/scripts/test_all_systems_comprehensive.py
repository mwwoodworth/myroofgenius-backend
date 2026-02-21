#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TEST - ALL 205 TASKS
Tests EVERY endpoint to ensure 100% operational status
"""

import requests
import json
import sys
from datetime import datetime
from typing import List, Dict, Tuple

# Base URL for testing
BASE_URL = "https://brainops-backend-prod.onrender.com"

# Define all endpoints from Tasks 61-110 (the ones we claimed to implement)
TASK_ENDPOINTS = {
    # Tasks 61-70: Sales & CRM
    61: ["/api/v1/leads", "/api/v1/leads/scoring", "/api/v1/leads/bant"],
    62: ["/api/v1/opportunities", "/api/v1/opportunities/pipeline"],
    63: ["/api/v1/pipelines", "/api/v1/pipelines/stages"],
    64: ["/api/v1/quotes", "/api/v1/quotes/templates"],
    65: ["/api/v1/proposals", "/api/v1/proposals/generate"],
    66: ["/api/v1/contracts", "/api/v1/contracts/lifecycle"],
    67: ["/api/v1/commissions", "/api/v1/commissions/calculate"],
    68: ["/api/v1/forecasts", "/api/v1/forecasts/revenue"],
    69: ["/api/v1/territories", "/api/v1/territories/assignments"],
    70: ["/api/v1/sales/analytics", "/api/v1/sales/metrics"],

    # Tasks 71-80: Marketing
    71: ["/api/v1/campaigns", "/api/v1/campaigns/metrics"],
    72: ["/api/v1/email-marketing", "/api/v1/email/templates"],
    73: ["/api/v1/social-media", "/api/v1/social/posts"],
    74: ["/api/v1/lead-nurturing", "/api/v1/nurturing/workflows"],
    75: ["/api/v1/content-marketing", "/api/v1/content/assets"],
    76: ["/api/v1/marketing/analytics", "/api/v1/marketing/roi"],
    77: ["/api/v1/segmentation", "/api/v1/segments/create"],
    78: ["/api/v1/ab-testing", "/api/v1/experiments"],
    79: ["/api/v1/marketing-automation", "/api/v1/automation/workflows"],
    80: ["/api/v1/landing-pages", "/api/v1/pages/conversions"],

    # Tasks 81-90: Customer Service
    81: ["/api/v1/tickets", "/api/v1/tickets/queue"],
    82: ["/api/v1/knowledge-base", "/api/v1/kb/articles"],
    83: ["/api/v1/live-chat", "/api/v1/chat/sessions"],
    84: ["/api/v1/feedback", "/api/v1/surveys"],
    85: ["/api/v1/sla", "/api/v1/sla/compliance"],
    86: ["/api/v1/customer-portal", "/api/v1/portal/access"],
    87: ["/api/v1/service-catalog", "/api/v1/services"],
    88: ["/api/v1/faq", "/api/v1/faq/categories"],
    89: ["/api/v1/support/analytics", "/api/v1/support/metrics"],
    90: ["/api/v1/escalations", "/api/v1/escalations/rules"],

    # Tasks 91-100: Analytics & BI
    91: ["/api/v1/analytics/bi/dashboards", "/api/v1/bi/reports"],
    92: ["/api/v1/data-warehouse", "/api/v1/etl/pipelines"],
    93: ["/api/v1/reporting", "/api/v1/reports/generate"],
    94: ["/api/v1/predictive", "/api/v1/predictions/models"],
    95: ["/api/v1/realtime-analytics", "/api/v1/realtime/streams"],
    96: ["/api/v1/visualizations", "/api/v1/charts"],
    97: ["/api/v1/metrics", "/api/v1/kpis"],
    98: ["/api/v1/data-governance", "/api/v1/governance/policies"],
    99: ["/api/v1/executive-dashboards", "/api/v1/executive/overview"],
    100: ["/api/v1/analytics-api", "/api/v1/analytics/endpoints"],

    # Tasks 101-110: Advanced Operations
    101: ["/api/v1/vendors", "/api/v1/vendors/evaluations"],
    102: ["/api/v1/procurement", "/api/v1/purchase-orders"],
    103: ["/api/v1/contract-lifecycle", "/api/v1/contracts/renewals"],
    104: ["/api/v1/risk-management", "/api/v1/risks/assessments"],
    105: ["/api/v1/compliance", "/api/v1/compliance/audits"],
    106: ["/api/v1/legal", "/api/v1/legal/cases"],
    107: ["/api/v1/insurance", "/api/v1/insurance/claims"],
    108: ["/api/v1/sustainability", "/api/v1/carbon-footprint"],
    109: ["/api/v1/rd_projects", "/api/v1/research/experiments"],
    110: ["/api/v1/strategic-planning", "/api/v1/okrs"],
}

# Core endpoints that should definitely work
CORE_ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/customers",
    "/api/v1/jobs",
    "/api/v1/estimates",
    "/api/v1/invoices",
    "/api/v1/ai/agents",
]

# Frontend applications to test
FRONTEND_APPS = {
    "MyRoofGenius": "https://myroofgenius.com",
    "WeatherCraft ERP": "https://weathercraft-erp.vercel.app",
    "WeatherCraft Public": "https://weathercraft-app.vercel.app",
}

def test_endpoint(url: str) -> Tuple[int, str, any]:
    """Test a single endpoint and return status code, status text, and response"""
    try:
        response = requests.get(url, timeout=5)
        try:
            data = response.json()
        except:
            data = response.text[:200]
        return response.status_code, "OK" if response.status_code < 400 else "FAIL", data
    except requests.exceptions.Timeout:
        return 0, "TIMEOUT", None
    except Exception as e:
        return 0, "ERROR", str(e)

def main():
    print("=" * 80)
    print("COMPREHENSIVE SYSTEM TEST - VALIDATING ALL CLAIMS")
    print("=" * 80)
    print(f"Testing at: {datetime.now().isoformat()}")
    print()

    # Test results storage
    results = {
        "core": {"passed": 0, "failed": 0, "endpoints": []},
        "tasks": {"passed": 0, "failed": 0, "endpoints": []},
        "frontend": {"passed": 0, "failed": 0, "apps": []},
    }

    # 1. Test Core Endpoints
    print("1. TESTING CORE ENDPOINTS")
    print("-" * 40)
    for endpoint in CORE_ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        status_code, status, data = test_endpoint(url)

        if status_code == 200:
            results["core"]["passed"] += 1
            print(f"✅ {endpoint}: {status_code}")
        else:
            results["core"]["failed"] += 1
            print(f"❌ {endpoint}: {status_code} - {status}")

        results["core"]["endpoints"].append({
            "endpoint": endpoint,
            "status_code": status_code,
            "status": status
        })

    print(f"\nCore Results: {results['core']['passed']}/{len(CORE_ENDPOINTS)} passed")

    # 2. Test Task Endpoints (61-110)
    print("\n2. TESTING TASK ENDPOINTS (61-110)")
    print("-" * 40)

    total_task_endpoints = 0
    for task_num, endpoints in TASK_ENDPOINTS.items():
        for endpoint in endpoints:
            total_task_endpoints += 1
            url = f"{BASE_URL}{endpoint}"
            status_code, status, data = test_endpoint(url)

            if status_code == 200:
                results["tasks"]["passed"] += 1
                result = "✅"
            elif status_code == 404:
                results["tasks"]["failed"] += 1
                result = "❌ NOT FOUND"
            elif status_code == 405:
                results["tasks"]["failed"] += 1
                result = "❌ METHOD NOT ALLOWED"
            else:
                results["tasks"]["failed"] += 1
                result = f"❌ {status}"

            if results["tasks"]["failed"] <= 10 or status_code == 200:  # Show first 10 failures and all successes
                print(f"Task {task_num}: {endpoint}: {result} ({status_code})")

            results["tasks"]["endpoints"].append({
                "task": task_num,
                "endpoint": endpoint,
                "status_code": status_code,
                "status": status
            })

    print(f"\nTask Results: {results['tasks']['passed']}/{total_task_endpoints} passed")

    # 3. Test Frontend Applications
    print("\n3. TESTING FRONTEND APPLICATIONS")
    print("-" * 40)
    for app_name, url in FRONTEND_APPS.items():
        status_code, status, data = test_endpoint(url)

        if status_code == 200:
            results["frontend"]["passed"] += 1
            print(f"✅ {app_name}: {status_code} - ONLINE")
        else:
            results["frontend"]["failed"] += 1
            print(f"❌ {app_name}: {status_code} - {status}")

        results["frontend"]["apps"].append({
            "app": app_name,
            "url": url,
            "status_code": status_code,
            "status": status
        })

    print(f"\nFrontend Results: {results['frontend']['passed']}/{len(FRONTEND_APPS)} passed")

    # 4. Test Database Connection
    print("\n4. TESTING DATABASE")
    print("-" * 40)
    health_url = f"{BASE_URL}/api/v1/health"
    status_code, status, data = test_endpoint(health_url)
    if status_code == 200 and isinstance(data, dict):
        print(f"Database Stats from Health endpoint:")
        if "stats" in data:
            for key, value in data["stats"].items():
                print(f"  - {key}: {value}")

    # 5. Calculate Overall Success Rate
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)

    total_passed = results["core"]["passed"] + results["tasks"]["passed"] + results["frontend"]["passed"]
    total_tests = (
        len(CORE_ENDPOINTS) +
        total_task_endpoints +
        len(FRONTEND_APPS)
    )

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"Core Endpoints: {results['core']['passed']}/{len(CORE_ENDPOINTS)} ({results['core']['passed']/len(CORE_ENDPOINTS)*100:.1f}%)")
    print(f"Task Endpoints: {results['tasks']['passed']}/{total_task_endpoints} ({results['tasks']['passed']/total_task_endpoints*100:.1f}%)")
    print(f"Frontend Apps: {results['frontend']['passed']}/{len(FRONTEND_APPS)} ({results['frontend']['passed']/len(FRONTEND_APPS)*100:.1f}%)")
    print(f"\nTOTAL: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")

    # 6. List Failed Endpoints
    if results["tasks"]["failed"] > 0:
        print("\n" + "=" * 80)
        print("FAILED ENDPOINTS (First 20)")
        print("=" * 80)
        count = 0
        for endpoint_data in results["tasks"]["endpoints"]:
            if endpoint_data["status_code"] != 200:
                count += 1
                print(f"{count}. Task {endpoint_data['task']}: {endpoint_data['endpoint']} - {endpoint_data['status_code']}")
                if count >= 20:
                    print(f"... and {results['tasks']['failed'] - 20} more failures")
                    break

    # 7. Final Verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    if success_rate >= 90:
        print("✅ System is OPERATIONAL (90%+ success rate)")
    elif success_rate >= 70:
        print("⚠️ System is PARTIALLY OPERATIONAL (70-89% success rate)")
    else:
        print("❌ System is NOT OPERATIONAL (<70% success rate)")

    print(f"\nActual Success Rate: {success_rate:.1f}%")

    # Save detailed results
    with open("test_results_comprehensive.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to test_results_comprehensive.json")

    return success_rate

if __name__ == "__main__":
    success_rate = main()
    sys.exit(0 if success_rate >= 90 else 1)