#!/usr/bin/env python3
"""
Test actual working endpoints with proper trailing slashes
"""

import requests
import json
from colorama import init, Fore

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(name, method, path):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json={}, timeout=5)
        
        if r.status_code in [200, 201, 307, 422, 401]:
            print(f"{Fore.GREEN}✓ {name}: {r.status_code}")
            if r.status_code == 200 and r.text:
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"  Response keys: {keys}")
                except:
                    pass
            return True
        else:
            print(f"{Fore.RED}✗ {name}: {r.status_code}")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ {name}: {str(e)}")
        return False

print(f"\n{Fore.CYAN}Testing Actual Working Endpoints")
print(f"{Fore.CYAN}{'='*50}")

# Core endpoints
print(f"\n{Fore.YELLOW}Core System:")
test_endpoint("Root", "GET", "/")
test_endpoint("Health", "GET", "/health")
test_endpoint("API Health", "GET", "/api/v1/health")
test_endpoint("System Status", "GET", "/api/v1/system/status")

# New v6 endpoints with trailing slash
print(f"\n{Fore.YELLOW}Task Management:")
test_endpoint("Tasks List", "GET", "/api/v1/tasks/")
test_endpoint("Workflows", "GET", "/api/v1/tasks/workflows/")

print(f"\n{Fore.YELLOW}File Management:")
test_endpoint("Files List", "GET", "/api/v1/files/")
test_endpoint("Storage Stats", "GET", "/api/v1/files/storage/")

print(f"\n{Fore.YELLOW}Memory System:")
test_endpoint("Recent Memories", "GET", "/api/v1/memory/recent/")

print(f"\n{Fore.YELLOW}Automation:")
test_endpoint("Automations List", "GET", "/api/v1/automation/")

print(f"\n{Fore.YELLOW}Analytics:")
test_endpoint("Dashboard", "GET", "/api/v1/analytics/dashboard/")

print(f"\n{Fore.YELLOW}CRM:")
test_endpoint("Customers", "GET", "/api/v1/crm/customers/")
test_endpoint("Jobs", "GET", "/api/v1/crm/jobs/")
test_endpoint("Invoices", "GET", "/api/v1/crm/invoices/")
test_endpoint("Estimates", "GET", "/api/v1/crm/estimates/")

print(f"\n{Fore.YELLOW}Revenue (v5.14 endpoints):")
test_endpoint("Test Revenue", "GET", "/api/v1/test-revenue/")
test_endpoint("AI Estimation", "GET", "/api/v1/ai-estimation/competitor-analysis")

print(f"\n{Fore.CYAN}{'='*50}")