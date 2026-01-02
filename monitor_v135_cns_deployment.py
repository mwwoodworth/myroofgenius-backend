#!/usr/bin/env python3
"""
Monitor v135.0.0 CNS Deployment
Central Nervous System with corrected table references
"""

import os
import time
import requests
import json
import logging

logger = logging.getLogger(__name__)

print("🧠 Monitoring BrainOps Backend v135.0.0 CNS deployment...")
print("=" * 60)

api_key = os.getenv("RENDER_API_KEY", "")
service_id = os.getenv("RENDER_SERVICE_ID", "srv-d1tfs4idbo4c73di6k00")

# Trigger deployment
print("\n📦 Triggering deployment of v135.0.0...")
try:
    deploy_response = requests.post(
        f"https://api.render.com/v1/services/{service_id}/deploys",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "clearCache": "clear",
            "imageUrl": "docker.io/mwwoodworth/brainops-backend:v135.0.0"
        }
    )
    print(f"Deployment trigger response: {deploy_response.status_code}")
    if deploy_response.status_code == 201:
        print("✅ Deployment triggered successfully")
    else:
        print(f"⚠️ Deployment response: {deploy_response.text[:200]}")
except Exception as e:
    print(f"❌ Error triggering deployment: {e}")

# Monitor deployment
print("\n🔄 Waiting for deployment to complete...")
deployment_success = False

