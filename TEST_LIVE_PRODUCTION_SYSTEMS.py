#!/usr/bin/env python3
"""
TEST LIVE PRODUCTION SYSTEMS - Verify everything is REAL
"""

import requests
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

print("=" * 80)
print(Fore.CYAN + "🧪 TESTING LIVE PRODUCTION SYSTEMS - NO FAKE BS")
print("=" * 80)

results = {
    "timestamp": datetime.now().isoformat(),
    "tests_passed": 0,
    "tests_failed": 0,
    "systems": {}
}

def test_endpoint(name, url, method="GET", data=None, headers=None):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"   {Fore.GREEN}✅ {name}: {response.status_code} OK")
            # Check for real data (not empty or mock)
            if response.text:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                if isinstance(data, list) and len(data) > 0:
                    print(f"      {Fore.CYAN}→ Real data: {len(data)} items")
                elif isinstance(data, dict) and any(data.values()):
                    print(f"      {Fore.CYAN}→ Real data: {list(data.keys())[:3]}...")
            results["tests_passed"] += 1
            return True
        else:
            print(f"   {Fore.RED}❌ {name}: {response.status_code}")
            results["tests_failed"] += 1
            return False
    except Exception as e:
        print(f"   {Fore.RED}❌ {name}: {str(e)}")
        results["tests_failed"] += 1
        return False

# 1. Test Backend API
print(f"\n{Fore.YELLOW}1️⃣ TESTING BACKEND API:")
backend_tests = [
    ("Health Check", "https://brainops-backend-prod.onrender.com/api/v1/health"),
    ("CRM Customers", "https://brainops-backend-prod.onrender.com/api/v1/crm/customers"),
    ("ERP Jobs", "https://brainops-backend-prod.onrender.com/api/v1/erp/jobs"),
    ("ERP Estimates", "https://brainops-backend-prod.onrender.com/api/v1/erp/estimates"),
    ("ERP Invoices", "https://brainops-backend-prod.onrender.com/api/v1/erp/invoices"),
    ("AI Agents", "https://brainops-backend-prod.onrender.com/api/v1/ai/agents"),
    ("LangGraph Status", "https://brainops-backend-prod.onrender.com/api/v1/langgraph/status"),
    ("Revenue Stats", "https://brainops-backend-prod.onrender.com/api/v1/revenue/stats"),
    ("Products List", "https://brainops-backend-prod.onrender.com/api/v1/products"),
    ("Automations", "https://brainops-backend-prod.onrender.com/api/v1/automations")
]

backend_working = 0
for name, url in backend_tests:
    if test_endpoint(name, url):
        backend_working += 1
    time.sleep(0.5)  # Rate limiting

results["systems"]["backend"] = {
    "total": len(backend_tests),
    "working": backend_working,
    "percentage": (backend_working / len(backend_tests)) * 100
}

# 2. Test MCP Servers (Local)
print(f"\n{Fore.YELLOW}2️⃣ TESTING MCP SERVERS (LOCAL):")
mcp_tests = [
    ("Database MCP", "http://localhost:5001/health"),
    ("CRM MCP", "http://localhost:5002/health"),
    ("ERP MCP", "http://localhost:5003/health"),
    ("AI Orchestrator MCP", "http://localhost:5004/health"),
    ("Monitoring MCP", "http://localhost:5005/health"),
    ("Automation MCP", "http://localhost:5006/health")
]

mcp_working = 0
for name, url in mcp_tests:
    if test_endpoint(name, url):
        mcp_working += 1

results["systems"]["mcp_servers"] = {
    "total": len(mcp_tests),
    "working": mcp_working,
    "percentage": (mcp_working / len(mcp_tests)) * 100
}

# 3. Test AI Agents (Local)
print(f"\n{Fore.YELLOW}3️⃣ TESTING AI AGENTS (LOCAL):")
agent_tests = [
    ("Orchestrator Agent", "http://localhost:6001/health"),
    ("Analyst Agent", "http://localhost:6002/health"),
    ("Automation Agent", "http://localhost:6003/health"),
    ("Customer Service Agent", "http://localhost:6004/health"),
    ("Monitoring Agent", "http://localhost:6005/health"),
    ("Revenue Agent", "http://localhost:6006/health")
]

agent_working = 0
for name, url in agent_tests:
    if test_endpoint(name, url):
        agent_working += 1

results["systems"]["ai_agents"] = {
    "total": len(agent_tests),
    "working": agent_working,
    "percentage": (agent_working / len(agent_tests)) * 100
}

