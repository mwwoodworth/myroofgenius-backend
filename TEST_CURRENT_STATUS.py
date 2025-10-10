#!/usr/bin/env python3
"""
Quick test of current system status
"""

import requests

BASE_URL = "https://brainops-backend-prod.onrender.com"

endpoints = [
    "/api/v1/health",
    "/api/v1/ai-board/status",
    "/api/v1/aurea/status",
    "/api/v1/langgraph/status",
    "/api/v1/ai-os/status",
    "/api/v1/customers",
    "/api/v1/jobs",
    "/api/v1/estimates",
    "/api/v1/invoices",
    "/api/v1/products/public",
]

print("Testing current status...")
print("=" * 50)

working = 0
for path in endpoints:
    try:
        resp = requests.get(f"{BASE_URL}{path}", timeout=5)
        status = "✅" if resp.status_code == 200 else f"❌ {resp.status_code}"
        print(f"{status} {path}")
        if resp.status_code == 200:
            working += 1
    except Exception as e:
        print(f"❌ {path}: {str(e)[:30]}")

print("=" * 50)
print(f"Success: {working}/{len(endpoints)} = {(working/len(endpoints))*100:.0f}%")