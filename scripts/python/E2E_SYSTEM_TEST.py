#!/usr/bin/env python3
"""
Complete End-to-End System Test
Tests all components and reports what's working
"""

import requests
import json
import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def test_complete_system():
    print("\n" + "="*60)
    print("🚀 COMPLETE E2E SYSTEM TEST")
    print("="*60)
    
    results = {
        "backend": {},
        "frontends": {},
        "database": {},
        "integrations": {},
        "overall": "UNKNOWN"
    }
    
    # Test Backend API
    print("\n1️⃣ Testing Backend API...")
    try:
        r = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health")
        if r.status_code == 200:
            results["backend"]["health"] = "✅ PASS"
            version = r.json().get("version", "unknown")
            results["backend"]["version"] = version
            print(f"   ✅ Health check passed (v{version})")
        else:
            results["backend"]["health"] = "❌ FAIL"
            print(f"   ❌ Health check failed ({r.status_code})")
    except Exception as e:
        results["backend"]["health"] = "❌ ERROR"
        print(f"   ❌ Backend unreachable: {e}")
    
    # Test CRM endpoints
    try:
        r = requests.get("https://brainops-backend-prod.onrender.com/api/v1/crm/customers")
        if r.status_code == 200:
            results["backend"]["crm"] = "✅ PASS"
            print("   ✅ CRM endpoints working")
        else:
            results["backend"]["crm"] = "❌ FAIL"
            print(f"   ❌ CRM endpoints failed ({r.status_code})")
    except:
        results["backend"]["crm"] = "❌ ERROR"
    
    # Test Revenue endpoints
    revenue_working = 0
    revenue_total = 7
    endpoints = [
        "/api/v1/test-revenue/",
        "/api/v1/ai-estimation/analyze",
        "/api/v1/stripe-revenue/products",
        "/api/v1/customer-pipeline/leads",
        "/api/v1/landing-pages/",
        "/api/v1/google-ads/campaigns",
        "/api/v1/revenue-dashboard/metrics"
    ]
    
    for endpoint in endpoints:
        try:
            r = requests.get(f"https://brainops-backend-prod.onrender.com{endpoint}", timeout=2)
            if r.status_code in [200, 201]:
                revenue_working += 1
        except:
            pass
    
    results["backend"]["revenue"] = f"{revenue_working}/{revenue_total} working"
    print(f"   📊 Revenue endpoints: {revenue_working}/{revenue_total} working")
    
    # Test Frontends
    print("\n2️⃣ Testing Frontends...")
    frontends = {
        "MyRoofGenius": "https://myroofgenius.com",
        "WeatherCraft ERP": "https://weathercraft-erp.vercel.app",
        "Task OS": "https://brainops-task-os.vercel.app"
    }
    
    for name, url in frontends.items():
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                results["frontends"][name] = "✅ PASS"
                print(f"   ✅ {name}: Operational")
            else:
                results["frontends"][name] = f"⚠️ {r.status_code}"
                print(f"   ⚠️ {name}: Status {r.status_code}")
        except:
            results["frontends"][name] = "❌ ERROR"
            print(f"   ❌ {name}: Unreachable")
    
    # Test Database
    print("\n3️⃣ Testing Database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM customers")
        customer_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cur.fetchone()[0]
        
        results["database"]["status"] = "✅ CONNECTED"
        results["database"]["tables"] = table_count
        results["database"]["customers"] = customer_count
        
        print(f"   ✅ Database connected ({table_count} tables, {customer_count} customers)")
        
        cur.close()
        conn.close()
    except Exception as e:
        results["database"]["status"] = "❌ ERROR"
        print(f"   ❌ Database error: {e}")
    
    # Test Integrations
    print("\n4️⃣ Testing Integrations...")
    
    # Stripe
    try:
        r = requests.get("https://api.stripe.com/v1/products", 
                        auth=("sk_test_placeholder", ""))
        if r.status_code == 401:  # Expected with test key
            results["integrations"]["stripe"] = "🔑 Needs real key"
            print("   🔑 Stripe: Needs production key")
        else:
            results["integrations"]["stripe"] = "✅ Connected"
    except:
        results["integrations"]["stripe"] = "❌ ERROR"
    
    # Calculate overall health
    total_tests = 0
    passed_tests = 0
    
    for category in results.values():
        if isinstance(category, dict):
            for test, result in category.items():
                total_tests += 1
                if "✅" in str(result) or "PASS" in str(result):
                    passed_tests += 1
    
    health_percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "="*60)
    print("📊 SYSTEM HEALTH SUMMARY")
    print("="*60)
    
    if health_percentage >= 90:
        results["overall"] = "✅ EXCELLENT"
        status = "EXCELLENT"
    elif health_percentage >= 70:
        results["overall"] = "🟡 GOOD"
        status = "GOOD"
    elif health_percentage >= 50:
        results["overall"] = "⚠️ DEGRADED"
        status = "DEGRADED"
    else:
        results["overall"] = "❌ CRITICAL"
        status = "CRITICAL"
    
    print(f"\n🎯 Overall System Health: {health_percentage:.1f}% - {status}")
    print(f"   Tests Passed: {passed_tests}/{total_tests}")
    
    # Critical Issues
    print("\n⚠️ CRITICAL ISSUES:")
    if revenue_working < revenue_total:
        print(f"   • Revenue system incomplete ({revenue_working}/{revenue_total} endpoints)")
    if results["database"].get("customers", 0) < 100:
        print(f"   • Low customer data ({results['database'].get('customers', 0)} records)")
    if "6.0" in str(results["backend"].get("version", "")):
        print("   • Backend not updated (still v6.0, should be v6.11)")
    
    # Save results
    with open("/home/mwwoodworth/code/E2E_TEST_RESULTS.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "health_percentage": health_percentage,
            "status": status,
            "results": results
        }, f, indent=2)
    
    print("\n✅ Test results saved to E2E_TEST_RESULTS.json")
    return health_percentage

if __name__ == "__main__":
    health = test_complete_system()
    exit(0 if health >= 70 else 1)