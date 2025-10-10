#!/usr/bin/env python3
"""
REAL Production System Test - No fake data
Tests what's ACTUALLY deployed and working
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(path, method="GET", data=None):
    """Test an endpoint and return status"""
    try:
        url = f"{BASE_URL}{path}"
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        
        return {
            "path": path,
            "status": response.status_code,
            "working": response.status_code in [200, 201],
            "data": response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            "path": path,
            "status": "error",
            "working": False,
            "error": str(e)
        }

def main():
    print("=" * 60)
    print("🔍 REAL PRODUCTION SYSTEM TEST")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test critical endpoints
    endpoints = [
        # Health
        ("/api/v1/health", "GET"),
        
        # Revenue System
        ("/api/v1/revenue/status", "GET"),
        ("/api/v1/revenue/config", "GET"),
        ("/api/v1/revenue/stats", "GET"),
        
        # Environment Master
        ("/api/v1/env/health", "GET"),
        ("/api/v1/env/all", "GET"),
        
        # Products
        ("/api/v1/products", "GET"),
        ("/api/v1/products/public", "GET"),
        
        # Memory System
        ("/api/v1/memory/recent", "GET"),
        
        # AI Systems
        ("/api/v1/aurea/status", "GET"),
        ("/api/v1/ai/status", "GET"),
        
        # Estimates
        ("/api/v1/estimates/quick-price/2000", "GET"),
    ]
    
    results = []
    for endpoint, method in endpoints:
        result = test_endpoint(endpoint, method)
        results.append(result)
        
        status_icon = "✅" if result["working"] else "❌"
        print(f"{status_icon} {endpoint}: {result['status']}")
        
        if result["working"] and result.get("data"):
            # Show key data points
            if "revenue" in endpoint:
                if isinstance(result["data"], dict):
                    for key, value in result["data"].items():
                        if key != "detail":
                            print(f"    {key}: {value}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    working = sum(1 for r in results if r["working"])
    total = len(results)
    percentage = (working / total) * 100
    
    print(f"Working Endpoints: {working}/{total} ({percentage:.1f}%)")
    
    # Check what's actually operational
    print("\n🎯 OPERATIONAL SYSTEMS:")
    operational = []
    
    if any(r["working"] for r in results if "revenue" in r["path"]):
        operational.append("✅ Revenue System")
    if any(r["working"] for r in results if "env" in r["path"]):
        operational.append("✅ Environment Management")
    if any(r["working"] for r in results if "products" in r["path"]):
        operational.append("✅ Product Catalog")
    if any(r["working"] for r in results if "memory" in r["path"]):
        operational.append("✅ Persistent Memory")
    if any(r["working"] for r in results if "aurea" in r["path"] or "ai" in r["path"]):
        operational.append("✅ AI Systems")
    
    for system in operational:
        print(f"  {system}")
    
    # Revenue Readiness Check
    print("\n💰 REVENUE GENERATION READINESS:")
    revenue_ready = []
    
    revenue_status = next((r for r in results if r["path"] == "/api/v1/revenue/status"), None)
    if revenue_status and revenue_status["working"]:
        data = revenue_status.get("data", {})
        if data.get("stripe_configured"):
            revenue_ready.append("✅ Stripe Configured")
        if data.get("live_key_available"):
            revenue_ready.append("✅ Live Keys Available")
        if data.get("automation_enabled"):
            revenue_ready.append("✅ Automation Enabled")
    
    products = next((r for r in results if "products" in r["path"] and r["working"]), None)
    if products:
        revenue_ready.append("✅ Products Available")
    
    for item in revenue_ready:
        print(f"  {item}")
    
    if len(revenue_ready) >= 3:
        print("\n🚀 SYSTEM IS READY TO PROCESS REAL PAYMENTS!")
    else:
        print("\n⚠️ Additional configuration needed for revenue generation")
    
    print("=" * 60)

if __name__ == "__main__":
    main()