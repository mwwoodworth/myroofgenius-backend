#!/usr/bin/env python3
"""
Test Production Automations - LangGraph Orchestrator
Verifies all automation endpoints and capabilities
"""

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_automation_endpoints():
    """Test all automation orchestrator endpoints"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING PRODUCTION AUTOMATIONS")
    print(f"{Fore.CYAN}LangGraph Orchestrator Integration")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "endpoints": []
    }
    
    # Test orchestrator status
    print(f"{Fore.YELLOW}Testing orchestrator status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/automations/orchestrator/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Orchestrator status: {data.get('status')}")
            print(f"   Capabilities: {', '.join(data.get('capabilities', []))}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Orchestrator status failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Orchestrator status error: {e}")
        results["failed"] += 1
    
    # Test automation health
    print(f"\n{Fore.YELLOW}Testing orchestrator health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/automations/orchestrator/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Orchestrator health: {'Healthy' if data.get('healthy') else 'Unhealthy'}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Health check failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Health check error: {e}")
        results["failed"] += 1
    
    # Test get automation runs
    print(f"\n{Fore.YELLOW}Testing automation runs...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/automations/orchestrator/runs", timeout=10)
        if response.status_code in [200, 401, 403]:
            if response.status_code == 200:
                data = response.json()
                print(f"{Fore.GREEN}✅ Automation runs accessible")
                print(f"   Total runs: {data.get('count', 0)}")
            else:
                print(f"{Fore.YELLOW}⚠️  Automation runs require auth: {response.status_code}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Automation runs failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Automation runs error: {e}")
        results["failed"] += 1
    
    # Test get schedules
    print(f"\n{Fore.YELLOW}Testing automation schedules...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/automations/orchestrator/schedule", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Automation schedules accessible")
            print(f"   Active schedules: {data.get('count', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Schedules failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Schedules error: {e}")
        results["failed"] += 1
    
    # Test metrics endpoint
    print(f"\n{Fore.YELLOW}Testing automation metrics...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/automations/orchestrator/metrics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Automation metrics accessible")
            if "overall" in data:
                overall = data["overall"]
                print(f"   Total runs: {overall.get('total_runs', 0)}")
                print(f"   Successful: {overall.get('successful', 0)}")
                print(f"   Failed: {overall.get('failed', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Metrics failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Metrics error: {e}")
        results["failed"] += 1
    
    # Test automation types
    automation_types = [
        "centerpoint_sync",
        "revenue_optimization", 
        "job_scheduling",
        "customer_communication",
        "invoice_processing",
        "system_monitoring"
    ]
    
    print(f"\n{Fore.YELLOW}Testing automation type endpoints...")
    for automation_type in automation_types:
        try:
            # Just check if endpoint exists (POST requires auth)
            response = requests.post(
                f"{BASE_URL}/api/v1/automations/orchestrator/execute/{automation_type}",
                json={},
                timeout=5
            )
            if response.status_code in [200, 201, 401, 403, 422]:
                print(f"{Fore.GREEN}✅ {automation_type}: Endpoint exists")
                results["passed"] += 1
            else:
                print(f"{Fore.RED}❌ {automation_type}: {response.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"{Fore.RED}❌ {automation_type}: Error - {e}")
            results["failed"] += 1
    
    # Summary
    total = results["passed"] + results["failed"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}AUTOMATION TEST SUMMARY")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}✅ Passed: {results['passed']}")
    print(f"{Fore.RED}❌ Failed: {results['failed']}")
    print(f"{Fore.CYAN}📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"\n{Fore.GREEN}🎉 AUTOMATION ORCHESTRATOR OPERATIONAL!")
        print(f"{Fore.GREEN}LangGraph production automations ready for deployment")
    elif success_rate >= 60:
        print(f"\n{Fore.YELLOW}⚠️  PARTIAL FUNCTIONALITY")
        print(f"{Fore.YELLOW}Some automation features need configuration")
    else:
        print(f"\n{Fore.RED}❌ AUTOMATION SYSTEM NEEDS ATTENTION")
        print(f"{Fore.RED}Check deployment and configuration")
    
    return success_rate >= 80

def test_complete_system():
    """Test the complete production system"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}COMPLETE SYSTEM TEST")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/api/v1/ai/status", "AI Status"),
        ("/api/v1/task-os/status", "Task OS Status"),
        ("/api/v1/jobs/summary", "Jobs Summary"),
        ("/api/v1/products", "Products"),
        ("/api/v1/revenue/status", "Revenue Status"),
        ("/api/v1/estimates/summary", "Estimates Summary"),
        ("/api/v1/analytics/metrics", "Analytics"),
        ("/api/v1/blog/posts", "Blog Posts"),
        ("/api/v1/aurea/status", "AUREA AI"),
        ("/api/v1/automations/orchestrator/status", "Automation Orchestrator")
    ]
    
    passed = 0
    failed = 0
    
    for endpoint, name in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ {name}: Operational")
                passed += 1
            else:
                print(f"{Fore.RED}❌ {name}: {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"{Fore.RED}❌ {name}: Error")
            failed += 1
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Fore.CYAN}Overall System Health: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"{Fore.GREEN}✅ SYSTEM FULLY OPERATIONAL")
    elif success_rate >= 70:
        print(f"{Fore.YELLOW}⚠️  SYSTEM PARTIALLY OPERATIONAL")
    else:
        print(f"{Fore.RED}❌ SYSTEM DEGRADED")
    
    return success_rate

if __name__ == "__main__":
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}BRAINOPS PRODUCTION AUTOMATION TEST")
    print(f"{Fore.MAGENTA}Testing LangGraph Orchestration System")
    print(f"{Fore.MAGENTA}Target: {BASE_URL}")
    print(f"{Fore.MAGENTA}Time: {datetime.now().isoformat()}")
    print(f"{Fore.MAGENTA}{'='*60}")
    
    # Test automations
    automation_success = test_automation_endpoints()
    
    # Test complete system
    system_health = test_complete_system()
    
    # Final verdict
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}FINAL VERDICT")
    print(f"{Fore.CYAN}{'='*60}")
    
    if automation_success and system_health >= 90:
        print(f"{Fore.GREEN}🚀 PRODUCTION READY WITH FULL AUTOMATION!")
        print(f"{Fore.GREEN}All systems operational with LangGraph orchestration")
        print(f"{Fore.GREEN}Deploy with confidence!")
    elif system_health >= 80:
        print(f"{Fore.YELLOW}⚠️  SYSTEM OPERATIONAL, AUTOMATION NEEDS CONFIG")
        print(f"{Fore.YELLOW}Core features working, configure automation settings")
    else:
        print(f"{Fore.RED}❌ SYSTEM NEEDS ATTENTION")
        print(f"{Fore.RED}Review deployment and configuration")
    
    print(f"\n{Fore.CYAN}Test completed at {datetime.now().isoformat()}")
    print(f"{Fore.CYAN}{'='*60}\n")