#!/usr/bin/env python3
"""
PRODUCTION SYSTEMS TEST - COMPREHENSIVE ANALYSIS
Tests all live production systems and generates a detailed report
"""

import requests
import json
from datetime import datetime
import time

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def test_backend():
    """Test BrainOps Backend API"""
    print(f"\n{BOLD}🔧 TESTING BACKEND API{RESET}")
    results = {}
    
    # Test health endpoint
    try:
        r = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=5)
        health = r.json()
        results['health'] = {
            'status': '✅' if r.status_code == 200 else '❌',
            'version': health.get('version', 'unknown'),
            'routers': health.get('loaded_routers', 0)
        }
        print(f"  Health: {results['health']['status']} Version {health.get('version')}, {health.get('loaded_routers')} routers")
    except Exception as e:
        results['health'] = {'status': '❌', 'error': str(e)}
        print(f"  Health: ❌ {str(e)}")
    
    # Test Vercel webhook endpoints
    endpoints = [
        "/api/v1/logs/vercel",
        "/api/v1/webhooks/vercel"
    ]
    
    for endpoint in endpoints:
        try:
            r = requests.post(f"https://brainops-backend-prod.onrender.com{endpoint}", 
                            json={"test": True}, timeout=5)
            status = '✅' if r.status_code in [200, 201] else f'❌ ({r.status_code})'
            results[endpoint] = status
            print(f"  {endpoint}: {status}")
        except Exception as e:
            results[endpoint] = f'❌ ({str(e)})'
            print(f"  {endpoint}: ❌ {str(e)}")
    
    return results

def test_myroofgenius():
    """Test MyRoofGenius Frontend"""
    print(f"\n{BOLD}🏠 TESTING MYROOFGENIUS{RESET}")
    results = {}
    
    # Test main site
    try:
        r = requests.get("https://www.myroofgenius.com", timeout=5)
        results['homepage'] = '✅' if r.status_code == 200 else f'❌ ({r.status_code})'
        print(f"  Homepage: {results['homepage']}")
    except Exception as e:
        results['homepage'] = f'❌ ({str(e)})'
        print(f"  Homepage: ❌ {str(e)}")
    
    # Test critical pages
    pages = ['/pricing', '/ai-analyzer', '/marketplace']
    for page in pages:
        try:
            r = requests.get(f"https://www.myroofgenius.com{page}", timeout=5)
            results[page] = '✅' if r.status_code == 200 else f'❌ ({r.status_code})'
            print(f"  {page}: {results[page]}")
        except Exception as e:
            results[page] = f'❌ ({str(e)})'
            print(f"  {page}: ❌ {str(e)}")
    
    # Test lead capture API
    try:
        test_lead = {
            "email": f"test_{int(time.time())}@example.com",
            "name": "Production Test",
            "offer": "ai-analysis"
        }
        r = requests.post("https://www.myroofgenius.com/api/leads/capture", 
                         json=test_lead, timeout=5)
        results['lead_capture'] = '✅' if r.status_code in [200, 201] else f'❌ ({r.status_code})'
        print(f"  Lead Capture: {results['lead_capture']}")
    except Exception as e:
        results['lead_capture'] = f'❌ ({str(e)})'
        print(f"  Lead Capture: ❌ {str(e)}")
    
    return results

def test_weathercraft():
    """Test WeatherCraft Systems"""
    print(f"\n{BOLD}🌦️ TESTING WEATHERCRAFT{RESET}")
    results = {}
    
    # Test WeatherCraft App
    try:
        r = requests.get("https://weathercraft-app.vercel.app", timeout=5)
        results['app'] = '✅' if r.status_code == 200 else f'❌ ({r.status_code})'
        print(f"  WeatherCraft App: {results['app']}")
    except Exception as e:
        results['app'] = f'❌ ({str(e)})'
        print(f"  WeatherCraft App: ❌ {str(e)}")
    
    # Test WeatherCraft ERP
    try:
        r = requests.get("https://weathercraft-erp.vercel.app", timeout=5)
        results['erp'] = '✅' if r.status_code == 200 else f'❌ ({r.status_code})'
        print(f"  WeatherCraft ERP: {results['erp']}")
    except Exception as e:
        results['erp'] = f'❌ ({str(e)})'
        print(f"  WeatherCraft ERP: ❌ {str(e)}")
    
    return results

def test_task_os():
    """Test Task OS"""
    print(f"\n{BOLD}📋 TESTING TASK OS{RESET}")
    results = {}
    
    try:
        r = requests.get("https://brainops-task-os.vercel.app", timeout=5)
        results['status'] = '✅' if r.status_code == 200 else f'❌ ({r.status_code})'
        print(f"  Task OS: {results['status']}")
    except Exception as e:
        results['status'] = f'❌ ({str(e)})'
        print(f"  Task OS: ❌ {str(e)}")
    
    return results