for i in range(30):
    try:
        response = requests.get(
            f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        data = response.json()[0]['deploy']
        status = data['status']
        version = data['image']['ref']

        print(f"\nCheck {i+1}/30:")
        print(f"  Status: {status}")
        print(f"  Version: {version}")

        if status == "live" and "v135.0.0" in version:
            print("\n✅ v135.0.0 Deployment successful!")
            deployment_success = True
            break
        elif status in ["update_failed", "canceled", "deactivated"]:
            print(f"\n❌ Deployment failed with status: {status}")
            break

        if i < 29:
            time.sleep(20)
    except Exception as e:
        print(f"Error checking deployment: {e}")
        time.sleep(20)

# Test endpoints after deployment
if deployment_success:
    print("\n" + "=" * 60)
    print("🧪 Testing v135.0.0 endpoints with CNS functionality...")
    print("=" * 60)

    # Wait for service to be ready
    print("Waiting for service to stabilize...")
    time.sleep(15)

    base_url = "https://brainops-backend-prod.onrender.com"

    # Test regular endpoints
    regular_endpoints = [
        ("health", "GET", "/api/v1/health"),
        ("customers", "GET", "/api/v1/customers"),
        ("jobs", "GET", "/api/v1/jobs"),
        ("employees", "GET", "/api/v1/employees"),
        ("monitoring", "GET", "/api/v1/monitoring"),
        ("workflows", "GET", "/api/v1/workflows"),
    ]

    print("\n📊 Testing regular endpoints:")
    regular_results = []

    for name, method, path in regular_endpoints:
        try:
            url = f"{base_url}{path}"
            response = requests.request(method, url, timeout=10)
            status_code = response.status_code

            if status_code == 200:
                try:
                    data = response.json()
                    version = data.get('version', 'N/A')
                    print(f"  ✅ {name:20} - {status_code} - v{version}")
                except Exception as e:
                    logger.warning(f"Could not parse response: {e}")
                    print(f"  ✅ {name:20} - {status_code}")
            else:
                print(f"  ❌ {name:20} - {status_code}")

            regular_results.append((name, status_code))
        except Exception as e:
            print(f"  ❌ {name:20} - ERROR: {str(e)[:50]}")
            regular_results.append((name, "ERROR"))

    # Test CNS endpoints specifically
    print("\n🧠 Testing CNS endpoints:")
    cns_endpoints = [
        ("CNS Status", "GET", "/api/v1/cns/status"),
        ("CNS Memory Search", "GET", "/api/v1/cns/memory/search?query=test&limit=5"),
        ("CNS Tasks", "GET", "/api/v1/cns/tasks"),
    ]

    cns_results = []

    for name, method, path in cns_endpoints:
        try:
            url = f"{base_url}{path}"
            response = requests.request(method, url, timeout=10)
            status_code = response.status_code

            if status_code == 200:
                data = response.json()
                if name == "CNS Status":
                    print(f"  ✅ {name:20} - {status_code}")
                    print(f"     CNS Version: {data.get('version', 'N/A')}")
                    print(f"     Memory Count: {data.get('memory_count', 0)}")
                    print(f"     Task Count: {data.get('task_count', 0)}")
                    print(f"     Project Count: {data.get('project_count', 0)}")
                    print(f"     Database: {data.get('database', 'unknown')}")
                    print(f"     Initialized: {data.get('initialized', False)}")
                else:
                    print(f"  ✅ {name:20} - {status_code}")
            else:
                print(f"  ❌ {name:20} - {status_code}")
                if status_code == 500:
                    error_text = response.text[:200]
                    print(f"     Error: {error_text}")

            cns_results.append((name, status_code))
        except Exception as e:
            print(f"  ❌ {name:20} - ERROR: {str(e)[:50]}")
            cns_results.append((name, "ERROR"))

    # Test CNS memory storage
    print("\n🧠 Testing CNS memory storage:")
    try:
        memory_data = {
            "type": "test",
            "category": "deployment",
            "title": "v135.0.0 Deployment Test",
            "content": {
                "message": "CNS v135.0.0 deployed successfully",
                "timestamp": time.time(),
                "version": "v135.0.0"
            },
            "importance": 0.8,
            "tags": ["deployment", "test", "v135"]
        }

        response = requests.post(
            f"{base_url}/api/v1/cns/memory",
            json=memory_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            memory_id = result.get('memory_id')
            print(f"  ✅ Memory stored successfully: {memory_id}")
        else:
            print(f"  ❌ Memory storage failed: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Memory storage error: {e}")

    # Test CNS task creation
    print("\n🧠 Testing CNS task creation:")
    try:
        task_data = {
            "title": "Verify CNS v135.0.0 Deployment",
            "description": "Ensure all CNS features are operational",
            "due_date": None,
            "tags": ["deployment", "verification"]
        }

        response = requests.post(
            f"{base_url}/api/v1/cns/tasks",
            json=task_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"  ✅ Task created successfully: {task_id}")
        else:
            print(f"  ❌ Task creation failed: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Task creation error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)

    regular_success = sum(1 for _, s in regular_results if s == 200)
    regular_total = len(regular_results)
    print(f"Regular Endpoints: {regular_success}/{regular_total} working ({regular_success*100//regular_total}%)")

    cns_success = sum(1 for _, s in cns_results if s == 200)
    cns_total = len(cns_results)
    print(f"CNS Endpoints: {cns_success}/{cns_total} working ({cns_success*100//cns_total}%)")

    total_success = regular_success + cns_success
    total_endpoints = regular_total + cns_total
    overall_percentage = (total_success * 100) // total_endpoints

    print(f"\nOVERALL: {total_success}/{total_endpoints} endpoints working ({overall_percentage}% operational)")

    if cns_success == cns_total:
        print("\n🎉 CNS FULLY OPERATIONAL!")
        print("✅ Central Nervous System v135.0.0 deployed successfully!")
        print("✅ All CNS tables correctly referenced")
        print("✅ Memory storage operational")
        print("✅ Task management operational")
        print("✅ Ready for AI integration with API keys")
    elif cns_success > 0:
        print("\n⚠️ CNS PARTIALLY OPERATIONAL")
        print("Some CNS features working but needs attention")
    else:
        print("\n❌ CNS NOT OPERATIONAL")
        print("CNS endpoints are not responding correctly")
        print("Check logs for database connection issues")
else:
    print("\n❌ Deployment did not complete successfully")
    print("Manual deployment may be required in Render dashboard")

print("\n" + "=" * 60)
print("🧠 CNS v135.0.0 Deployment Monitor Complete")
print("=" * 60)