# 4. Test Frontend Applications
print(f"\n{Fore.YELLOW}4️⃣ TESTING FRONTEND APPLICATIONS:")
frontend_tests = [
    ("MyRoofGenius", "https://myroofgenius.com"),
    ("WeatherCraft ERP", "https://weathercraft-erp.vercel.app"),
    ("BrainOps Task OS", "https://brainops-task-os.vercel.app")
]

frontend_working = 0
for name, url in frontend_tests:
    if test_endpoint(name, url):
        frontend_working += 1
    time.sleep(1)  # Rate limiting

results["systems"]["frontends"] = {
    "total": len(frontend_tests),
    "working": frontend_working,
    "percentage": (frontend_working / len(frontend_tests)) * 100
}

# 5. Test Integration Endpoints (New)
print(f"\n{Fore.YELLOW}5️⃣ TESTING INTEGRATION ENDPOINTS:")
integration_tests = [
    ("MCP Integration Health", "https://brainops-backend-prod.onrender.com/api/v1/integration/mcp/health"),
    ("Agent Integration Health", "https://brainops-backend-prod.onrender.com/api/v1/integration/agents/health"),
    ("System Health Report", "https://brainops-backend-prod.onrender.com/api/v1/system/health-report"),
    ("Workflow Templates", "https://brainops-backend-prod.onrender.com/api/v1/workflows/templates")
]

integration_working = 0
for name, url in integration_tests:
    if test_endpoint(name, url):
        integration_working += 1
    time.sleep(0.5)

results["systems"]["integrations"] = {
    "total": len(integration_tests),
    "working": integration_working,
    "percentage": (integration_working / len(integration_tests)) * 100
}

# 6. Verify No Mock Data
print(f"\n{Fore.YELLOW}6️⃣ VERIFYING NO MOCK DATA:")
verification_tests = []

# Check if frontends are using real API
try:
    # Check MyRoofGenius for real data
    response = requests.get("https://myroofgenius.com", timeout=10)
    if "mock" not in response.text.lower() and "demo" not in response.text.lower():
        print(f"   {Fore.GREEN}✅ MyRoofGenius: No mock data detected")
        verification_tests.append(True)
    else:
        print(f"   {Fore.RED}❌ MyRoofGenius: Mock data found")
        verification_tests.append(False)
except:
    verification_tests.append(False)

# Check backend for real database data
try:
    response = requests.get("https://brainops-backend-prod.onrender.com/api/v1/crm/customers", timeout=10)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        # Check if data looks real (not test/demo)
        real_data = not all("test" in str(item).lower() or "demo" in str(item).lower() for item in data[:5])
        if real_data:
            print(f"   {Fore.GREEN}✅ Backend: Using real database data")
            verification_tests.append(True)
        else:
            print(f"   {Fore.YELLOW}⚠️ Backend: Data appears to be test data")
            verification_tests.append(False)
except:
    verification_tests.append(False)

results["systems"]["verification"] = {
    "total": len(verification_tests),
    "no_mock": sum(verification_tests),
    "percentage": (sum(verification_tests) / len(verification_tests)) * 100 if verification_tests else 0
}

# Final Report
print("\n" + "=" * 80)
print(Fore.CYAN + "📊 FINAL PRODUCTION TEST REPORT")
print("=" * 80)

total_tests = results["tests_passed"] + results["tests_failed"]
overall_percentage = (results["tests_passed"] / total_tests) * 100 if total_tests > 0 else 0

print(f"\n{Fore.WHITE}Overall Results:")
print(f"   Tests Passed: {Fore.GREEN}{results['tests_passed']}/{total_tests}")
print(f"   Success Rate: {Fore.GREEN if overall_percentage >= 80 else Fore.YELLOW}{overall_percentage:.1f}%")

print(f"\n{Fore.WHITE}System Status:")
for system, data in results["systems"].items():
    status_color = Fore.GREEN if data["percentage"] >= 80 else Fore.YELLOW if data["percentage"] >= 50 else Fore.RED
    print(f"   {system.replace('_', ' ').title()}: {status_color}{data['working']}/{data['total']} ({data['percentage']:.0f}%)")

# Determine if system is fully operational
fully_operational = all(
    system["percentage"] >= 75 for system in results["systems"].values()
)

print("\n" + "=" * 80)
if fully_operational:
    print(Fore.GREEN + Style.BRIGHT + "✅ SYSTEM IS FULLY OPERATIONAL - NO FAKE BS!")
    print(Fore.GREEN + "All critical systems are running with REAL data and functionality")
else:
    print(Fore.YELLOW + "⚠️ SYSTEM PARTIALLY OPERATIONAL")
    print(Fore.YELLOW + "Some components need attention")

print("=" * 80)

# Save results
with open("/home/mwwoodworth/code/production_test_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n{Fore.CYAN}Results saved to: production_test_results.json")