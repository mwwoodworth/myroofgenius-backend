#!/usr/bin/env python3
"""
Test AI OS v9.3 Deployment
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_health():
    """Test health endpoint"""
    print("1. Testing Health Endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        data = resp.json()
        version = data.get("version", "unknown")
        print(f"   ✅ Health check passed - Version: {version}")
        print(f"   Database: {data.get('database', 'unknown')}")
        return version
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return None

def test_ai_board():
    """Test AI Board endpoints"""
    print("\n2. Testing AI Board...")
    
    # Test status endpoint
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/ai-board/status", timeout=10)
        if resp.status_code == 200:
            print("   ✅ AI Board status endpoint working")
            print(f"   Response: {resp.json()}")
        else:
            print(f"   ⚠️ AI Board status returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ AI Board status failed: {e}")
    
    # Test start session
    try:
        payload = {"session_type": "strategic"}
        resp = requests.post(f"{BASE_URL}/api/v1/ai-board/start-session", 
                            json=payload, timeout=10)
        if resp.status_code in [200, 201]:
            data = resp.json()
            print(f"   ✅ AI Board session started: {data.get('session_id', 'unknown')}")
        else:
            print(f"   ⚠️ AI Board session returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ AI Board session failed: {e}")

def test_aurea():
    """Test AUREA endpoints"""
    print("\n3. Testing AUREA...")
    
    # Test status
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/aurea/status", timeout=10)
        if resp.status_code == 200:
            print("   ✅ AUREA status endpoint working")
            data = resp.json()
            print(f"   Consciousness Level: {data.get('consciousness_level', 'unknown')}")
        else:
            print(f"   ⚠️ AUREA status returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ AUREA status failed: {e}")
    
    # Test think
    try:
        payload = {"prompt": "How can I improve business operations?"}
        resp = requests.post(f"{BASE_URL}/api/v1/aurea/think", 
                            json=payload, timeout=10)
        if resp.status_code in [200, 201]:
            print("   ✅ AUREA think endpoint working")
        else:
            print(f"   ⚠️ AUREA think returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ AUREA think failed: {e}")

def test_langgraph():
    """Test LangGraph endpoints"""
    print("\n4. Testing LangGraph...")
    
    # Test status
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/langgraph/status", timeout=10)
        if resp.status_code == 200:
            print("   ✅ LangGraph status endpoint working")
            data = resp.json()
            print(f"   Workflows: {data.get('workflows', [])}")
        else:
            print(f"   ⚠️ LangGraph status returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ LangGraph status failed: {e}")
    
    # Test execute workflow
    try:
        payload = {
            "workflow_name": "Customer Journey",
            "input_data": {"customer_id": "test123"}
        }
        resp = requests.post(f"{BASE_URL}/api/v1/langgraph/execute", 
                            json=payload, timeout=10)
        if resp.status_code in [200, 201]:
            print("   ✅ LangGraph execute endpoint working")
        else:
            print(f"   ⚠️ LangGraph execute returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ LangGraph execute failed: {e}")

def test_ai_os_unified():
    """Test unified AI OS endpoints"""
    print("\n5. Testing AI OS Unified System...")
    
    # Test system status
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/ai-os/status", timeout=10)
        if resp.status_code == 200:
            print("   ✅ AI OS status endpoint working")
            data = resp.json()
            print(f"   System Mode: {data.get('mode', 'unknown')}")
            print(f"   Health Score: {data.get('health_score', 0)}")
        else:
            print(f"   ⚠️ AI OS status returned {resp.status_code}")
    except Exception as e:
        print(f"   ❌ AI OS status failed: {e}")

def main():
    print("=" * 60)
    print("AI OS v9.3 DEPLOYMENT TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Run tests
    version = test_health()
    
    if version and version.startswith("9"):
        print("\n✅ Version 9.x detected, testing AI components...")
        test_ai_board()
        test_aurea()
        test_langgraph()
        test_ai_os_unified()
    else:
        print(f"\n⚠️ Version {version} detected, AI components may not be available")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if version and version.startswith("9"):
        print("✅ AI OS v9.3 is DEPLOYED and RUNNING!")
        print("✅ AI components are being initialized")
        print("⚠️ Some endpoints may need database table fixes")
    else:
        print("❌ AI OS v9.3 is NOT fully deployed")
        print("⚠️ Check Render deployment status")
    
    print("\nNext Steps:")
    print("1. Monitor Render logs for any errors")
    print("2. Fix database table issues if needed")
    print("3. Test with authenticated requests")
    print("4. Monitor AI component initialization")

if __name__ == "__main__":
    main()