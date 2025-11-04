#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TEST - Task OS & AI Integration
Tests all systems for real operational readiness
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
from colorama import init, Fore, Style

init(autoreset=True)

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TASK_OS_URL = "https://brainops-task-os.vercel.app"
MYROOFGENIUS_URL = "https://myroofgenius.com"

class SystemTester:
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
        
    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a test and record results"""
        try:
            result = func(*args, **kwargs)
            if result:
                self.results["passed"] += 1
                print(f"{Fore.GREEN}✅ {name}")
                self.results["tests"].append({"name": name, "status": "passed"})
                return True
            else:
                self.results["failed"] += 1
                print(f"{Fore.RED}❌ {name}")
                self.results["tests"].append({"name": name, "status": "failed"})
                return False
        except Exception as e:
            self.results["failed"] += 1
            print(f"{Fore.RED}❌ {name}: {str(e)}")
            self.results["tests"].append({"name": name, "status": "error", "error": str(e)})
            return False
    
    def warning(self, message: str):
        """Add a warning"""
        self.results["warnings"] += 1
        print(f"{Fore.YELLOW}⚠️  {message}")
        
    def section(self, title: str):
        """Print section header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{title}")
        print(f"{Fore.CYAN}{'='*60}")

def test_backend_health() -> bool:
    """Test backend health endpoint"""
    r = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            data.get("status") == "healthy" and
            data.get("version") == "3.4.05")

def test_ai_status() -> bool:
    """Test AI status endpoint"""
    r = requests.get(f"{BACKEND_URL}/api/v1/ai/status", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            data.get("status") == "operational" and
            "metrics" in data)

def test_ai_revenue() -> bool:
    """Test AI revenue analysis"""
    r = requests.get(f"{BACKEND_URL}/api/v1/ai/revenue/analysis", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "analysis" in data and
            "opportunities" in data)

def test_ai_command() -> bool:
    """Test AI command execution"""
    command_data = {
        "command": "Test command execution",
        "context": {"test": True},
        "priority": 5
    }
    r = requests.post(f"{BACKEND_URL}/api/v1/ai/command", 
                     json=command_data, timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            data.get("success") == True)

def test_ai_system_health() -> bool:
    """Test AI system health monitoring"""
    r = requests.get(f"{BACKEND_URL}/api/v1/ai/system/health", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "health" in data and
            data["health"].get("status") in ["healthy", "degraded", "unknown"])

def test_self_healing() -> bool:
    """Test self-healing trigger"""
    r = requests.post(f"{BACKEND_URL}/api/v1/ai/system/heal", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "healing_id" in data)

def test_task_os_status() -> bool:
    """Test Task OS status endpoint"""
    r = requests.get(f"{BACKEND_URL}/api/v1/task-os/status", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            data.get("status") in ["operational", "initializing"])

def test_task_os_frontend() -> bool:
    """Test Task OS frontend availability"""
    r = requests.get(TASK_OS_URL, timeout=10)
    return r.status_code == 200

def test_myroofgenius_frontend() -> bool:
    """Test MyRoofGenius frontend"""
    r = requests.get(MYROOFGENIUS_URL, timeout=10, allow_redirects=True)
    return r.status_code in [200, 307]  # 307 is temporary redirect

def test_products_api() -> bool:
    """Test products API"""
    r = requests.get(f"{BACKEND_URL}/api/v1/products", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "products" in data and
            len(data["products"]) > 0)

def test_blog_api() -> bool:
    """Test blog API"""
    r = requests.get(f"{BACKEND_URL}/api/v1/blog/posts", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "posts" in data)

def test_analytics_api() -> bool:
    """Test analytics API"""
    r = requests.get(f"{BACKEND_URL}/api/v1/analytics/dashboard", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            "metrics" in data)

def test_aurea_status() -> bool:
    """Test AUREA AI status"""
    r = requests.get(f"{BACKEND_URL}/api/v1/aurea/status", timeout=10)
    data = r.json()
    return (r.status_code == 200 and 
            data.get("ai_active") == True)