def generate_report(all_results):
    """Generate comprehensive report"""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}📊 PRODUCTION SYSTEMS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    
    # Calculate overall health
    total_tests = 0
    passed_tests = 0
    
    for system, results in all_results.items():
        for test, result in results.items():
            total_tests += 1
            if isinstance(result, str) and '✅' in result:
                passed_tests += 1
            elif isinstance(result, dict) and result.get('status') == '✅':
                passed_tests += 1
    
    health_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Overall status
    if health_percentage >= 90:
        status_color = GREEN
        status_text = "EXCELLENT"
    elif health_percentage >= 70:
        status_color = YELLOW
        status_text = "OPERATIONAL"
    else:
        status_color = RED
        status_text = "DEGRADED"
    
    print(f"\n{BOLD}OVERALL SYSTEM HEALTH: {status_color}{health_percentage:.1f}% - {status_text}{RESET}")
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    # Critical issues
    print(f"\n{BOLD}CRITICAL ISSUES:{RESET}")
    issues = []
    
    # Check backend version
    backend_health = all_results.get('backend', {}).get('health', {})
    if isinstance(backend_health, dict) and backend_health.get('version') != '4.34':
        issues.append(f"❌ Backend running v{backend_health.get('version', 'unknown')} instead of v4.34")
    
    # Check Vercel webhooks
    if '❌' in str(all_results.get('backend', {}).get('/api/v1/logs/vercel', '')):
        issues.append("❌ Vercel log endpoint not working")
    if '❌' in str(all_results.get('backend', {}).get('/api/v1/webhooks/vercel', '')):
        issues.append("❌ Vercel webhook endpoint not working")
    
    # Check lead capture
    if '❌' in str(all_results.get('myroofgenius', {}).get('lead_capture', '')):
        issues.append("❌ Lead capture system not working")
    
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"  {GREEN}✅ No critical issues detected{RESET}")
    
    # Revenue readiness
    print(f"\n{BOLD}REVENUE READINESS:{RESET}")
    revenue_ready = []
    revenue_blocked = []
    
    # Check MyRoofGenius
    mrg = all_results.get('myroofgenius', {})
    if '✅' in str(mrg.get('homepage', '')) and '✅' in str(mrg.get('/pricing', '')):
        revenue_ready.append("✅ MyRoofGenius homepage and pricing live")
    else:
        revenue_blocked.append("❌ MyRoofGenius pages not fully operational")
    
    if '✅' in str(mrg.get('lead_capture', '')):
        revenue_ready.append("✅ Lead capture system working")
    else:
        revenue_blocked.append("❌ Lead capture system broken")
    
    # Check WeatherCraft
    wc = all_results.get('weathercraft', {})
    if '✅' in str(wc.get('app', '')):
        revenue_ready.append("✅ WeatherCraft App live")
    
    print(f"  {GREEN}Ready:{RESET}")
    for item in revenue_ready:
        print(f"    {item}")
    
    if revenue_blocked:
        print(f"  {RED}Blocked:{RESET}")
        for item in revenue_blocked:
            print(f"    {item}")
    
    # Next steps
    print(f"\n{BOLD}RECOMMENDED NEXT STEPS:{RESET}")
    if health_percentage < 100:
        if backend_health.get('version') != '4.34':
            print("  1. Fix backend deployment (v4.34 failed to deploy)")
            print("     - Check Render logs for deployment errors")
            print("     - May need to use simpler Dockerfile")
        if '❌' in str(mrg.get('lead_capture', '')):
            print("  2. Fix lead capture API endpoint")
        print("  3. Generate traffic to MyRoofGenius")
        print("  4. Monitor first customer signups")
    else:
        print("  1. ✅ All systems operational!")
        print("  2. Focus on traffic generation")
        print("  3. Monitor conversion rates")
    
    return health_percentage

def main():
    """Run all tests and generate report"""
    print(f"{BOLD}{BLUE}🚀 STARTING PRODUCTION SYSTEMS TEST{RESET}")
    
    all_results = {}
    
    # Run all tests
    all_results['backend'] = test_backend()
    all_results['myroofgenius'] = test_myroofgenius()
    all_results['weathercraft'] = test_weathercraft()
    all_results['task_os'] = test_task_os()
    
    # Generate report
    health = generate_report(all_results)
    
    # Save to file
    with open('/home/mwwoodworth/code/production_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'health_percentage': health,
            'results': all_results
        }, f, indent=2)
    
    print(f"\n{BOLD}📄 Full results saved to: /home/mwwoodworth/code/production_test_results.json{RESET}")
    
    return health

if __name__ == "__main__":
    health = main()
    exit(0 if health >= 90 else 1)