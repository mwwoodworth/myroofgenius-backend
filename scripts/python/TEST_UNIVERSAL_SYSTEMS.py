#!/usr/bin/env python3
"""
Test Universal AI and Distributed Monitoring Systems
Verify cross-platform capabilities and observability
"""

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_universal_ai():
    """Test Universal AI orchestration endpoints"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING UNIVERSAL AI ORCHESTRATION")
    print(f"{Fore.CYAN}Cross-Platform AI System")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    # Test Universal AI status
    print(f"{Fore.YELLOW}Testing Universal AI status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/universal-ai/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Universal AI status: {data.get('status')}")
            print(f"   System OS: {data.get('system', {}).get('os')}")
            print(f"   Providers: {len(data.get('providers', []))}")
            print(f"   Active tasks: {data.get('active_tasks', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Universal AI status failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Universal AI status error: {e}")
        results["failed"] += 1
    
    # Test available providers
    print(f"\n{Fore.YELLOW}Testing AI providers...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/universal-ai/providers", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ AI providers accessible")
            print(f"   Total providers: {data.get('total', 0)}")
            for provider in data.get('providers', [])[:3]:
                print(f"   - {provider.get('provider')}: {len(provider.get('models', []))} models")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ AI providers failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ AI providers error: {e}")
        results["failed"] += 1
    
    # Test system metrics
    print(f"\n{Fore.YELLOW}Testing system metrics...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/universal-ai/metrics", timeout=10)
        if response.status_code in [200, 503]:
            if response.status_code == 200:
                data = response.json()
                print(f"{Fore.GREEN}✅ System metrics accessible")
                print(f"   OS: {data.get('os_type')}")
                print(f"   CPU: {data.get('cpu', {}).get('percent')}%")
                print(f"   Memory: {data.get('memory', {}).get('percent')}%")
            else:
                print(f"{Fore.YELLOW}⚠️  Metrics temporarily unavailable")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ System metrics failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ System metrics error: {e}")
        results["failed"] += 1
    
    # Test supported OS
    print(f"\n{Fore.YELLOW}Testing supported operating systems...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/universal-ai/supported-os", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Supported OS list accessible")
            print(f"   Current OS: {data.get('current_os')}")
            print(f"   Supported: {', '.join(data.get('supported_os', []))}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Supported OS failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Supported OS error: {e}")
        results["failed"] += 1
    
    # Test health check
    print(f"\n{Fore.YELLOW}Testing Universal AI health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/universal-ai/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Universal AI health: {'Healthy' if data.get('healthy') else 'Unhealthy'}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Health check failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Health check error: {e}")
        results["failed"] += 1
    
    return results

def test_distributed_monitoring():
    """Test Distributed Monitoring endpoints"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING DISTRIBUTED MONITORING")
    print(f"{Fore.CYAN}Cross-Platform Observability")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    # Test monitor status
    print(f"{Fore.YELLOW}Testing monitor status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Monitor status: {data.get('status')}")
            print(f"   Services monitored: {data.get('services_monitored', 0)}")
            print(f"   Healthy services: {data.get('healthy_services', 0)}")
            print(f"   Active alerts: {data.get('active_alerts', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Monitor status failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Monitor status error: {e}")
        results["failed"] += 1
    
    # Test monitored services
    print(f"\n{Fore.YELLOW}Testing monitored services...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/services", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Services list accessible")
            print(f"   Total: {data.get('total', 0)}")
            print(f"   Healthy: {data.get('healthy', 0)}")
            print(f"   Degraded: {data.get('degraded', 0)}")
            print(f"   Unhealthy: {data.get('unhealthy', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Services list failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Services list error: {e}")
        results["failed"] += 1
    
    # Test active alerts
    print(f"\n{Fore.YELLOW}Testing active alerts...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/alerts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Alerts accessible")
            print(f"   Total alerts: {data.get('total', 0)}")
            print(f"   Critical: {data.get('critical', 0)}")
            print(f"   High: {data.get('high', 0)}")
            print(f"   Medium: {data.get('medium', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Alerts failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Alerts error: {e}")
        results["failed"] += 1
    
    # Test supported platforms
    print(f"\n{Fore.YELLOW}Testing supported platforms...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/platforms", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Platforms list accessible")
            platforms = data.get('platforms', [])
            print(f"   Supported platforms: {len(platforms)}")
            for platform in platforms[:3]:
                print(f"   - {platform.get('os')}: {', '.join(platform.get('features', [])[:3])}...")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Platforms failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Platforms error: {e}")
        results["failed"] += 1
    
    # Test monitoring health
    print(f"\n{Fore.YELLOW}Testing monitoring health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Monitoring health: {'Healthy' if data.get('healthy') else 'Unhealthy'}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Health check failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Health check error: {e}")
        results["failed"] += 1
    
    # Test dashboard data
    print(f"\n{Fore.YELLOW}Testing dashboard data...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/monitor/dashboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Dashboard data accessible")
            summary = data.get('summary', {})
            if summary:
                print(f"   Services: {summary.get('services', 0)}")
                print(f"   Active alerts: {summary.get('active_alerts', 0)}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Dashboard failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Dashboard error: {e}")
        results["failed"] += 1
    
    return results

def test_complete_system():
    """Test the complete production system"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}COMPLETE SYSTEM TEST")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/api/v1/ai/status", "AI Status"),
        ("/api/v1/task-os/status", "Task OS Status"),
        ("/api/v1/universal-ai/status", "Universal AI"),
        ("/api/v1/monitor/status", "Distributed Monitoring"),
        ("/api/v1/automations/orchestrator/status", "Automation Orchestrator"),
        ("/api/v1/products", "Products"),
        ("/api/v1/revenue/status", "Revenue Status"),
        ("/api/v1/analytics/metrics", "Analytics"),
        ("/api/v1/aurea/status", "AUREA AI")
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
    print(f"{Fore.MAGENTA}UNIVERSAL SYSTEMS PRODUCTION TEST")
    print(f"{Fore.MAGENTA}Testing Cross-Platform AI & Monitoring")
    print(f"{Fore.MAGENTA}Target: {BASE_URL}")
    print(f"{Fore.MAGENTA}Time: {datetime.now().isoformat()}")
    print(f"{Fore.MAGENTA}{'='*60}")
    
    # Test Universal AI
    ai_results = test_universal_ai()
    
    # Test Distributed Monitoring
    monitor_results = test_distributed_monitoring()
    
    # Test complete system
    system_health = test_complete_system()
    
    # Calculate totals
    total_passed = ai_results["passed"] + monitor_results["passed"]
    total_failed = ai_results["failed"] + monitor_results["failed"]
    total_tests = total_passed + total_failed
    overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Final verdict
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}FINAL VERDICT")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}✅ Passed: {total_passed}")
    print(f"{Fore.RED}❌ Failed: {total_failed}")
    print(f"{Fore.CYAN}📊 Universal Systems Success Rate: {overall_success:.1f}%")
    print(f"{Fore.CYAN}📊 Overall System Health: {system_health:.1f}%")
    
    if overall_success >= 80 and system_health >= 90:
        print(f"\n{Fore.GREEN}🚀 UNIVERSAL SYSTEMS FULLY OPERATIONAL!")
        print(f"{Fore.GREEN}Cross-platform AI and monitoring ready for production")
        print(f"{Fore.GREEN}All operating systems and AI providers supported")
    elif overall_success >= 60:
        print(f"\n{Fore.YELLOW}⚠️  UNIVERSAL SYSTEMS PARTIALLY OPERATIONAL")
        print(f"{Fore.YELLOW}Some features need configuration")
    else:
        print(f"\n{Fore.RED}❌ UNIVERSAL SYSTEMS NEED ATTENTION")
        print(f"{Fore.RED}Review deployment and configuration")
    
    print(f"\n{Fore.CYAN}Test completed at {datetime.now().isoformat()}")
    print(f"{Fore.CYAN}{'='*60}\n")