def main():
    """Run all tests"""
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}COMPREHENSIVE SYSTEM TEST - TASK OS & AI INTEGRATION")
    print(f"{Fore.MAGENTA}Time: {datetime.now().isoformat()}")
    print(f"{Fore.MAGENTA}{'='*60}")
    
    tester = SystemTester()
    
    # Backend Health Tests
    tester.section("BACKEND HEALTH TESTS")
    tester.test("Backend Health Check", test_backend_health)
    tester.test("Products API", test_products_api)
    tester.test("Blog API", test_blog_api)
    tester.test("Analytics API", test_analytics_api)
    
    # AI System Tests
    tester.section("AI SYSTEM TESTS")
    tester.test("AI Status", test_ai_status)
    tester.test("AI Revenue Analysis", test_ai_revenue)
    tester.test("AI Command Execution", test_ai_command)
    tester.test("AI System Health", test_ai_system_health)
    tester.test("Self-Healing Trigger", test_self_healing)
    tester.test("AUREA Status", test_aurea_status)
    
    # Task OS Tests
    tester.section("TASK OS TESTS")
    tester.test("Task OS Backend Status", test_task_os_status)
    tester.test("Task OS Frontend", test_task_os_frontend)
    
    # Frontend Tests
    tester.section("FRONTEND TESTS")
    tester.test("MyRoofGenius Frontend", test_myroofgenius_frontend)
    
    # Database/CenterPoint Check (informational)
    tester.section("DATA STATUS")
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/task-os/status", timeout=10)
        data = r.json()
        if data.get("data"):
            cp_customers = data["data"].get("centerpoint_customers", 0)
            total_customers = data["data"].get("total_customers", 0)
            cp_files = data["data"].get("centerpoint_files", 0)
            
            if cp_customers == 0:
                tester.warning(f"No CenterPoint customers synced (0/{total_customers})")
            else:
                print(f"{Fore.GREEN}✅ CenterPoint customers: {cp_customers}")
                
            if cp_files == 0:
                tester.warning("No CenterPoint files synced")
            else:
                print(f"{Fore.GREEN}✅ CenterPoint files: {cp_files}")
    except:
        tester.warning("Could not check CenterPoint data status")
    
    # Summary
    tester.section("TEST SUMMARY")
    total = tester.results["passed"] + tester.results["failed"]
    success_rate = (tester.results["passed"] / total * 100) if total > 0 else 0
    
    print(f"{Fore.GREEN}Passed: {tester.results['passed']}")
    print(f"{Fore.RED}Failed: {tester.results['failed']}")
    print(f"{Fore.YELLOW}Warnings: {tester.results['warnings']}")
    print(f"{Fore.CYAN}Success Rate: {success_rate:.1f}%")
    
    # Overall Status
    print(f"\n{Fore.MAGENTA}{'='*60}")
    if success_rate >= 90:
        print(f"{Fore.GREEN}🎉 SYSTEM STATUS: FULLY OPERATIONAL")
        print(f"{Fore.GREEN}All AI and Task OS systems are working!")
    elif success_rate >= 70:
        print(f"{Fore.YELLOW}⚠️  SYSTEM STATUS: PARTIALLY OPERATIONAL")
        print(f"{Fore.YELLOW}Most systems working but some issues detected")
    else:
        print(f"{Fore.RED}❌ SYSTEM STATUS: DEGRADED")
        print(f"{Fore.RED}Multiple system failures detected")
    print(f"{Fore.MAGENTA}{'='*60}")
    
    # Recommendations
    if tester.results["warnings"] > 0:
        print(f"\n{Fore.YELLOW}RECOMMENDATIONS:")
        if cp_customers == 0:
            print(f"{Fore.YELLOW}• Run CenterPoint sync to populate production data")
        if tester.results["failed"] > 0:
            print(f"{Fore.YELLOW}• Review failed tests and fix issues")
    
    return success_rate >= 70

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test failed with error: {e}")
        exit(1)