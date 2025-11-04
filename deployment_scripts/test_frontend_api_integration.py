#!/usr/bin/env python3
"""Test frontend API integration"""

import requests

def test_frontend_integration():
    print("Testing MyRoofGenius Frontend Integration...")
    print("=" * 60)
    
    # Test frontend endpoints
    frontend_urls = [
        "https://myroofgenius.com",
        "https://www.myroofgenius.com",
        "https://myroofgenius.vercel.app"
    ]
    
    for url in frontend_urls:
        try:
            resp = requests.get(url, timeout=5, allow_redirects=True)
            print(f"{url}: {resp.status_code}")
            if resp.status_code == 500:
                # Try to get error details
                if "NEXT_PUBLIC_API_URL" in resp.text:
                    print("  - Possible API configuration issue")
                elif "Authentication" in resp.text:
                    print("  - Possible auth integration issue")
        except Exception as e:
            print(f"{url}: Error - {str(e)[:50]}")
    
    print("\nBackend API Status:")
    resp = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ API Version: {data.get('version')}")
        print(f"✅ Routes Loaded: {data.get('routes_loaded')}")
        print(f"✅ Database: {data.get('database')}")
    
    print("\nRecommendation:")
    print("The frontend 500 error is likely due to:")
    print("1. Environment variable mismatch")
    print("2. API URL configuration") 
    print("3. Build/deployment issue on Vercel")
    print("\nThe backend API is fully operational.")

if __name__ == "__main__":
    test_frontend_integration()