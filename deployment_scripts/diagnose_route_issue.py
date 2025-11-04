#!/usr/bin/env python3
"""
Diagnose why routes are returning 501 Not Implemented
"""
import requests
import json

BASE_URL = "https://brainops-backend-prod.onrender.com"

def analyze_openapi_spec():
    """Analyze OpenAPI spec to understand route structure"""
    print("🔍 Analyzing OpenAPI Specification...")
    
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code != 200:
        print("❌ Failed to fetch OpenAPI spec")
        return
    
    spec = response.json()
    paths = spec.get('paths', {})
    
    print(f"\n📊 API Structure Analysis:")
    print(f"Total endpoints: {len(paths)}")
    
    # Group endpoints by prefix
    prefixes = {}
    for path in paths:
        parts = path.split('/')
        if len(parts) > 3:
            prefix = f"/{parts[1]}/{parts[2]}/{parts[3]}"
        elif len(parts) > 2:
            prefix = f"/{parts[1]}/{parts[2]}"
        else:
            prefix = path
        
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(path)
    
    print("\n🗂️ Endpoint Groups:")
    for prefix, endpoints in sorted(prefixes.items()):
        print(f"\n{prefix}: {len(endpoints)} endpoints")
        for ep in endpoints[:3]:  # Show first 3
            print(f"  - {ep}")
        if len(endpoints) > 3:
            print(f"  ... and {len(endpoints) - 3} more")
    
    # Check for catch-all routes
    print("\n🎯 Checking for catch-all routes...")
    catch_all_routes = [p for p in paths if '{path}' in p]
    for route in catch_all_routes:
        print(f"  Found: {route}")
        methods = list(paths[route].keys())
        print(f"    Methods: {methods}")
    
    # Test specific endpoints
    print("\n🧪 Testing Specific Endpoints:")
    test_endpoints = [
        ("/api/v1/health", "GET"),
        ("/api/v1/auth/login", "POST"),
        ("/api/v1/memory", "GET"),
        ("/api/v1/agents", "GET"),
        ("/api/v1/", "GET"),
    ]
    
    for endpoint, method in test_endpoints:
        if method == "GET":
            resp = requests.get(BASE_URL + endpoint)
        else:
            resp = requests.post(BASE_URL + endpoint, json={})
        
        print(f"\n{endpoint} ({method}): {resp.status_code}")
        if resp.status_code == 501:
            error = resp.json()
            print(f"  Error: {error.get('message', 'Unknown')}")

def check_health_endpoint_details():
    """Get detailed health information"""
    print("\n🏥 Health Endpoint Details:")
    resp = requests.get(f"{BASE_URL}/api/v1/health")
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=2))

def main():
    print("=" * 60)
    print("🔍 Route Loading Diagnostic")
    print("=" * 60)
    
    check_health_endpoint_details()
    analyze_openapi_spec()
    
    print("\n" + "=" * 60)
    print("📝 Diagnosis Summary")
    print("=" * 60)
    print("\nThe 501 errors with 'Module not found in project' suggest:")
    print("1. Routes are registered but handlers are missing")
    print("2. There might be catch-all routes intercepting requests")
    print("3. The route modules aren't being imported properly")
    print("\nThe fact that /api/v1/health works but others don't")
    print("indicates selective route loading issues.")

if __name__ == "__main__":
    main()