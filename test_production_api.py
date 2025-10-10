#!/usr/bin/env python3
"""Test BrainOps Production API"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoints():
    """Test various endpoints"""
    
    # Test health
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Version: {data.get('version')}")
        print(f"Database: {data.get('database')}")
        print(f"Stats: {data.get('stats', {})}")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test /api/v1/health  
    print("Testing /api/v1/health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Version: {data.get('version')}")
        print(f"Operational: {data.get('operational')}")
        print(f"Stats: {data.get('stats', {})}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_endpoints()
