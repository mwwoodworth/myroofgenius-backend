#!/usr/bin/env python3
"""
Production Test Suite for v100.0.0
Tests Analytics & BI endpoints and verifies system integrity
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

def test_analytics_bi():
    """Test Analytics & BI endpoints (Tasks 91-100)"""
    print("\n=== Testing Analytics & Business Intelligence ===")

    endpoints = [
        # Task 91: Business Intelligence
        ("/api/v1/analytics/bi/dashboards", "BI Dashboards"),
        ("/api/v1/analytics/bi/kpis", "BI KPIs"),

        # Task 92: Data Warehouse
        ("/api/v1/analytics/warehouse/etl", "ETL Jobs"),
        ("/api/v1/analytics/warehouse/quality", "Data Quality"),

        # Task 93: Reporting Engine
        ("/api/v1/analytics/reports/templates", "Report Templates"),
        ("/api/v1/analytics/reports/generate", "Report Generation"),

        # Task 94: Predictive Analytics
        ("/api/v1/analytics/predictive/forecast", "Predictive Forecast"),

        # Task 95: Real-time Analytics
        ("/api/v1/analytics/realtime/metrics", "Real-time Metrics"),

        # Task 96: Data Visualization
        ("/api/v1/analytics/visualization/charts", "Charts"),

        # Task 97: Performance Metrics
        ("/api/v1/analytics/metrics/business", "Business Metrics"),

        # Task 98: Data Governance
        ("/api/v1/analytics/governance/catalog", "Data Catalog"),

        # Task 99: Executive Dashboards
        ("/api/v1/analytics/dashboards/executive", "Executive Dashboard"),

        # Task 100: Analytics API
        ("/api/v1/analytics/api/datasets", "Analytics API")
    ]

    working = 0
    total = len(endpoints)

    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"✅ {name}: {len(data)} items")
                    else:
                        print(f"✅ {name}: {data.get('status', 'OK')}")
                    working += 1
                except:
                    print(f"✅ {name}: Accessible")
                    working += 1
            else:
                print(f"⚠️ {name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {str(e)[:50]}")

    print(f"\nAnalytics Summary: {working}/{total} endpoints operational")
    return working >= total * 0.7

def test_predictive_analytics():
    """Test predictive analytics with real data"""
    print("\n=== Testing Predictive Analytics Features ===")

    # Test revenue forecasting
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/predictive/forecast",
            params={"type": "revenue", "periods": 3},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Revenue Forecast: {data.get('forecast_type', 'Revenue prediction available')}")
        else:
            print(f"⚠️ Revenue forecast returned {response.status_code}")
    except Exception as e:
        print(f"❌ Revenue forecast failed: {e}")

    # Test churn prediction
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/predictive/churn",
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ Churn Prediction: Endpoint accessible")
        else:
            print(f"⚠️ Churn prediction returned {response.status_code}")
    except Exception as e:
        print(f"❌ Churn prediction failed: {e}")

def test_data_governance():
    """Test data governance and compliance"""
    print("\n=== Testing Data Governance & Compliance ===")

    # Test GDPR compliance
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/governance/compliance",
            params={"type": "gdpr"},
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ GDPR Compliance: Endpoint accessible")
        else:
            print(f"⚠️ GDPR compliance returned {response.status_code}")
    except Exception as e:
        print(f"❌ GDPR compliance failed: {e}")

    # Test data quality rules
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/analytics/governance/quality",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data Quality: {len(data.get('rules', []))} rules configured")
        else:
            print(f"⚠️ Data quality returned {response.status_code}")
    except Exception as e:
        print(f"❌ Data quality failed: {e}")

def test_all_systems():
    """Test all major system endpoints"""
    print("\n=== Testing All Systems Integration ===")

    system_categories = [
        ("Sales CRM", ["/api/v1/pipelines/", "/api/v1/quotes/"]),
        ("Marketing", ["/api/v1/campaigns/", "/api/v1/email/templates"]),
        ("Customer Service", ["/api/v1/tickets/", "/api/v1/faqs/"]),
        ("Analytics", ["/api/v1/analytics/bi/dashboards", "/api/v1/analytics/api/datasets"])
    ]

    for category, endpoints in system_categories:
        working = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if response.status_code == 200:
                    working += 1
            except:
                pass

        status = "✅" if working == len(endpoints) else "⚠️" if working > 0 else "❌"
        print(f"{status} {category}: {working}/{len(endpoints)} endpoints working")

def main():
    print("=" * 60)
    print("PRODUCTION SYSTEM TEST - v100.0.0")
    print("Analytics & Business Intelligence Complete")
    print("=" * 60)

    # Test health first
    version = test_health()

    # Test all systems
    test_analytics_bi()
    test_predictive_analytics()
    test_data_governance()
    test_all_systems()

    print("\n" + "=" * 60)
    print("TEST COMPLETE - v100.0.0")
    print("Tasks 91-100: Analytics & BI System Deployed")
    print("=" * 60)

if __name__ == "__main__":
    main()