#!/usr/bin/env python3
"""
Fix AI endpoint validation errors by testing with correct request structure
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_ai_endpoints():
    """Test AI endpoints with correct request structure"""
    
    print("=" * 80)
    print("FIXING AI ENDPOINT VALIDATION ERRORS")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)
    print()
    
    # Test 1: Roof Analysis with correct structure
    print("1. Testing Roof Analysis Endpoint...")
    roof_data = {
        "image_url": "https://example.com/roof.jpg",
        "address": "123 Main St, Denver, CO",
        "urgency": "normal",
        "customer_id": "test-123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/analyze-roof",
            json=roof_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Roof analysis working!")
            data = response.json()
            print(f"   Confidence: {data.get('confidence', 0)}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    print()
    
    # Test 2: Lead Scoring with correct structure
    print("2. Testing Lead Scoring Endpoint...")
    lead_data = {
        "lead_data": {
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "555-0123",
            "interest_level": "high"
        },
        "behavior_signals": [
            "visited_pricing_page",
            "downloaded_brochure",
            "spent_10_minutes_on_site"
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/lead-scoring",
            json=lead_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Lead scoring working!")
            data = response.json()
            print(f"   Score: {data.get('score', 0)}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    print()
    
    # Test 3: Content Generation
    print("3. Testing Content Generation Endpoint...")
    content_data = {
        "topic": "roof maintenance",
        "style": "professional",
        "length": "medium"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/generate-content",
            json=content_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Content generation working!")
            data = response.json()
            print(f"   Title: {data.get('title', 'No title')}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    print()
    
    # Test 4: Churn Prediction
    print("4. Testing Churn Prediction Endpoint...")
    churn_data = {
        "customer_data": {
            "customer_id": "test-456",
            "last_purchase_days_ago": 90,
            "total_purchases": 3,
            "support_tickets": 2
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/predict-churn",
            json=churn_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Churn prediction working!")
            data = response.json()
            print(f"   Risk Level: {data.get('risk_level', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    print()
    
    # Test 5: Revenue Optimization
    print("5. Testing Revenue Optimization Endpoint...")
    revenue_data = {
        "customer_id": "test-789",
        "product_id": "pro-plan",
        "market_data": {
            "competitor_price": 150,
            "market_demand": "high"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/optimize-revenue",
            json=revenue_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Revenue optimization working!")
            data = response.json()
            print(f"   Recommended Price: ${data.get('recommended_price', 0)}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    print()
    print("=" * 80)
    print("AI ENDPOINT TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_ai_endpoints()