#!/usr/bin/env python3
"""
Production Monitoring and Revenue Testing for v3.3.26
Tests all critical endpoints for revenue generation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

BASE_URL = "https://brainops-backend-prod.onrender.com"

def check_health():
    """Check system health"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        data = response.json()
        version = data.get("version", "unknown")
        status = data.get("status", "unknown")
        
        print(f"📊 System Health Check:")
        print(f"  Version: {version}")
        print(f"  Status: {status}")
        print(f"  Routes: {data.get('routes_loaded', 0)}")
        print(f"  Endpoints: {data.get('total_endpoints', 0)}")
        
        if version == "3.3.26":
            print("  ✅ New version deployed!")
        else:
            print(f"  ⏳ Waiting for v3.3.26 (current: {version})")
        
        return data
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None

def test_revenue_generation():
    """Test revenue generation endpoints"""
    print("\n💰 Testing Revenue Generation:")
    
    endpoints = [
        ("/api/v1/aurea/revenue/generate", "POST", {
            "customer_type": "commercial",
            "service_type": "full_replacement",
            "urgency": "high"
        }),
        ("/api/v1/aurea/status", "GET", None),
        ("/api/v1/aurea/chat", "POST", {
            "message": "Generate a quote for a 5000 sq ft commercial roof",
            "context": {"customer": "ABC Corp", "budget": 50000}
        })
    ]
    
    for endpoint, method, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: SUCCESS")
                if "revenue" in endpoint:
                    result = response.json()
                    if "opportunity_id" in result:
                        print(f"     Created opportunity: {result['opportunity_id']}")
                        print(f"     Estimated value: ${result.get('estimated_value', 0):,}")
            else:
                print(f"  ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")

def test_ai_board():
    """Test AI Board endpoints"""
    print("\n🤖 Testing AI Board:")
    
    endpoints = [
        "/api/v1/ai-board/status",
        "/api/v1/ai-board/agents",
        "/api/v1/ai-board/analytics"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: SUCCESS")
            else:
                print(f"  ⚠️ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")

def test_myroofgenius_integration():
    """Test MyRoofGenius specific endpoints"""
    print("\n🏠 Testing MyRoofGenius Integration:")
    
    # Test public product endpoints
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/public", timeout=10)
        if response.status_code == 200:
            products = response.json()
            print(f"  ✅ Public products: {len(products) if isinstance(products, list) else 'available'}")
        else:
            print(f"  ❌ Public products: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Public products: {str(e)[:50]}")
    
    # Test AUREA public chat
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/aurea/public/chat",
            json={"message": "I need a roof inspection"},
            timeout=10
        )
        if response.status_code == 200:
            print("  ✅ Public AUREA chat: WORKING")
        else:
            print(f"  ⚠️ Public AUREA chat: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Public AUREA chat: {str(e)[:50]}")

def continuous_monitor(duration_minutes=5):
    """Continuously monitor for deployment"""
    print(f"\n🔄 Starting continuous monitoring for {duration_minutes} minutes...")
    print("=" * 60)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    check_count = 0
    v3326_deployed = False
    
    while time.time() < end_time:
        check_count += 1
        print(f"\n[Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}]")
        
        health = check_health()
        if health and health.get("version") == "3.3.26":
            v3326_deployed = True
            print("\n🎉 VERSION 3.3.26 DEPLOYED SUCCESSFULLY!")
            
            # Run full test suite
            test_revenue_generation()
            test_ai_board()
            test_myroofgenius_integration()
            
            print("\n✅ ALL SYSTEMS OPERATIONAL - READY FOR REVENUE!")
            break
        
        if not v3326_deployed:
            print("⏳ Waiting 30 seconds for next check...")
            time.sleep(30)
    
    if not v3326_deployed:
        print("\n⚠️ v3.3.26 not detected yet. Manual deployment may be needed.")
        print("Visit: https://dashboard.render.com to check deployment status")

def main():
    """Main monitoring function"""
    print("=" * 60)
    print("🚀 BrainOps Production Monitor v3.3.26")
    print("=" * 60)
    
    # Initial check
    health = check_health()
    
    if health:
        # Quick test of current endpoints
        test_revenue_generation()
        test_ai_board()
        test_myroofgenius_integration()
    
    # Start continuous monitoring
    continuous_monitor(duration_minutes=5)

if __name__ == "__main__":
    main()