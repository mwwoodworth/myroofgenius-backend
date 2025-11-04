#!/usr/bin/env python3
"""
Debug specific AI endpoint errors
"""

import requests
import json

BASE_URL = "https://brainops-backend-prod.onrender.com"

# Test each AI endpoint with verbose output
endpoints = [
    ("GET", "/api/v1/ai-board/status", None),
    ("POST", "/api/v1/ai-board/start-session", {"session_type": "strategic"}),
    ("GET", "/api/v1/aurea/status", None),
    ("POST", "/api/v1/aurea/initialize", {}),
    ("POST", "/api/v1/aurea/think", {"prompt": "test"}),
    ("GET", "/api/v1/langgraph/status", None),
    ("POST", "/api/v1/langgraph/execute", {"workflow_name": "test", "input_data": {}}),
    ("GET", "/api/v1/ai-os/status", None),
    ("GET", "/api/v1/customers", None),
    ("GET", "/api/v1/jobs", None),
]

print("DEBUGGING AI ENDPOINT ERRORS")
print("=" * 60)

for method, path, payload in endpoints:
    print(f"\n{method} {path}")
    print("-" * 40)
    
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{path}", timeout=10)
        else:
            resp = requests.post(f"{BASE_URL}{path}", json=payload, timeout=10)
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 500:
            # Try to get error details
            try:
                error_data = resp.json()
                if "detail" in error_data:
                    print(f"Error: {error_data['detail'][:500]}")
            except:
                print(f"Error: {resp.text[:500]}")
        elif resp.status_code in [200, 201]:
            print("✅ SUCCESS")
        else:
            print(f"Response: {resp.text[:200]}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")