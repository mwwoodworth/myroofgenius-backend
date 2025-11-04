#!/usr/bin/env python3
"""
Monitor v132.0.0 deployment with FULL functionality
"""

import time
import requests
import json

print("🚀 Monitoring BrainOps Backend v132.0.0 deployment...")
print("=" * 60)

api_key = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
service_id = "srv-d1tfs4idbo4c73di6k00"

# Wait for deployment to complete
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

        if status == "live" and "v132.0.0" in version:
            print("\n✅ v132.0.0 Deployment successful!")
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
    print("Testing v132.0.0 endpoints with FULL functionality...")
    print("=" * 60)

    # Wait a bit for service to stabilize
    time.sleep(10)

    endpoints = [
        ("health", "GET", "/api/v1/health"),
        ("customers", "GET", "/api/v1/customers"),
        ("jobs", "GET", "/api/v1/jobs"),
        ("employees", "GET", "/api/v1/employees"),
        ("estimates", "GET", "/api/v1/estimates"),
        ("invoices", "GET", "/api/v1/invoices"),
        ("equipment", "GET", "/api/v1/equipment"),
        ("inventory", "GET", "/api/v1/inventory"),
        ("timesheets", "GET", "/api/v1/timesheets"),
        ("reports", "GET", "/api/v1/reports"),
        ("revenue/stats", "GET", "/api/v1/revenue/stats"),
        ("crm/leads", "GET", "/api/v1/crm/leads"),
        ("tenants", "GET", "/api/v1/tenants"),
        ("monitoring", "GET", "/api/v1/monitoring"),
        ("ai/agents", "GET", "/api/v1/ai/agents"),
        ("workflows", "GET", "/api/v1/workflows"),
    ]

    base_url = "https://brainops-backend-prod.onrender.com"
    results = []

    for name, method, path in endpoints:
        try:
            url = f"{base_url}{path}"
            response = requests.request(method, url, timeout=10)
            status_code = response.status_code

            if status_code == 200:
                try:
                    data = response.json()
                    version = data.get('version', 'N/A')
                    if version != 'N/A':
                        print(f"✅ {name:20} - {status_code} - v{version}")
                    else:
                        print(f"✅ {name:20} - {status_code}")
                except:
                    print(f"✅ {name:20} - {status_code}")
            else:
                print(f"❌ {name:20} - {status_code}")

            results.append((name, status_code))
        except Exception as e:
            print(f"❌ {name:20} - ERROR: {str(e)[:50]}")
            results.append((name, "ERROR"))

    # Summary
    print("\n" + "=" * 60)
    success = sum(1 for _, s in results if s == 200)
    total = len(results)
    percentage = (success * 100) // total

    print(f"SUMMARY: {success}/{total} endpoints working ({percentage}% operational)")
    print("=" * 60)

    if success == total:
        print("🎉 v132.0.0 WITH FULL FUNCTIONALITY DEPLOYED SUCCESSFULLY!")
        print("✨ ALL ENDPOINTS ARE NOW OPERATIONAL!")
        print("💯 Backend functionality has been FULLY RESTORED!")
    elif success >= 14:
        print("✅ v132.0.0 deployed with MOST functionality working!")
        failed = [name for name, status in results if status != 200]
        if failed:
            print(f"⚠️ Failed endpoints: {', '.join(failed)}")
    else:
        print("⚠️ v132.0.0 deployed but several endpoints need attention")
        failed = [name for name, status in results if status != 200]
        if failed:
            print(f"Failed endpoints: {', '.join(failed)}")
else:
    print("\n❌ Deployment did not complete successfully")
    print("Please check Render dashboard for more details")