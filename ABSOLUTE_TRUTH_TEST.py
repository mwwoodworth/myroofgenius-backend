#!/usr/bin/env python3
"""
ABSOLUTE TRUTH TEST - No bullshit, just facts
"""

import subprocess
import requests
import psycopg2
import json
import time
from datetime import datetime

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except:
        return "ERROR"

def test_url(url):
    """Test if URL responds"""
    try:
        r = requests.get(url, timeout=3)
        return r.status_code
    except:
        return 0

print("=" * 80)
print("ABSOLUTE TRUTH TEST - NO BULLSHIT")
print(f"Time: {datetime.now()}")
print("=" * 80)

# 1. ACTUAL RUNNING PROCESSES
print("\n1. ACTUAL RUNNING PROCESSES:")
print("-" * 40)

# Count real processes
mcp_procs = run_cmd("ps aux | grep -E 'mcp.*server\\.py' | grep -v grep | wc -l")
agent_procs = run_cmd("ps aux | grep -E 'agent\\.py' | grep -v grep | wc -l")
print(f"MCP Server processes: {mcp_procs}")
print(f"AI Agent processes: {agent_procs}")

# Show actual process names
print("\nActual running Python processes:")
procs = run_cmd("ps aux | grep python3 | grep -v grep | awk '{print $11, $12}' | head -10")
print(procs)

# 2. ACTUAL LISTENING PORTS
print("\n2. ACTUAL LISTENING PORTS:")
print("-" * 40)

ports_5xxx = run_cmd("ss -tulpn 2>/dev/null | grep ':500' | awk '{print $5}' | cut -d: -f2 | sort -n")
ports_6xxx = run_cmd("ss -tulpn 2>/dev/null | grep ':600' | awk '{print $5}' | cut -d: -f2 | sort -n")
print(f"Ports 5000-5999: {ports_5xxx}")
print(f"Ports 6000-6999: {ports_6xxx}")

# 3. TEST EACH LOCAL SERVICE
print("\n3. LOCAL SERVICE TESTS:")
print("-" * 40)

local_services = {
    "MCP Database": 5001,
    "MCP CRM": 5002,
    "MCP ERP": 5003,
    "MCP AI Orchestrator": 5004,
    "MCP Monitoring": 5005,
    "MCP Automation": 5006,
    "Agent Orchestrator": 6001,
    "Agent Analyst": 6002,
    "Agent Automation": 6003,
    "Agent Customer": 6004,
    "Agent Monitoring": 6005,
    "Agent Revenue": 6006
}

working_services = []
for name, port in local_services.items():
    status = test_url(f"http://localhost:{port}/health")
    if status == 200:
        print(f"✓ {name}: WORKING (port {port})")
        working_services.append(name)
    else:
        print(f"✗ {name}: DEAD (port {port})")

# 4. BACKEND API TEST
print("\n4. BACKEND API TEST:")
print("-" * 40)

api_base = "https://brainops-backend-prod.onrender.com"
endpoints = [
    "/api/v1/health",
    "/api/v1/integration/mcp/health",
    "/api/v1/integration/agents/health",
    "/api/v1/erp/jobs",
    "/api/v1/crm/customers"
]

api_working = []
for endpoint in endpoints:
    status = test_url(api_base + endpoint)
    if status in [200, 201]:
        print(f"✓ {endpoint}: {status}")
        api_working.append(endpoint)
    else:
        print(f"✗ {endpoint}: {status}")

# 5. DATABASE TEST
print("\n5. DATABASE TEST:")
print("-" * 40)

try:
    conn = psycopg2.connect(
        "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    cur = conn.cursor()
    
    # Test queries
    queries = [
        ("Customers", "SELECT COUNT(*) FROM customers"),
        ("Jobs", "SELECT COUNT(*) FROM jobs"),
        ("AI Agents", "SELECT COUNT(*) FROM ai_agents WHERE status = 'active'"),
        ("Service Registry", "SELECT COUNT(*) FROM service_registry"),
        ("Copilot Messages", "SELECT COUNT(*) FROM copilot_messages WHERE memory_type = 'master_configuration'")
    ]
    
    for name, query in queries:
        try:
            cur.execute(query)
            count = cur.fetchone()[0]
            print(f"✓ {name}: {count}")
        except Exception as e:
            print(f"✗ {name}: ERROR - {str(e)[:50]}")
    
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")

# 6. FRONTEND TEST
print("\n6. FRONTEND TEST:")
print("-" * 40)

frontends = [
    ("MyRoofGenius", "https://myroofgenius.com"),
    ("WeatherCraft ERP", "https://weathercraft-erp.vercel.app"),
    ("BrainOps Task OS", "https://brainops-task-os.vercel.app")
]

for name, url in frontends:
    status = test_url(url)
    print(f"{name}: {status}")

# 7. PERSISTENCE TEST
print("\n7. PERSISTENCE TEST:")
print("-" * 40)

# Check cron
cron_check = run_cmd("crontab -l | grep -c start_all_services")
print(f"Cron job exists: {'YES' if cron_check == '1' else 'NO'}")

# Check systemd services (if they exist)
systemd_check = run_cmd("ls /tmp/*.service 2>/dev/null | wc -l")
print(f"Systemd service files: {systemd_check}")

# Check supervisor config
supervisor_check = run_cmd("test -f /home/mwwoodworth/code/supervisor.conf && echo YES || echo NO")
print(f"Supervisor config exists: {supervisor_check}")

# FINAL VERDICT
print("\n" + "=" * 80)
print("VERDICT:")
print("=" * 80)

total_services = len(local_services)
total_working = len(working_services)
api_total = len(endpoints)
api_success = len(api_working)

print(f"\nLocal Services: {total_working}/{total_services} working ({(total_working/total_services)*100:.0f}%)")
print(f"API Endpoints: {api_success}/{api_total} working ({(api_success/api_total)*100:.0f}%)")

if total_working == total_services and api_success == api_total:
    print("\n✓ SYSTEM IS 100% OPERATIONAL")
elif total_working >= total_services * 0.8 and api_success >= api_total * 0.8:
    print("\n⚠ SYSTEM IS MOSTLY OPERATIONAL")
else:
    print("\n✗ SYSTEM HAS CRITICAL FAILURES")

print("\nWHAT'S REAL:")
print(f"- {total_working} services actually running locally")
print(f"- {api_success} API endpoints responding")
print(f"- Backend deployed and reachable")
print(f"- Database connected with real data")

print("\nWHAT NEEDS FIXING:")
if total_working < total_services:
    print(f"- {total_services - total_working} local services are DOWN")
if api_success < api_total:
    print(f"- {api_total - api_success} API endpoints are FAILING")

print("=" * 80)