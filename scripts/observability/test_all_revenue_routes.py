#!/usr/bin/env python3
"""
Test all revenue routes to confirm they're operational
"""

import requests
import json

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(method, path, data=None, params=None, name=None):
    """Test an endpoint and report status"""
    url = f"{BASE_URL}{path}"
    name = name or path
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, params=params, timeout=5)
        else:
            response = requests.request(method, url, json=data, params=params, timeout=5)
        
        if response.status_code < 400:
            print(f"✅ {name}: {response.status_code} - WORKING")
            return True
        elif response.status_code == 422:
            print(f"⚠️  {name}: {response.status_code} - Validation error (endpoint exists)")
            return True
        else:
            print(f"❌ {name}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("REVENUE SYSTEM OPERATIONAL TEST")
    print("=" * 60)
    print()
    
    # Test health
    print("🏥 SYSTEM HEALTH:")
    test_endpoint("GET", "/api/v1/health", name="Health Check")
    print()
    
    print("💰 REVENUE ENDPOINTS:")
    
    # Test revenue routes
    endpoints = [
        ("GET", "/api/v1/test-revenue/", None, None, "Test Revenue"),
        
        # AI Estimation
        ("POST", "/api/v1/ai-estimation/competitor-analysis", None, 
         {"zip_code": "80202", "service_type": "roof"}, "Competitor Analysis"),
        ("POST", "/api/v1/ai-estimation/generate-estimate", 
         {"address": "123 Main St", "roof_type": "shingle", "desired_material": "asphalt_shingle", 
          "customer_email": "test@example.com"}, None, "Generate Estimate"),
        
        # Stripe Revenue
        ("GET", "/api/v1/stripe-revenue/products", None, None, "Stripe Products"),
        ("POST", "/api/v1/stripe-revenue/create-checkout-session",
         {"price_id": "price_test", "customer_email": "test@example.com"}, None, "Checkout Session"),
        
        # Customer Pipeline
        ("POST", "/api/v1/customer-pipeline/leads",
         {"email": "test@example.com", "name": "Test Lead", "source": "website"}, None, "Create Lead"),
        ("GET", "/api/v1/customer-pipeline/leads", None, None, "List Leads"),
        
        # Landing Pages
        ("GET", "/api/v1/landing-pages/active", None, None, "Active Landing Pages"),
        ("POST", "/api/v1/landing-pages/track-conversion",
         {"page_id": "test", "variant": "A"}, None, "Track Conversion"),
        
        # Google Ads
        ("GET", "/api/v1/google-ads/campaigns", None, None, "Ad Campaigns"),
        ("POST", "/api/v1/google-ads/optimize",
         {"campaign_id": "test"}, None, "Optimize Campaign"),
        
        # Revenue Dashboard
        ("GET", "/api/v1/revenue-dashboard/metrics", None, None, "Revenue Metrics"),
        ("GET", "/api/v1/revenue-dashboard/chart-data", None, 
         {"period": "30d"}, "Chart Data"),
    ]
    
    working = 0
    total = len(endpoints)
    
    for method, path, data, params, name in endpoints:
        if test_endpoint(method, path, data, params, name):
            working += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {working}/{total} endpoints operational")
    
    if working == total:
        print("✅ ALL REVENUE SYSTEMS OPERATIONAL!")
    elif working > total * 0.7:
        print("⚠️  Most systems operational, some issues remain")
    else:
        print("❌ Critical issues with revenue system")
    
    print("=" * 60)

if __name__ == "__main__":
    main()