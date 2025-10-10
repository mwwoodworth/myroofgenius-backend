#!/usr/bin/env python3
"""
Test revenue system locally
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
print("Testing revenue route imports...")
try:
    from routes.test_revenue import router as test_revenue_router
    print("✅ test_revenue imported")
except Exception as e:
    print(f"❌ test_revenue failed: {e}")

try:
    from routes.ai_estimation import router as ai_estimation_router
    print("✅ ai_estimation imported")
except Exception as e:
    print(f"❌ ai_estimation failed: {e}")

try:
    from routes.stripe_revenue import router as stripe_revenue_router
    print("✅ stripe_revenue imported")
except Exception as e:
    print(f"❌ stripe_revenue failed: {e}")

try:
    from routes.customer_pipeline import router as customer_pipeline_router
    print("✅ customer_pipeline imported")
except Exception as e:
    print(f"❌ customer_pipeline failed: {e}")

try:
    from routes.landing_pages import router as landing_pages_router
    print("✅ landing_pages imported")
except Exception as e:
    print(f"❌ landing_pages failed: {e}")

try:
    from routes.google_ads_automation import router as google_ads_router
    print("✅ google_ads_automation imported")
except Exception as e:
    print(f"❌ google_ads_automation failed: {e}")

try:
    from routes.revenue_dashboard import router as revenue_dashboard_router
    print("✅ revenue_dashboard imported")
except Exception as e:
    print(f"❌ revenue_dashboard failed: {e}")

print("\nTesting main_v504.py...")
try:
    import main_v504
    print(f"✅ main_v504 imported successfully")
    print(f"   Revenue routes loaded: {main_v504.REVENUE_ROUTES_LOADED}")
except Exception as e:
    print(f"❌ main_v504 failed: {e}")
    import traceback
    traceback.print_exc()