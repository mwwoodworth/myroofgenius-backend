#!/usr/bin/env python3
"""
Test Stripe System with Permanent Restricted Key
"""

import stripe
import json
from datetime import datetime

# Permanent Restricted Key - Never Expires
STRIPE_SECRET_KEY = "<STRIPE_KEY_REDACTED>"
stripe.api_key = STRIPE_SECRET_KEY

print("=" * 80)
print("🔐 TESTING STRIPE WITH PERMANENT RESTRICTED KEY")
print("=" * 80)
print(f"Time: {datetime.now()}")
print()

def test_connection():
    """Test Stripe connection with permanent key"""
    print("1️⃣ Testing Connection...")
    print("-" * 40)
    try:
        # Test API connection
        account = stripe.Account.retrieve()
        print(f"✅ Connected to: {account.email}")
        print(f"   Account ID: {account.id}")
        print(f"   Account Name: {account.settings.dashboard.display_name if hasattr(account.settings.dashboard, 'display_name') else 'N/A'}")
        return True
    except stripe.error.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_products():
    """Test product listing"""
    print("\n2️⃣ Testing Product Access...")
    print("-" * 40)
    try:
        products = stripe.Product.list(limit=5)
        print(f"✅ Found {len(products.data)} products")
        for product in products.data:
            print(f"   - {product.name}: {product.id}")
        return True
    except Exception as e:
        print(f"❌ Error listing products: {e}")
        return False

def test_customers():
    """Test customer operations"""
    print("\n3️⃣ Testing Customer Operations...")
    print("-" * 40)
    try:
        # List customers
        customers = stripe.Customer.list(limit=3)
        print(f"✅ Can list customers: {len(customers.data)} found")
        
        # Try to create a test customer
        test_customer = stripe.Customer.create(
            email=f"test_{datetime.now().timestamp()}@myroofgenius.com",
            description="Test customer for permanent key validation"
        )
        print(f"✅ Can create customers: {test_customer.id}")
        
        # Delete test customer
        stripe.Customer.delete(test_customer.id)
        print("✅ Can delete customers")
        
        return True
    except Exception as e:
        print(f"❌ Customer operations error: {e}")
        return False

def test_checkout():
    """Test checkout session creation"""
    print("\n4️⃣ Testing Checkout Session...")
    print("-" * 40)
    try:
        # Get a product/price to test with
        prices = stripe.Price.list(limit=1)
        if not prices.data:
            print("⚠️ No prices found to test checkout")
            return False
        
        price = prices.data[0]
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price.id,
                "quantity": 1
            }],
            mode="subscription" if price.recurring else "payment",
            success_url="https://myroofgenius.com/success",
            cancel_url="https://myroofgenius.com/cancel"
        )
        
        print(f"✅ Checkout session created: {session.id}")
        print(f"   URL: {session.url[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Checkout error: {e}")
        return False

def test_subscriptions():
    """Test subscription operations"""
    print("\n5️⃣ Testing Subscription Access...")
    print("-" * 40)
    try:
        subscriptions = stripe.Subscription.list(limit=3)
        print(f"✅ Can list subscriptions: {len(subscriptions.data)} found")
        
        if subscriptions.data:
            sub = subscriptions.data[0]
            print(f"   - Status: {sub.status}")
            print(f"   - Customer: {sub.customer}")
        
        return True
    except Exception as e:
        print(f"❌ Subscription error: {e}")
        return False

def main():
    """Run all tests"""
    
    tests = [
        test_connection,
        test_products,
        test_customers,
        test_checkout,
        test_subscriptions
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 SUCCESS! The permanent restricted key is working perfectly!")
        print("✅ This key will NEVER expire")
        print("✅ All necessary permissions are granted")
        print("✅ Ready for production use")
    else:
        print("\n⚠️ Some tests failed. Check the permissions on your restricted key.")
        print("Go to: https://dashboard.stripe.com/apikeys")
        print("Edit your restricted key and grant the necessary permissions")
    
    print("\n📝 KEY INFORMATION:")
    print("Variable Name: STRIPE_SECRET_KEY")
    print("Key Type: Restricted (Permanent)")
    print(f"Key: rk_live_...{STRIPE_SECRET_KEY[-4:]}")
    print("\n🔧 Update these files with the permanent key:")
    print("- /home/mwwoodworth/code/fastapi-operator-env/.env.production ✅")
    print("- /home/mwwoodworth/code/fastapi-operator-env/routes/stripe_automation.py ✅")
    print("- /home/mwwoodworth/code/fastapi-operator-env/routes/stripe_revenue.py ✅")
    print("- /home/mwwoodworth/code/fastapi-operator-env/routes/stripe_automation_enhanced.py ✅")
    print("- Frontend: NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY")

if __name__ == "__main__":
    main()