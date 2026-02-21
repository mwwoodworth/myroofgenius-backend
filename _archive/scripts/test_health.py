#!/usr/bin/env python3
"""Test health endpoint locally"""

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test /health endpoint
response = client.get("/health")
print(f"GET /health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test /api/v1/health endpoint
response = client.get("/api/v1/health")
print(f"GET /api/v1/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json() if response.status_code == 200 else response.text}")
print()

if response.status_code == 200:
    print("✅ Health checks working!")
else:
    print("❌ Health check failed!")