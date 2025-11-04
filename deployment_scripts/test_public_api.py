#!/usr/bin/env python3
"""Test public product API endpoints"""

import requests
import json

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_public_products():
    """Test public product endpoints"""
    
    print("=" * 60)
    print("Testing Public Product API Endpoints")
    print("=" * 60)
    
    # Test 1: List products
    print("\n1. Testing /api/v1/products/public/list")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/public/list")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Products found: {data.get('total', 0)}")
            if data.get('products'):
                print(f"   First product: {data['products'][0]['name']}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 2: Get categories
    print("\n2. Testing /api/v1/products/public/categories")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/public/categories")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Categories found: {data.get('total', 0)}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 3: Get featured products
    print("\n3. Testing /api/v1/products/public/featured")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/public/featured")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Featured products: {data.get('total', 0)}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 4: Check if routes are requiring auth incorrectly
    print("\n4. Testing authentication requirements")
    endpoints = [
        "/api/v1/products",
        "/api/v1/products/list",
        "/api/v1/products/public",
        "/api/v1/products/public/list"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: Failed - {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_public_products()