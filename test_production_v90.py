#!/usr/bin/env python3
"""
Production Test Suite for v90.0.0
Tests all new endpoints and verifies data persistence
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "https://brainops-backend-prod.onrender.com"
LOCAL_URL = "http://localhost:8004"

def test_health():
    """Test backend health and version"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        data = response.json()
        print(f"✅ Backend Health: {data['status']}")
        print(f"📦 Version: {data['version']}")
        print(f"📊 Stats: {data['stats']['customers']} customers, {data['stats']['jobs']} jobs")
        return data['version']
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None

def test_sales_crm():
    """Test Sales CRM endpoints"""
    print("\n=== Testing Sales CRM (Tasks 61-70) ===")

    # Test pipelines
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pipelines/", timeout=10)
        if response.status_code == 200:
            pipelines = response.json()
            print(f"✅ Sales Pipelines: {len(pipelines)} pipelines")
        else:
            print(f"⚠️ Pipelines endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Pipelines test failed: {e}")

    # Test quotes
    try:
        response = requests.get(f"{BASE_URL}/api/v1/quotes/", timeout=10)
        if response.status_code == 200:
            quotes = response.json()
            print(f"✅ Quotes: {len(quotes)} quotes")
        else:
            print(f"⚠️ Quotes endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Quotes test failed: {e}")

def test_marketing_automation():
    """Test Marketing Automation endpoints"""
    print("\n=== Testing Marketing Automation (Tasks 71-80) ===")

    # Test campaigns
    try:
        response = requests.get(f"{BASE_URL}/api/v1/campaigns/", timeout=10)
        if response.status_code == 200:
            campaigns = response.json()
            print(f"✅ Marketing Campaigns: {len(campaigns)} campaigns")
        else:
            print(f"⚠️ Campaigns endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Campaigns test failed: {e}")

    # Test email templates
    try:
        response = requests.get(f"{BASE_URL}/api/v1/email/templates", timeout=10)
        if response.status_code == 200:
            print(f"✅ Email Marketing: endpoint accessible")
        else:
            print(f"⚠️ Email endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Email test failed: {e}")

def test_customer_service():
    """Test Customer Service endpoints"""
    print("\n=== Testing Customer Service (Tasks 81-90) ===")

    # Test tickets
    try:
        response = requests.get(f"{BASE_URL}/api/v1/tickets/", timeout=10)
        if response.status_code == 200:
            tickets = response.json()
            print(f"✅ Support Tickets: {len(tickets)} tickets")
        else:
            print(f"⚠️ Tickets endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Tickets test failed: {e}")

    # Test FAQs
    try:
        response = requests.get(f"{BASE_URL}/api/v1/faqs/", timeout=10)
        if response.status_code == 200:
            faqs = response.json()
            print(f"✅ FAQs: {len(faqs)} FAQs")
        else:
            print(f"⚠️ FAQs endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ FAQs test failed: {e}")

def test_data_persistence():
    """Test data persistence by creating and retrieving data"""
    print("\n=== Testing Data Persistence ===")

    # Create a test campaign
    campaign_data = {
        "name": f"Test Campaign {datetime.now().isoformat()}",
        "campaign_type": "email",
        "start_date": datetime.now().isoformat(),
        "status": "draft"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/campaigns/",
            json=campaign_data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            created_campaign = response.json()
            print(f"✅ Created campaign: {created_campaign.get('name', 'Unknown')}")

            # Verify it persists
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/api/v1/campaigns/", timeout=10)
            if response.status_code == 200:
                campaigns = response.json()
                if any(c.get('name') == campaign_data['name'] for c in campaigns):
                    print(f"✅ Data persistence verified - campaign found")
                else:
                    print(f"⚠️ Campaign created but not found in list")
        else:
            print(f"⚠️ Campaign creation returned {response.status_code}")
    except Exception as e:
        print(f"❌ Persistence test failed: {e}")

def test_all_frontends():
    """Test all frontend systems"""
    print("\n=== Testing Frontend Systems ===")

    frontends = [
        ("MyRoofGenius", "https://myroofgenius.com"),
        ("WeatherCraft ERP", "https://weathercraft-erp.vercel.app"),
        ("WeatherCraft Public", "https://www.weathercraftroofingco.com"),
        ("BrainOps Task OS", "https://brainops-task-os.vercel.app")
    ]

    for name, url in frontends:
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OPERATIONAL")
            else:
                print(f"⚠️ {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")

def main():
    print("=" * 60)
    print("PRODUCTION SYSTEM TEST - v90.0.0")
    print("=" * 60)

    # Test health first
    version = test_health()

    # Wait for deployment if not v90
    if version and version != "90.0.0":
        print(f"\n⏳ Backend showing {version}, waiting for v90.0.0 deployment...")
        print("   (This may take 3-5 minutes)")

        # Wait and recheck
        for i in range(10):
            time.sleep(30)
            response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
            data = response.json()
            if data['version'] == "90.0.0":
                print(f"✅ v90.0.0 deployed!")
                break
            else:
                print(f"   Still {data['version']}, waiting...")

    # Test all systems
    test_sales_crm()
    test_marketing_automation()
    test_customer_service()
    test_data_persistence()
    test_all_frontends()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()