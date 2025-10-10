#!/usr/bin/env python3
"""
Create comprehensive Perplexity audit dashboard
v3.1.206
"""

import requests
import json
from datetime import datetime
import time

API_URL = "https://brainops-backend-prod.onrender.com"

def run_comprehensive_audit():
    """Run comprehensive system audit for Perplexity"""
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": None,
        "categories": {},
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "system_status": "unknown"
    }
    
    # 1. Backend Health Check
    print("🏥 Testing Backend Health...")
    try:
        resp = requests.get(f"{API_URL}/api/v1/health", timeout=10)
        if resp.status_code == 200:
            health_data = resp.json()
            results["version"] = health_data.get("version", "unknown")
            results["categories"]["backend"] = {
                "status": "operational",
                "tests": [{"name": "API Health", "status": "passed", "details": f"v{results['version']}"}]
            }
            results["passed_tests"] += 1
        else:
            results["categories"]["backend"] = {
                "status": "down",
                "tests": [{"name": "API Health", "status": "failed", "details": f"Status {resp.status_code}"}]
            }
            results["failed_tests"] += 1
    except Exception as e:
        results["categories"]["backend"] = {
            "status": "error",
            "tests": [{"name": "API Health", "status": "failed", "details": str(e)}]
        }
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    
    # 2. Authentication Tests
    print("\n🔐 Testing Authentication...")
    auth_tests = []
    access_token = None
    
    # Test Registration
    try:
        test_email = f"perplexity_test_{int(time.time())}@example.com"
        resp = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json={
                "email": test_email,
                "password": "TestPassword123!",
                "full_name": "Perplexity Tester"
            },
            timeout=10
        )
        if resp.status_code == 200:
            auth_tests.append({"name": "User Registration", "status": "passed", "details": f"Created {test_email}"})
            results["passed_tests"] += 1
        else:
            auth_tests.append({"name": "User Registration", "status": "failed", "details": f"Status {resp.status_code}"})
            results["failed_tests"] += 1
    except Exception as e:
        auth_tests.append({"name": "User Registration", "status": "failed", "details": str(e)})
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    
    # Test Login
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={
                "email": "test@brainops.com",
                "password": "TestPassword123!"
            },
            timeout=10
        )
        if resp.status_code == 200:
            tokens = resp.json()
            access_token = tokens.get("access_token")
            auth_tests.append({"name": "User Login", "status": "passed", "details": "Login successful"})
            results["passed_tests"] += 1
        else:
            auth_tests.append({"name": "User Login", "status": "failed", "details": f"Status {resp.status_code}"})
            results["failed_tests"] += 1
    except Exception as e:
        auth_tests.append({"name": "User Login", "status": "failed", "details": str(e)})
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    results["categories"]["authentication"] = {
        "status": "operational" if all(t["status"] == "passed" for t in auth_tests) else "degraded",
        "tests": auth_tests
    }
    
    # 3. Protected Routes
    if access_token:
        print("\n🛡️ Testing Protected Routes...")
        headers = {"Authorization": f"Bearer {access_token}"}
        protected_tests = []
        
        protected_endpoints = [
            ("GET", "/api/v1/users/me", "User Profile"),
            ("GET", "/api/v1/memory/recent", "Memory Recent"),
            ("GET", "/api/v1/projects", "Projects List"),
            ("GET", "/api/v1/tasks", "Tasks List")
        ]
        
        for method, endpoint, name in protected_endpoints:
            try:
                resp = requests.request(method, f"{API_URL}{endpoint}", headers=headers, timeout=10)
                if resp.status_code == 200:
                    protected_tests.append({"name": name, "status": "passed", "details": "Accessible"})
                    results["passed_tests"] += 1
                else:
                    protected_tests.append({"name": name, "status": "failed", "details": f"Status {resp.status_code}"})
                    results["failed_tests"] += 1
            except Exception as e:
                protected_tests.append({"name": name, "status": "failed", "details": str(e)})
                results["failed_tests"] += 1
            
            results["total_tests"] += 1
        
        results["categories"]["protected_routes"] = {
            "status": "operational" if all(t["status"] == "passed" for t in protected_tests) else "degraded",
            "tests": protected_tests
        }
    
    # 4. AUREA AI
    if access_token:
        print("\n🤖 Testing AUREA AI...")
        aurea_tests = []
        
        try:
            resp = requests.post(
                f"{API_URL}/api/v1/aurea/chat",
                headers=headers,
                json={"message": "Hello AUREA, are you operational?"},
                timeout=20
            )
            if resp.status_code == 200:
                response_data = resp.json()
                if response_data.get("response"):
                    aurea_tests.append({"name": "AUREA Chat", "status": "passed", "details": "AI responding"})
                    results["passed_tests"] += 1
                else:
                    aurea_tests.append({"name": "AUREA Chat", "status": "failed", "details": "Empty response"})
                    results["failed_tests"] += 1
            else:
                aurea_tests.append({"name": "AUREA Chat", "status": "failed", "details": f"Status {resp.status_code}"})
                results["failed_tests"] += 1
        except Exception as e:
            aurea_tests.append({"name": "AUREA Chat", "status": "failed", "details": str(e)})
            results["failed_tests"] += 1
        
        results["total_tests"] += 1
        
        # Test AUREA Status
        try:
            resp = requests.get(f"{API_URL}/api/v1/aurea/status", timeout=10)
            if resp.status_code == 200:
                aurea_tests.append({"name": "AUREA Status", "status": "passed", "details": "System operational"})
                results["passed_tests"] += 1
            else:
                aurea_tests.append({"name": "AUREA Status", "status": "failed", "details": f"Status {resp.status_code}"})
                results["failed_tests"] += 1
        except Exception as e:
            aurea_tests.append({"name": "AUREA Status", "status": "failed", "details": str(e)})
            results["failed_tests"] += 1
        
        results["total_tests"] += 1
        
        results["categories"]["aurea_ai"] = {
            "status": "operational" if all(t["status"] == "passed" for t in aurea_tests) else "degraded",
            "tests": aurea_tests
        }
    
    # 5. Calculators
    print("\n🧮 Testing Calculators...")
    calc_tests = []
    
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/calculators/material",
            json={
                "roof_area": 1500,
                "roof_type": "shingle",
                "pitch": 4.0,
                "waste_factor": 0.1
            },
            timeout=10
        )
        if resp.status_code == 200:
            calc_tests.append({"name": "Material Calculator", "status": "passed", "details": "Calculation successful"})
            results["passed_tests"] += 1
        else:
            calc_tests.append({"name": "Material Calculator", "status": "failed", "details": f"Status {resp.status_code}"})
            results["failed_tests"] += 1
    except Exception as e:
        calc_tests.append({"name": "Material Calculator", "status": "failed", "details": str(e)})
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/calculators/labor",
            json={
                "roof_area": 1500,
                "roof_type": "shingle",
                "complexity": "medium",
                "crew_size": 4
            },
            timeout=10
        )
        if resp.status_code == 200:
            calc_tests.append({"name": "Labor Calculator", "status": "passed", "details": "Calculation successful"})
            results["passed_tests"] += 1
        else:
            calc_tests.append({"name": "Labor Calculator", "status": "failed", "details": f"Status {resp.status_code}"})
            results["failed_tests"] += 1
    except Exception as e:
        calc_tests.append({"name": "Labor Calculator", "status": "failed", "details": str(e)})
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    
    results["categories"]["calculators"] = {
        "status": "operational" if all(t["status"] == "passed" for t in calc_tests) else "degraded",
        "tests": calc_tests
    }
    
    # 6. Memory System
    if access_token:
        print("\n💾 Testing Memory System...")
        memory_tests = []
        
        # Create Memory
        try:
            resp = requests.post(
                f"{API_URL}/api/v1/memory/create",
                headers=headers,
                json={
                    "title": "Perplexity Audit Test",
                    "content": "Testing memory persistence for audit",
                    "memory_type": "test",
                    "role": "system"
                },
                timeout=10
            )
            if resp.status_code == 200:
                memory_tests.append({"name": "Create Memory", "status": "passed", "details": "Memory created"})
                results["passed_tests"] += 1
            else:
                memory_tests.append({"name": "Create Memory", "status": "failed", "details": f"Status {resp.status_code}"})
                results["failed_tests"] += 1
        except Exception as e:
            memory_tests.append({"name": "Create Memory", "status": "failed", "details": str(e)})
            results["failed_tests"] += 1
        
        results["total_tests"] += 1
        
        # Search Memory
        try:
            resp = requests.post(
                f"{API_URL}/api/v1/memory/search",
                headers=headers,
                params={"query": "audit", "limit": 10},
                timeout=10
            )
            if resp.status_code == 200:
                memory_tests.append({"name": "Search Memory", "status": "passed", "details": "Search functional"})
                results["passed_tests"] += 1
            else:
                memory_tests.append({"name": "Search Memory", "status": "failed", "details": f"Status {resp.status_code}"})
                results["failed_tests"] += 1
        except Exception as e:
            memory_tests.append({"name": "Search Memory", "status": "failed", "details": str(e)})
            results["failed_tests"] += 1
        
        results["total_tests"] += 1
        
        results["categories"]["memory_system"] = {
            "status": "operational" if all(t["status"] == "passed" for t in memory_tests) else "degraded",
            "tests": memory_tests
        }
    
    # 7. Blog API
    print("\n📝 Testing Blog API...")
    blog_tests = []
    
    try:
        resp = requests.get(f"{API_URL}/api/v1/blog?limit=5", timeout=10)
        if resp.status_code == 200:
            blog_tests.append({"name": "List Blog Posts", "status": "passed", "details": "API accessible"})
            results["passed_tests"] += 1
        else:
            blog_tests.append({"name": "List Blog Posts", "status": "failed", "details": f"Status {resp.status_code}"})
            results["failed_tests"] += 1
    except Exception as e:
        blog_tests.append({"name": "List Blog Posts", "status": "failed", "details": str(e)})
        results["failed_tests"] += 1
    
    results["total_tests"] += 1
    
    results["categories"]["blog_api"] = {
        "status": "operational" if all(t["status"] == "passed" for t in blog_tests) else "degraded",
        "tests": blog_tests
    }
    
    # Calculate overall status
    pass_rate = results["passed_tests"] / results["total_tests"] if results["total_tests"] > 0 else 0
    
    if pass_rate >= 0.95:
        results["system_status"] = "operational"
    elif pass_rate >= 0.80:
        results["system_status"] = "degraded"
    elif pass_rate >= 0.50:
        results["system_status"] = "partial_outage"
    else:
        results["system_status"] = "major_outage"
    
    # Generate HTML Dashboard
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MyRoofGenius - Perplexity Audit Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .category {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .passed {{ color: #10b981; font-weight: bold; }}
        .failed {{ color: #ef4444; font-weight: bold; }}
        .test-item {{ padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
        .test-item:last-child {{ border-bottom: none; }}
        .progress {{ background: #e5e7eb; height: 30px; border-radius: 15px; overflow: hidden; }}
        .progress-bar {{ background: #10b981; height: 100%; text-align: center; line-height: 30px; color: white; }}
        .status-operational {{ background: #10b981; color: white; padding: 5px 10px; border-radius: 4px; }}
        .status-degraded {{ background: #f59e0b; color: white; padding: 5px 10px; border-radius: 4px; }}
        .status-down {{ background: #ef4444; color: white; padding: 5px 10px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 MyRoofGenius - Perplexity Audit Dashboard</h1>
        <p>Generated: {results['timestamp']} UTC</p>
        <p>Backend Version: {results['version']}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Overall System Status: <span class="status-{results['system_status']}">{results['system_status'].upper().replace('_', ' ')}</span></h2>
        <div class="progress">
            <div class="progress-bar" style="width: {pass_rate*100:.0f}%">
                {pass_rate*100:.0f}% Operational
            </div>
        </div>
        <p>✅ Passed: <span class="passed">{results['passed_tests']}</span> | 
           ❌ Failed: <span class="failed">{results['failed_tests']}</span> | 
           📊 Total: {results['total_tests']}</p>
    </div>
"""
    
    # Add category results
    for category, data in results["categories"].items():
        status_class = "operational" if data["status"] == "operational" else "degraded" if data["status"] == "degraded" else "down"
        html += f"""
    <div class="category">
        <h3>{category.replace('_', ' ').title()} - <span class="status-{status_class}">{data['status'].upper()}</span></h3>
"""
        for test in data["tests"]:
            icon = "✅" if test["status"] == "passed" else "❌"
            status_class = "passed" if test["status"] == "passed" else "failed"
            html += f"""
        <div class="test-item">
            {icon} <span class="{status_class}">{test['name']}</span>: {test['details']}
        </div>
"""
        html += """
    </div>
"""
    
    # Add recommendations
    html += """
    <div class="category" style="background: #fef2f2; border: 2px solid #ef4444;">
        <h3>📋 Recommendations</h3>
"""
    
    if pass_rate >= 0.95:
        html += """
        <p style="color: #10b981; font-size: 18px;">✅ SYSTEM READY FOR LAUNCH - All critical systems operational!</p>
"""
    else:
        html += """
        <p style="color: #ef4444; font-size: 18px;">⚠️ ISSUES DETECTED - Resolve before launch:</p>
        <ul>
"""
        for category, data in results["categories"].items():
            if data["status"] != "operational":
                failed_tests = [t for t in data["tests"] if t["status"] == "failed"]
                if failed_tests:
                    html += f"            <li><strong>{category.replace('_', ' ').title()}</strong>: "
                    html += ", ".join([t["name"] for t in failed_tests])
                    html += "</li>\n"
        html += """
        </ul>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    # Save dashboard
    with open("perplexity_audit_dashboard_v3206.html", "w") as f:
        f.write(html)
    
    # Print summary
    print("\n" + "="*50)
    print("PERPLEXITY AUDIT SUMMARY")
    print("="*50)
    print(f"Overall Status: {results['system_status'].upper().replace('_', ' ')}")
    print(f"Pass Rate: {pass_rate*100:.1f}%")
    print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
    print("\nCategory Results:")
    for category, data in results["categories"].items():
        passed = len([t for t in data["tests"] if t["status"] == "passed"])
        total = len(data["tests"])
        print(f"  - {category.replace('_', ' ').title()}: {passed}/{total} passed")
    
    print(f"\n✅ Dashboard saved to: perplexity_audit_dashboard_v3206.html")
    
    return results

if __name__ == "__main__":
    run_comprehensive_audit()