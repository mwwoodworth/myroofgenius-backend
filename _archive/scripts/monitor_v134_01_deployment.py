#!/usr/bin/env python3
"""
Monitor v134.0.1 CNS deployment with fixes
"""

import os

import time
import requests
import json

print("🧠 CENTRAL NERVOUS SYSTEM v134.0.1 DEPLOYMENT (FIXED)")
print("=" * 60)

api_key = os.environ.get("RENDER_API_KEY")
service_id = "srv-d1tfs4idbo4c73di6k00"

# Trigger deployment
print("\n📦 Triggering deployment of v134.0.1 with CNS fixes...")
try:
    deploy_response = requests.post(
        f"https://api.render.com/v1/services/{service_id}/deploys",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "clearCache": "clear",
            "imageUrl": "docker.io/mwwoodworth/brainops-backend:v134.0.1"
        }
    )
    if deploy_response.status_code in [200, 201]:
        print("✅ Deployment triggered successfully")
    else:
        print(f"⚠️ Deployment trigger returned: {deploy_response.status_code}")
        print(deploy_response.text)
except Exception as e:
    print(f"❌ Failed to trigger deployment: {e}")

# Monitor deployment
print("\n⏳ Monitoring deployment progress...")
deployment_successful = False
for i in range(40):  # Check for 20 minutes
    try:
        response = requests.get(
            f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        data = response.json()[0]['deploy']
        status = data['status']
        version = data['image']['ref']

        print(f"\nCheck {i+1}/40:")
        print(f"  Status: {status}")
        print(f"  Version: {version}")

        if status == "live" and "v134.0.1" in version:
            print("\n🎉 v134.0.1 DEPLOYMENT SUCCESSFUL!")
            deployment_successful = True
            break
        elif status in ["update_failed", "canceled", "deactivated"]:
            print(f"\n❌ Deployment failed with status: {status}")
            break

        if i < 39:
            time.sleep(30)
    except Exception as e:
        print(f"Error checking deployment: {e}")
        time.sleep(30)

# Test endpoints if deployment successful
if deployment_successful:
    print("\n" + "=" * 60)
    print("🧪 Testing production endpoints...")

    base_url = "https://brainops-backend-prod.onrender.com"

    # First test core endpoints to ensure system is up
    print("\n📊 Testing core endpoints:")
    core_endpoints = [
        ("health", "GET", "/api/v1/health"),
        ("customers", "GET", "/api/v1/customers"),
        ("monitoring", "GET", "/api/v1/monitoring"),
    ]

    all_working = True
    for name, method, path in core_endpoints:
        try:
            response = requests.request(method, f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 'N/A')
                print(f"✅ {name:15} - {response.status_code} - v{version}")
            else:
                print(f"❌ {name:15} - {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"❌ {name:15} - ERROR: {str(e)[:50]}")
            all_working = False

    # Test CNS endpoints (may be 404 if CNS not available, which is OK)
    print("\n🧠 Testing Central Nervous System endpoints:")
    cns_endpoints = [
        ("CNS Status", "GET", "/api/v1/cns/status"),
        ("CNS Memory Search", "GET", "/api/v1/cns/memory/search?query=test"),
        ("CNS Tasks", "GET", "/api/v1/cns/tasks"),
    ]

    cns_available = False
    for name, method, path in cns_endpoints:
        try:
            response = requests.request(method, f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name:20} - {response.status_code} - CNS IS OPERATIONAL!")
                cns_available = True
                # Show sample data for CNS status
                if "status" in path:
                    data = response.json()
                    print(f"   Memory entries: {data.get('memory_count', 0)}")
                    print(f"   Tasks: {data.get('task_count', 0)}")
                    print(f"   Projects: {data.get('project_count', 0)}")
            elif response.status_code == 404:
                print(f"⚠️ {name:20} - 404 (CNS not available - this is OK)")
            else:
                print(f"❌ {name:20} - {response.status_code}")
        except Exception as e:
            print(f"❌ {name:20} - ERROR: {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 60)
    if all_working:
        print("✅ CORE SYSTEM FULLY OPERATIONAL")
        if cns_available:
            print("🧠 CENTRAL NERVOUS SYSTEM IS ACTIVE!")
            print("📝 CNS Features Available:")
            print("   - Persistent memory with semantic search")
            print("   - Task and project management")
            print("   - Decision tracking and learning")
            print("   - Automation rules engine")
            print("   - Cross-session context persistence")
        else:
            print("⚠️ CNS not available (service unavailable or not configured)")
            print("   This is normal if cns_service.py is not included")
            print("   Core system continues to work without CNS")
        print("\n🚀 v134.0.1 successfully deployed with graceful CNS handling!")
    else:
        print("❌ Some core endpoints are having issues")
        print("Please check Render logs for more details")
else:
    print("\n⚠️ Deployment did not complete successfully")
    print("Please check Render dashboard for more details")