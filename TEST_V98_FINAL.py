#!/usr/bin/env python3
"""
Final test for v9.8 - Should be 100% operational
"""

import requests
import time
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def wait_and_test():
    """Wait for v9.8 and test"""
    print("=" * 60)
    print("FINAL TEST FOR v9.8 - TARGET: 100% OPERATIONAL")
    print("=" * 60)
    
    # Wait for deployment
    for i in range(10):
        try:
            resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            version = resp.json().get("version", "unknown")
            print(f"Checking... Version: {version}")
            
            if version == "9.8":
                print("\n✅ v9.8 is deployed!\n")
                break
        except:
            pass
        time.sleep(15)
    
    # Test all endpoints
    endpoints = [
        ("GET", "/api/v1/health", None, "Health Check"),
        ("GET", "/api/v1/ai-board/status", None, "AI Board Status"),
        ("POST", "/api/v1/ai-board/start-session", {"session_type": "strategic"}, "AI Board Session"),
        ("POST", "/api/v1/ai-board/make-decision", {"context": {"type": "test"}}, "AI Board Decision"),
        ("GET", "/api/v1/aurea/status", None, "AUREA Status"),
        ("POST", "/api/v1/aurea/initialize", {}, "AUREA Initialize"),
        ("POST", "/api/v1/aurea/think", {"prompt": "test"}, "AUREA Think"),
        ("POST", "/api/v1/aurea/converse", {"message": "hello"}, "AUREA Converse"),
        ("GET", "/api/v1/langgraph/status", None, "LangGraph Status"),
        ("POST", "/api/v1/langgraph/execute", {"workflow_name": "Customer Journey", "input_data": {}}, "LangGraph Execute"),
        ("GET", "/api/v1/ai-os/status", None, "AI OS Status"),
        ("GET", "/api/v1/customers", None, "Customers List"),
        ("GET", "/api/v1/jobs", None, "Jobs List"),
        ("GET", "/api/v1/estimates", None, "Estimates List"),
        ("GET", "/api/v1/invoices", None, "Invoices List"),
        ("GET", "/api/v1/products/public", None, "Public Products"),
        ("POST", "/api/v1/aurea/public/chat", {"message": "hello"}, "Public AUREA Chat"),
    ]
    
    working = 0
    total = len(endpoints)
    
    print("Testing all endpoints:")
    print("-" * 40)
    
    for method, path, payload, name in endpoints:
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{path}", timeout=10)
            else:
                resp = requests.post(f"{BASE_URL}{path}", json=payload, timeout=10)
            
            if resp.status_code in [200, 201]:
                print(f"✅ {name}")
                working += 1
            else:
                print(f"❌ {name}: {resp.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error")
    
    print("\n" + "=" * 60)
    success_rate = (working/total*100)
    print(f"RESULTS: {working}/{total} endpoints working")
    print(f"SUCCESS RATE: {success_rate:.0f}%")
    print("=" * 60)
    
    if success_rate == 100:
        print("\n🎉🎉🎉 PERFECT! 100% OPERATIONAL! 🎉🎉🎉")
        print("✅ ALL SYSTEMS GO!")
        print("🚀 Ready to leverage DevOps AI agents!")
    elif success_rate >= 90:
        print("\n✅ Nearly there! System is highly operational")
    elif success_rate >= 80:
        print("\n⚠️ Good progress, but needs more work")
    else:
        print("\n❌ Still have issues to fix")
    
    return success_rate

if __name__ == "__main__":
    rate = wait_and_test()
    
    if rate == 100:
        print("\n" + "🎊" * 20)
        print("BACKEND IS NOW LOCKED IN!")
        print("We can now use our DevOps AI agents to:")
        print("- Automate deployments")
        print("- Monitor system health")
        print("- Self-heal issues")
        print("- Scale operations")
        print("🎊" * 20)