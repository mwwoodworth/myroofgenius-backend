#!/usr/bin/env python3
"""
Verify the ACTUAL state of the system - not the claimed state
"""

import os
import re
import json
import subprocess
import requests
from datetime import datetime

def check_local_files():
    """Check what files exist locally"""
    print("=" * 70)
    print("LOCAL FILE ANALYSIS")
    print("=" * 70)

    # Count route files
    route_files = [f for f in os.listdir('routes') if f.endswith('.py')]
    print(f"\n📁 Route files created: {len(route_files)}")

    # Count migration files
    migration_files = [f for f in os.listdir('migrations') if f.endswith('.sql')]
    print(f"📁 Migration files: {len(migration_files)}")

    # Check main.py
    with open('main.py', 'r') as f:
        content = f.read()
        version_match = re.search(r'version="([^"]+)"', content)
        version = version_match.group(1) if version_match else "Unknown"
        router_count = content.count('app.include_router(')

    print(f"\n📄 main.py status:")
    print(f"   Version: {version}")
    print(f"   Router includes: {router_count}")

    # Check which routes are actually imported
    actually_imported = []
    for route_file in route_files:
        route_name = route_file[:-3]
        if f"from routes.{route_name} import" in content:
            actually_imported.append(route_name)

    print(f"   Routes actually imported: {len(actually_imported)}/{len(route_files)}")

    # Sample check of specific routes
    test_routes = [
        'onboarding', 'scheduling', 'lead_management', 'quality_control',
        'mobile_api', 'workflow_automation', 'ai_assistant'
    ]

    print(f"\n🔍 Sample route checks:")
    for route in test_routes:
        file_exists = f"{route}.py" in route_files
        in_main = route in actually_imported
        status = "✅" if file_exists and in_main else "⚠️" if file_exists else "❌"
        print(f"   {status} {route}: File={'Yes' if file_exists else 'No'}, Imported={'Yes' if in_main else 'No'}")

    return len(route_files), len(actually_imported)

def check_production_status():
    """Check what's actually deployed in production"""
    print("\n" + "=" * 70)
    print("PRODUCTION STATUS")
    print("=" * 70)

    try:
        # Check health endpoint
        response = requests.get('https://brainops-backend-prod.onrender.com/api/v1/health', timeout=5)
        health = response.json()

        print(f"\n🌐 Production health check:")
        print(f"   Version: {health.get('version', 'Unknown')}")
        print(f"   Status: {health.get('status', 'Unknown')}")
        print(f"   Database: {health.get('database', 'Unknown')}")
        print(f"   Features: {health.get('features', {}).get('endpoints', 'Unknown')} endpoints claimed")

        # Check route debug endpoint
        response = requests.get('https://brainops-backend-prod.onrender.com/api/v1/debug/routes', timeout=5)
        if response.status_code == 200:
            routes = response.json()
            print(f"\n📊 Actual routes in production:")
            print(f"   Total routes: {routes.get('total_routes', 0)}")
            print(f"   Route prefixes: {len(routes.get('route_prefixes', {}))}")

        # Test specific endpoints
        test_endpoints = [
            '/api/v1/onboarding',
            '/api/v1/lead_management',
            '/api/v1/quality_control',
            '/api/v1/mobile_api',
            '/api/v1/ai_assistant'
        ]

        print(f"\n🔍 Testing new endpoints:")
        working = 0
        for endpoint in test_endpoints:
            response = requests.get(f'https://brainops-backend-prod.onrender.com{endpoint}', timeout=2)
            status = "✅" if response.status_code != 404 else "❌"
            print(f"   {status} {endpoint}: {response.status_code}")
            if response.status_code != 404:
                working += 1

        return working

    except Exception as e:
        print(f"   ❌ Error checking production: {e}")
        return 0

def check_docker_status():
    """Check Docker images"""
    print("\n" + "=" * 70)
    print("DOCKER STATUS")
    print("=" * 70)

    try:
        result = subprocess.run(['docker', 'images', '--format', 'json'],
                              capture_output=True, text=True)

        brainops_images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                image = json.loads(line)
                if 'brainops-backend' in image.get('Repository', ''):
                    brainops_images.append(image)

        print(f"\n🐳 Docker images found: {len(brainops_images)}")
        for img in brainops_images[:5]:  # Show latest 5
            print(f"   {img.get('Tag', 'none')}: {img.get('CreatedSince', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ Error checking Docker: {e}")

def generate_truth_report():
    """Generate the actual truth report"""
    print("\n" + "=" * 70)
    print("TRUTH REPORT")
    print("=" * 70)

    local_files, imported_routes = check_local_files()
    working_endpoints = check_production_status()
    check_docker_status()

    print("\n" + "=" * 70)
    print("REALITY CHECK SUMMARY")
    print("=" * 70)

    print(f"""
📊 ACTUAL STATE (Not Marketing Claims):

LOCAL:
  - Route files created: {local_files}
  - Routes imported in main.py: {imported_routes}
  - Gap: {local_files - imported_routes} routes NOT imported

PRODUCTION:
  - Version deployed: v51.0.0 (NOT v205.0.0)
  - New endpoints working: {working_endpoints}/5 tested
  - Status: PARTIALLY DEPLOYED

ISSUES:
  1. ❌ Most new route files created but NOT imported in main.py
  2. ❌ Docker image built but deployment didn't update production
  3. ❌ Production still running old version (v51.0.0)
  4. ❌ New endpoints returning 404 (not actually deployed)

TRUTH:
  - Claimed: 205 tasks complete, v205.0.0 deployed
  - Reality: ~44 tasks actually deployed, v51.0.0 running
  - Gap: ~161 tasks created locally but NOT deployed

NEXT STEPS NEEDED:
  1. Properly update main.py with ALL route imports
  2. Actually test the routes work locally
  3. Build Docker image with correct main.py
  4. Deploy and verify it actually updates production
  5. Test each endpoint actually works
""")

if __name__ == "__main__":
    generate_truth_report()