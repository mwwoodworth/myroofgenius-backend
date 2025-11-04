#!/usr/bin/env python3
"""
Verify ALL Production Systems are Operational
"""

import requests
import json
from datetime import datetime

def check_system(name, url, expected_status=200):
    """Check if a system is operational"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == expected_status:
            print(f"✅ {name}: OPERATIONAL")
            return True
        else:
            print(f"❌ {name}: Status {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🚀 PRODUCTION SYSTEMS VERIFICATION")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}\n")
    
    systems = [
        ("Backend API", "https://brainops-backend-prod.onrender.com/api/v1/health"),
        ("Revenue Pricing", "https://brainops-backend-prod.onrender.com/api/v1/revenue/pricing"),
        ("AI Support", "https://brainops-backend-prod.onrender.com/api/v1/support/support-metrics"),
        ("Revenue Dashboard", "https://brainops-backend-prod.onrender.com/api/v1/revenue/revenue-dashboard"),
        ("MyRoofGenius Frontend", "https://myroofgenius.com", 200),
        ("WeatherCraft App", "https://weathercraft-app.vercel.app", 200),
        ("Task OS", "https://brainops-task-os.vercel.app", 200),
    ]
    
    results = []
    for name, url, *args in systems:
        expected = args[0] if args else 200
        results.append(check_system(name, url, expected))
    
    # Check backend version
    try:
        resp = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health")
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n📊 Backend Version: {data.get('version', 'Unknown')}")
            print(f"📊 Loaded Routers: {data.get('loaded_routers', 0)}")
    except:
        pass
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    operational = sum(results)
    total = len(results)
    percentage = (operational / total) * 100
    
    print(f"Systems Operational: {operational}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("\n✅ ALL SYSTEMS FULLY OPERATIONAL!")
        print("💰 REVENUE COLLECTION READY!")
        print("🚀 PRODUCTION DEPLOYMENT SUCCESSFUL!")
    elif percentage >= 80:
        print("\n⚠️ Most systems operational")
        print("Some non-critical systems may need attention")
    else:
        print("\n❌ Critical systems offline")
        print("Immediate attention required")
    
    return percentage == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
