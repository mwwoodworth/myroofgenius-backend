#!/usr/bin/env python3
"""
COMPLETE SYSTEM REVIEW - Final verification of all systems
"""

import os
import subprocess
import json
import time
import socket
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def check_port(port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.warning(f"Error checking port {port}: {e}")
        return False

def main():
    print("=" * 80)
    print("COMPLETE SYSTEM REVIEW - FINAL VERIFICATION")
    print(f"Time: {datetime.now()}")
    print("=" * 80)
    
    results = {
        "local_services": {},
        "backend_api": {},
        "database": {},
        "frontends": {},
        "persistence": {},
        "summary": {}
    }
    
    # 1. Check Local Services
    print("\n1️⃣ LOCAL SERVICES CHECK:")
    print("-" * 40)
    
    mcp_services = {
        5001: "MCP Database",
        5002: "MCP CRM",
        5003: "MCP ERP",
        5004: "MCP AI Orchestrator",
        5005: "MCP Monitoring",
        5006: "MCP Automation"
    }
    
    ai_agents = {
        6001: "Agent Orchestrator",
        6002: "Agent Analyst",
        6003: "Agent Automation",
        6004: "Agent Customer",
        6005: "Agent Monitoring",
        6006: "Agent Revenue"
    }
    
    mcp_running = 0
    for port, name in mcp_services.items():
        is_running = check_port(port)
        status = "✅ RUNNING" if is_running else "❌ NOT RUNNING"
        print(f"{name}: {status}")
        results["local_services"][name] = is_running
        if is_running:
            mcp_running += 1
    
    print()
    agent_running = 0
    for port, name in ai_agents.items():
        is_running = check_port(port)
        status = "✅ RUNNING" if is_running else "❌ NOT RUNNING"
        print(f"{name}: {status}")
        results["local_services"][name] = is_running
        if is_running:
            agent_running += 1
    
    print(f"\nMCP Servers: {mcp_running}/6")
    print(f"AI Agents: {agent_running}/6")
    
    # 2. Check Backend API
    print("\n2️⃣ BACKEND API CHECK:")
    print("-" * 40)
    
    api_endpoints = [
        "/api/v1/health",
        "/api/v1/erp/jobs",
        "/api/v1/erp/estimates",
        "/api/v1/erp/invoices",
        "/api/v1/crm/customers",
        "/api/v1/integration/mcp/health",
        "/api/v1/integration/agents/health"
    ]
    
    api_working = 0
    for endpoint in api_endpoints:
        try:
            url = f"https://brainops-backend-prod.onrender.com{endpoint}"
            response = requests.get(url, timeout=5)
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{endpoint}: {status}")
            results["backend_api"][endpoint] = response.status_code == 200
            if response.status_code == 200:
                api_working += 1
        except Exception as e:
            print(f"{endpoint}: ❌ ERROR - {str(e)[:50]}")
            results["backend_api"][endpoint] = False
    
    print(f"\nAPI Endpoints: {api_working}/{len(api_endpoints)}")
    
    # 3. Check Database
    print("\n3️⃣ DATABASE CHECK:")
    print("-" * 40)
    
    try:
        db_url = os.environ.get("DATABASE_URL")

        # Get table count
        cmd = f'psql "{db_url}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \'public\';"'
        table_count = subprocess.check_output(cmd, shell=True).decode().strip()
        print(f"Total Tables: {table_count}")
        
        # Get row counts
        for table in ["customers", "jobs", "invoices", "estimates", "ai_agents"]:
            cmd = f'psql "{db_url}" -t -c "SELECT COUNT(*) FROM {table};"'
            try:
                count = subprocess.check_output(cmd, shell=True).decode().strip()
                print(f"{table.capitalize()}: {count}")
                results["database"][table] = int(count)
            except Exception as e:
                logger.error(f"Error querying table {table}: {e}")
                print(f"{table.capitalize()}: ❌ Error")
                results["database"][table] = 0
        
        results["database"]["connected"] = True
    except Exception as e:
        print(f"Database connection: ❌ ERROR - {str(e)[:100]}")
        results["database"]["connected"] = False
    
    # 4. Check Frontends
    print("\n4️⃣ FRONTEND CHECK:")
    print("-" * 40)
    
    frontends = {
        "https://myroofgenius.com": "MyRoofGenius",
        "https://weathercraft-erp.vercel.app": "WeatherCraft ERP",
        "https://brainops-task-os.vercel.app": "BrainOps Task OS"
    }
    
    frontend_working = 0
    for url, name in frontends.items():
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            status = "✅ ONLINE" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{name}: {status}")
            results["frontends"][name] = response.status_code == 200
            if response.status_code == 200:
                frontend_working += 1
        except Exception as e:
            print(f"{name}: ❌ ERROR - {str(e)[:50]}")
            results["frontends"][name] = False
    
    print(f"\nFrontends: {frontend_working}/{len(frontends)}")
    
    # 5. Check Persistence
    print("\n5️⃣ PERSISTENCE CHECK:")
    print("-" * 40)
    
    # Check cron jobs
    try:
        cron_output = subprocess.check_output("crontab -l 2>/dev/null", shell=True).decode()
        has_5min = "*/5 * * * *" in cron_output and "start_all_services.sh" in cron_output
        has_reboot = "@reboot" in cron_output and "start_all_services.sh" in cron_output
        
        print(f"5-minute cron job: {'✅ EXISTS' if has_5min else '❌ MISSING'}")
        print(f"@reboot cron job: {'✅ EXISTS' if has_reboot else '❌ MISSING'}")
        
        results["persistence"]["cron_5min"] = has_5min
        results["persistence"]["cron_reboot"] = has_reboot
    except Exception as e:
        logger.error(f"Error checking cron jobs: {e}")
        print("Cron jobs: ❌ ERROR checking")
        results["persistence"]["cron_5min"] = False
        results["persistence"]["cron_reboot"] = False
    
    # Check bashrc
    try:
        with open(os.path.expanduser("~/.bashrc"), "r") as f:
            bashrc_content = f.read()
            has_bashrc = "start_all_services.sh" in bashrc_content
        print(f"Bashrc autostart: {'✅ EXISTS' if has_bashrc else '❌ MISSING'}")
        results["persistence"]["bashrc"] = has_bashrc
    except Exception as e:
        logger.error(f"Error checking bashrc: {e}")
        print("Bashrc autostart: ❌ ERROR checking")
        results["persistence"]["bashrc"] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY:")
    print("=" * 80)
    
    total_services = mcp_running + agent_running
    total_expected = 12
    
    total_endpoints = api_working
    expected_endpoints = len(api_endpoints)
    
    total_frontends = frontend_working
    expected_frontends = len(frontends)
    
    overall_percentage = (
        (total_services / total_expected * 0.4) +
        (total_endpoints / expected_endpoints * 0.3) +
        (total_frontends / expected_frontends * 0.2) +
        (0.1 if results["database"].get("connected", False) else 0)
    ) * 100
    
    print(f"Local Services: {total_services}/{total_expected} ({total_services/total_expected*100:.0f}%)")
    print(f"API Endpoints: {total_endpoints}/{expected_endpoints} ({total_endpoints/expected_endpoints*100:.0f}%)")
    print(f"Frontends: {total_frontends}/{expected_frontends} ({total_frontends/expected_frontends*100:.0f}%)")
    print(f"Database: {'✅ CONNECTED' if results['database'].get('connected', False) else '❌ DISCONNECTED'}")
    print(f"Persistence: {'✅ CONFIGURED' if results['persistence'].get('cron_5min', False) else '⚠️ PARTIAL'}")
    
    print(f"\n🎯 OVERALL SYSTEM STATUS: {overall_percentage:.1f}% OPERATIONAL")
    
    if overall_percentage >= 95:
        print("\n✅ SYSTEM IS FULLY OPERATIONAL AND PERMANENT!")
        print("   All services will auto-restart on failure.")
        print("   No manual intervention required.")
    elif overall_percentage >= 80:
        print("\n⚠️ SYSTEM IS MOSTLY OPERATIONAL")
        print("   Some services may need attention.")
    else:
        print("\n❌ SYSTEM HAS CRITICAL ISSUES")
        print("   Manual intervention required.")
    
    # Save results
    with open("/home/mwwoodworth/code/SYSTEM_REVIEW_RESULTS.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "overall_percentage": overall_percentage,
            "results": results
        }, f, indent=2)
    
    print("\n📝 Results saved to SYSTEM_REVIEW_RESULTS.json")
    print("=" * 80)

if __name__ == "__main__":
    main()