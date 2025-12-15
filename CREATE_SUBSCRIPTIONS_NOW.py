#!/usr/bin/env python3
"""
CREATE STRIPE SUBSCRIPTIONS - Quick Revenue Activation
Focus on SaaS subscriptions only for immediate revenue
"""

import stripe
import os
import json
from datetime import datetime

# STRIPE LIVE KEYS (Valid for 7 days from activation)
STRIPE_SECRET_KEY = "<STRIPE_KEY_REDACTED>"
STRIPE_PUBLISHABLE_KEY = "pk_live_51RHXCuFs5YLnaPiWkafx5348uNTKn2b5iUT0gKalb9lFgdVZt8lESg2MqDkZHjRPYto8uGtMnzUJJP3BV9ziff1H00VuIKLyPG"

stripe.api_key = STRIPE_SECRET_KEY

print("=" * 80)
print("🚀 CREATING MYROOFGENIUS SUBSCRIPTION PLANS")
print("=" * 80)
print(f"Time: {datetime.now()}")
print()

def create_subscription_products():
    """Create the three main subscription tiers"""
    
    products = []
    
    # Subscription tier definitions
    plans = [
        {
            "name": "MyRoofGenius Starter",
            "description": "Perfect for homeowners and small contractors",
            "price": 4900,  # $49/month
            "features": [
                "3 AI roof analyses per month",
                "Basic estimation tools",
                "Email support",
                "Mobile app access"
            ]
        },
        {
            "name": "MyRoofGenius Professional",
            "description": "Everything you need to grow your roofing business",
            "price": 19900,  # $199/month
            "features": [
                "Unlimited AI roof analyses",
                "Advanced estimation suite",
                "CRM & job tracking",
                "Priority support",
                "Team collaboration",
                "Custom branding"
            ]
        },
        {
            "name": "MyRoofGenius Enterprise",
            "description": "Custom solutions for large roofing companies",
            "price": 49900,  # $499/month
            "features": [
                "Everything in Professional",
                "White label options",
                "API access",
                "Dedicated account manager",
                "Custom integrations",
                "Advanced analytics"
            ]
        }
    ]
    
    print("📦 Creating Subscription Products...")
    print("-" * 40)
    
    for plan in plans:
        try:
            # Check if product already exists
            existing = stripe.Product.search(
                query=f"name:'{plan['name']}'"
            )
            
            if existing.data:
                product = existing.data[0]
                print(f"✅ Product exists: {product.name}")
            else:
                # Create product
                product = stripe.Product.create(
                    name=plan["name"],
                    description=plan["description"],
                    metadata={
                        "platform": "myroofgenius",
                        "features": json.dumps(plan["features"])
                    }
                )
                print(f"✅ Created product: {product.name}")
            
            # Create or get price
            prices = stripe.Price.list(product=product.id, limit=1)
            
            if prices.data:
                price = prices.data[0]
                print(f"   💰 Price exists: ${price.unit_amount/100:.2f}/month")
            else:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=plan["price"],
                    currency="usd",
                    recurring={"interval": "month"},
                    metadata={"tier": plan["name"].split()[-1].lower()}
                )
                print(f"   💰 Created price: ${price.unit_amount/100:.2f}/month")
            
            # Store for later use
            products.append({
                "product": product,
                "price": price,
                "plan": plan
            })
            
        except Exception as e:
            print(f"❌ Error with {plan['name']}: {e}")
    
    return products

def create_test_checkout_urls(products):
    """Generate test checkout URLs for each plan"""
    
    print("\n🔗 Generating Checkout URLs...")
    print("-" * 40)
    
    checkout_urls = []
    
    for item in products:
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": item["price"].id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url="https://myroofgenius.com/dashboard?subscription=success",
                cancel_url="https://myroofgenius.com/pricing",
                metadata={
                    "product_name": item["product"].name
                }
            )
            
            checkout_urls.append({
                "name": item["product"].name,
                "price": f"${item['price'].unit_amount/100:.2f}/month",
                "url": session.url
            })
            
            print(f"✅ {item['product'].name}")
            print(f"   Price: ${item['price'].unit_amount/100:.2f}/month")
            print(f"   Checkout: {session.url[:50]}...")
            
        except Exception as e:
            print(f"❌ Error creating checkout for {item['product'].name}: {e}")
    
    return checkout_urls

def print_integration_code(products):
    """Print the code needed for frontend integration"""
    
    print("\n📝 Frontend Integration Code")
    print("-" * 40)
    print("\nAdd this to your MyRoofGenius pricing page:\n")
    
    print("```javascript")
    print("// Price IDs for your subscription tiers")
    for item in products:
        tier = item["plan"]["name"].split()[-1].lower()
        print(f"const {tier}PriceId = '{item['price'].id}';")
    
    print("\n// Checkout function")
    print("""
async function startSubscription(priceId) {
  try {
    const response = await fetch('/api/v1/stripe-automation/checkout/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        price: priceId,
        success_url: window.location.origin + '/dashboard?subscription=success',
        cancel_url: window.location.origin + '/pricing'
      })
    });
    
    const { checkout_url } = await response.json();
    window.location.href = checkout_url;
  } catch (error) {
    console.error('Checkout error:', error);
  }
}

// Button click handlers
document.getElementById('starter-btn').onclick = () => startSubscription(starterPriceId);
document.getElementById('professional-btn').onclick = () => startSubscription(professionalPriceId);
document.getElementById('enterprise-btn').onclick = () => startSubscription(enterprisePriceId);
""")
    print("```")

def main():
    """Main execution"""
    
    # Test connection
    print("🔑 Testing Stripe Connection...")
    print("-" * 40)
    try:
        account = stripe.Account.retrieve()
        print(f"✅ Connected to: {account.email}")
        print(f"   Account ID: {account.id}")
    except stripe.error.AuthenticationError:
        print("❌ Invalid Stripe API key!")
        print("\nPlease update STRIPE_SECRET_KEY in this file with your actual key from:")
        print("https://dashboard.stripe.com/apikeys")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Create products
    products = create_subscription_products()
    
    if not products:
        print("\n❌ No products created. Check errors above.")
        return
    
    # Generate checkout URLs
    checkout_urls = create_test_checkout_urls(products)
    
    # Print integration code
    print_integration_code(products)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ SUBSCRIPTION SETUP COMPLETE!")
    print("=" * 80)
    
    print("\n🎯 TEST YOUR CHECKOUT FLOW:")
    for url in checkout_urls:
        print(f"\n{url['name']} ({url['price']}):")
        print(f"  {url['url']}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Test one of the checkout URLs above")
    print("2. Add the integration code to your frontend")
    print("3. Deploy the frontend changes")
    print("4. Start marketing your subscription plans!")
    
    print("\n💡 QUICK WINS:")
    print("- Add 'Start Free Trial' buttons (use Stripe's trial_period_days)")
    print("- Create a special launch discount (use Stripe coupons)")
    print("- Set up abandoned cart emails (use Stripe's checkout.session.expired webhook)")
    
    print("\n🚀 You're ready to start generating recurring revenue!")

if __name__ == "__main__":
    main()