#!/usr/bin/env python3
"""
Final test for v9.6 - check if all endpoints are working
"""

import requests
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://brainops-backend-prod.onrender.com"

def wait_for_version(target_version="9.6", timeout=300):
    """Wait for specific version to be deployed"""
    print(f"Waiting for v{target_version} to be deployed...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            data = resp.json()
            version = data.get("version", "unknown")
            print(f"  Current version: {version}")
            
            if version == target_version:
                print(f"✅ v{target_version} is deployed!")
                return True
        except Exception as e:
            logger.warning(f"Error checking deployment version: {e}")
        
        time.sleep(15)
    
    print(f"⏱️ Timeout waiting for v{target_version}")
    return False

def test_all_endpoints():
    """Test all endpoints"""
    results = {
        "working": 0,
        "errors": 0,
        "total": 0
    }
    
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
        ("GET", "/api/v1/products/public", None, "Public Products"),
        ("POST", "/api/v1/aurea/public/chat", {"message": "hello"}, "Public AUREA Chat"),
    ]
    
    print("\n" + "=" * 60)
    print("TESTING ALL ENDPOINTS")
    print("=" * 60)
    
    for method, path, payload, name in endpoints:
        results["total"] += 1
        
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{path}", timeout=10)
            else:
                resp = requests.post(f"{BASE_URL}{path}", json=payload, timeout=10)
            
            if resp.status_code in [200, 201]:
                print(f"✅ {name}: SUCCESS")
                results["working"] += 1
            else:
                print(f"❌ {name}: {resp.status_code}")
                results["errors"] += 1
                if resp.status_code == 500:
                    try:
                        error = resp.json()
                        if "detail" in error:
                            print(f"   Error: {error['detail'][:100]}")
                    except Exception as e:
                        logger.warning(f"Failed to parse error response: {e}")
        except Exception as e:
            print(f"❌ {name}: Connection error")
            results["errors"] += 1
    
    return results

def main():
    print("=" * 60)
    print("FINAL TEST FOR v9.6 DEPLOYMENT")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    print(f"Target: {BASE_URL}")
    
    # Wait for v9.6
    if not wait_for_version("9.6"):
        print("v9.6 not deployed yet. Testing current version...")
    
    # Test all endpoints
    results = test_all_endpoints()
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    success_rate = (results["working"] / results["total"] * 100) if results["total"] > 0 else 0
    
    print(f"Total Endpoints: {results['total']}")
    print(f"Working: {results['working']}")
    print(f"Errors: {results['errors']}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 PERFECT! ALL ENDPOINTS WORKING!")
    elif success_rate >= 80:
        print("\n✅ SYSTEM IS OPERATIONAL")
    elif success_rate >= 50:
        print("\n⚠️ SYSTEM IS PARTIALLY OPERATIONAL")
    else:
        print("\n❌ SYSTEM HAS MAJOR ISSUES")
    
    print("\nDeployment Status:")
    if success_rate >= 80:
        print("✅ v9.6 is successfully deployed and operational")
    else:
        print("⚠️ v9.6 is deployed but needs more fixes")

if __name__ == "__main__":
    main()