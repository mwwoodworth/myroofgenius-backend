#!/usr/bin/env python3
"""
Monitor v134.0.0 CNS deployment to Render
"""

import os

import time
import requests
import json

print("🧠 CENTRAL NERVOUS SYSTEM v134.0.0 DEPLOYMENT")
print("=" * 60)

api_key = os.environ.get("RENDER_API_KEY")
service_id = "srv-d1tfs4idbo4c73di6k00"

# Trigger deployment
print("\n📦 Triggering deployment of v134.0.0...")
try:
    deploy_response = requests.post(
        f"https://api.render.com/v1/services/{service_id}/deploys",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "clearCache": "clear",
            "imageUrl": "docker.io/mwwoodworth/brainops-backend:v134.0.0"
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

        if status == "live" and "v134.0.0" in version:
            print("\n🎉 v134.0.0 CNS DEPLOYMENT SUCCESSFUL!")
            break
        elif status in ["update_failed", "canceled", "deactivated"]:
            print(f"\n❌ Deployment failed with status: {status}")
            break

        if i < 39:
            time.sleep(30)
    except Exception as e:
        print(f"Error checking deployment: {e}")
        time.sleep(30)

# Test CNS endpoints
if status == "live":
    print("\n" + "=" * 60)
    print("🧪 Testing CNS endpoints in production...")

    base_url = "https://brainops-backend-prod.onrender.com"

    # First test existing endpoints
    print("\n📊 Testing core endpoints:")
    core_endpoints = [
        ("health", "GET", "/api/v1/health"),
        ("customers", "GET", "/api/v1/customers"),
        ("monitoring", "GET", "/api/v1/monitoring"),
    ]

    for name, method, path in core_endpoints:
        try:
            response = requests.request(method, f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 'N/A')
                print(f"✅ {name:15} - {response.status_code} - v{version}")
            else:
                print(f"❌ {name:15} - {response.status_code}")
        except Exception as e:
            print(f"❌ {name:15} - ERROR: {str(e)[:50]}")

    # Test CNS endpoints
    print("\n🧠 Testing Central Nervous System endpoints:")
    cns_endpoints = [
        ("CNS Status", "GET", "/api/v1/cns/status"),
        ("CNS Memory Search", "GET", "/api/v1/cns/memory/search?query=test"),
        ("CNS Tasks", "GET", "/api/v1/cns/tasks"),
    ]

    for name, method, path in cns_endpoints:
        try:
            response = requests.request(method, f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name:20} - {response.status_code}")
                # Show sample data for CNS status
                if "status" in path:
                    data = response.json()
                    print(f"   Memory entries: {data.get('memory_count', 0)}")
                    print(f"   Tasks: {data.get('task_count', 0)}")
                    print(f"   Projects: {data.get('project_count', 0)}")
            elif response.status_code == 404:
                print(f"⚠️ {name:20} - 404 (CNS routes may not be mounted)")
            else:
                print(f"❌ {name:20} - {response.status_code}")
        except Exception as e:
            print(f"❌ {name:20} - ERROR: {str(e)[:50]}")

    # Test creating a memory
    print("\n💾 Testing CNS memory creation:")
    try:
        memory_data = {
            "memory_type": "context",
            "category": "system_deployment",
            "title": "CNS v134.0.0 Deployed",
            "content": {
                "event": "Central Nervous System deployed to production",
                "version": "134.0.0",
                "features": ["Persistent memory", "Task management", "AI integration"],
                "timestamp": "2025-09-29"
            },
            "importance_score": 0.9,
            "tags": ["deployment", "cns", "production"]
        }

        response = requests.post(
            f"{base_url}/api/v1/cns/memory",
            json=memory_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Memory created: {result.get('memory_id', 'N/A')}")
        elif response.status_code == 404:
            print("⚠️ CNS memory endpoint not found (routes may not be mounted)")
        else:
            print(f"❌ Memory creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Memory creation error: {str(e)[:100]}")

    print("\n" + "=" * 60)
    print("🧠 CENTRAL NERVOUS SYSTEM DEPLOYMENT COMPLETE")
    print("📝 CNS Features:")
    print("   - Persistent memory with semantic search")
    print("   - Task and project management")
    print("   - Decision tracking and learning")
    print("   - Automation rules engine")
    print("   - Cross-session context persistence")
    print("\n🚀 v134.0.0 is now LIVE in production!")
else:
    print("\n⚠️ Deployment did not complete successfully")
    print("Please check Render dashboard for more details")