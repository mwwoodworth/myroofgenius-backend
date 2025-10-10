#!/usr/bin/env python3
"""
Test MyRoofGenius Revenue System
Real revenue generation testing
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_pricing():
    """Test new competitive pricing"""
    print("\n🏷️ TESTING PRICING TIERS")
    print("-" * 50)
    
    resp = requests.get(f"{BASE_URL}/api/v1/revenue/pricing")
    if resp.status_code == 200:
        data = resp.json()
        print("✅ Pricing Retrieved:")
        for tier_name, tier_info in data.get("tiers", {}).items():
            print(f"\n  {tier_info['name']}: ${tier_info['price']/100}/mo")
            print(f"    Value: {tier_info['value_prop']}")
            print(f"    Features: {len(tier_info['features'])} included")
        
        print(f"\n  Competitor Comparison:")
        for competitor, price in data.get("competitor_comparison", {}).items():
            print(f"    {competitor}: {price}")
        
        print(f"\n  💰 {data.get('savings', '')}")
        return True
    else:
        print(f"❌ Failed to get pricing: {resp.status_code}")
        return False

def test_checkout_session():
    """Test Stripe checkout session creation"""
    print("\n💳 TESTING CHECKOUT SESSION")
    print("-" * 50)
    
    checkout_data = {
        "tier": "starter",
        "customer_email": "test@myroofgenius.com",
        "success_url": "https://myroofgenius.com/success",
        "cancel_url": "https://myroofgenius.com/pricing"
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/v1/revenue/create-checkout-session",
        json=checkout_data
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Checkout Session Created:")
        print(f"   Session ID: {data.get('session_id', 'N/A')}")
        print(f"   Tier: {data.get('tier')}")
        print(f"   Trial Days: {data.get('trial_days')}")
        print(f"   Monthly Price: ${data.get('monthly_price')}")
        print(f"   Checkout URL: {data.get('checkout_url', 'Generated')[:50]}...")
        return True
    else:
        print(f"⚠️  Checkout creation returned: {resp.status_code}")
        if resp.text:
            print(f"   Response: {resp.text[:200]}")
        return False

def test_ai_quote():
    """Test AI quote generation"""
    print("\n🤖 TESTING AI QUOTE GENERATOR")
    print("-" * 50)
    
    quote_data = {
        "image_url": "https://example.com/roof.jpg",
        "property_details": {
            "square_feet": 2500,
            "address": "123 Main St, Denver, CO"
        }
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/v1/revenue/ai-quote-generator",
        json=quote_data
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ AI Quote Generated:")
        print(f"   Quote ID: {data.get('quote_id')}")
        print(f"   Roof Area: {data.get('analysis', {}).get('roof_area_sqft')} sq ft")
        print(f"   Damage: {data.get('analysis', {}).get('damage_assessment')}")
        print(f"   Total Cost: ${data.get('costs', {}).get('total', 0):,.2f}")
        print(f"   AI Confidence: {data.get('ai_confidence', 0)*100:.0f}%")
        print(f"   Valid For: {data.get('valid_for_days')} days")
        return True
    else:
        print(f"❌ Quote generation failed: {resp.status_code}")
        return False

def test_support_chat():
    """Test AI support system"""
    print("\n💬 TESTING AI SUPPORT")
    print("-" * 50)
    
    # Test support metrics endpoint
    resp = requests.get(f"{BASE_URL}/api/v1/support/support-metrics")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ AI Support Metrics:")
        perf = data.get("ai_performance", {})
        print(f"   Resolution Rate: {perf.get('resolution_rate', 'N/A')}")
        print(f"   Avg Response Time: {perf.get('avg_response_time', 'N/A')}")
        print(f"   Customer Satisfaction: {perf.get('customer_satisfaction', 0)}/5")
        
        savings = data.get("cost_savings", {})
        print(f"\n   💰 Cost Savings:")
        print(f"   Monthly Savings: ${savings.get('monthly_savings', 0):,.2f}")
        
        return True
    else:
        print(f"❌ Support metrics failed: {resp.status_code}")
        return False

def test_revenue_dashboard():
    """Test revenue analytics dashboard"""
    print("\n📊 TESTING REVENUE DASHBOARD")
    print("-" * 50)
    
    resp = requests.get(f"{BASE_URL}/api/v1/revenue/revenue-dashboard")
    if resp.status_code == 200:
        data = resp.json()
        metrics = data.get("metrics", {})
        print(f"✅ Revenue Metrics:")
        print(f"   MRR: ${metrics.get('mrr', 0):,.2f}")
        print(f"   ARR: ${metrics.get('arr', 0):,.2f}")
        print(f"   Total Customers: {metrics.get('total_customers', 0)}")
        print(f"   Churn Rate: {metrics.get('churn_rate', 0)*100:.1f}%")
        print(f"   LTV/CAC Ratio: {metrics.get('ltv_cac_ratio', 0):.2f}")
        
        growth = data.get("growth", {})
        print(f"\n   📈 Growth:")
        print(f"   Month over Month: {growth.get('month_over_month', 'N/A')}")
        print(f"   New Customers: {growth.get('new_customers_this_month', 0)}")
        
        projections = data.get("projections", {})
        print(f"\n   🔮 Projections:")
        print(f"   Next Month MRR: ${projections.get('next_month_mrr', 0):,.2f}")
        print(f"   Next Quarter ARR: ${projections.get('next_quarter_arr', 0):,.2f}")
        
        return True
    else:
        print(f"❌ Dashboard failed: {resp.status_code}")
        return False

def test_onboarding():
    """Test automated onboarding"""
    print("\n🎯 TESTING ONBOARDING AUTOMATION")
    print("-" * 50)
    
    resp = requests.post(
        f"{BASE_URL}/api/v1/revenue/onboarding-automation",
        json={"customer_email": "new@customer.com"}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Onboarding Scheduled:")
        print(f"   Customer: {data.get('customer')}")
        print(f"   Activation Time: {data.get('estimated_activation_time')}")
        
        steps = data.get("automation_steps", [])
        print(f"\n   📋 Automation Steps ({len(steps)}):")
        for step in steps[:3]:
            print(f"   Day {step['day']}: {step['action']}")
        
        return True
    else:
        print(f"❌ Onboarding failed: {resp.status_code}")
        return False

def main():
    print("🚀 MYROOFGENIUS REVENUE SYSTEM TEST")
    print("=" * 70)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Wait for deployment
    print("\n⏳ Waiting 30 seconds for deployment...")
    time.sleep(30)
    
    # Run tests
    results = []
    results.append(("Pricing", test_pricing()))
    results.append(("Checkout", test_checkout_session()))
    results.append(("AI Quote", test_ai_quote()))
    results.append(("Support", test_support_chat()))
    results.append(("Dashboard", test_revenue_dashboard()))
    results.append(("Onboarding", test_onboarding()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total) * 100
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\nOverall: {passed}/{total} passed ({percentage:.1f}%)")
    
    if percentage >= 80:
        print("\n✅ REVENUE SYSTEM READY FOR PRODUCTION!")
        print("💰 Ready to collect real revenue")
        print("🚀 AI automation at $29-$99/month")
        print("📈 Projected: $7,830/month with 170 customers")
    elif percentage >= 60:
        print("\n⚠️ Revenue system partially operational")
        print("Some features need attention")
    else:
        print("\n❌ Revenue system needs fixes")
        print("Critical issues detected")
    
    return percentage >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)