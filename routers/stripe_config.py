"""
Stripe Configuration for MyRoofGenius
"""
import os

# Stripe Product/Price IDs
# These should be created in Stripe Dashboard and added to environment
STRIPE_PRODUCTS = {
    "professional": {
        "name": "Professional Plan",
        "price_id": os.getenv("STRIPE_PRICE_PROFESSIONAL", "price_1QU5xKFs5YLnaPiWKhU5WXYZ"),
        "amount": 9700,  # $97.00 in cents
        "interval": "month",
        "features": [
            "100 AI roof analyses per month",
            "Instant PDF reports",
            "Material calculations",
            "Labor estimates",
            "Email support"
        ]
    },
    "business": {
        "name": "Business Plan",
        "price_id": os.getenv("STRIPE_PRICE_BUSINESS", "price_1QU5xLFs5YLnaPiWABCD1234"),
        "amount": 19700,  # $197.00 in cents
        "interval": "month",
        "features": [
            "500 AI roof analyses per month",
            "Priority processing",
            "Custom branding",
            "API access",
            "Phone support",
            "Team collaboration"
        ]
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price_id": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_1QU5xMFs5YLnaPiWEFGH5678"),
        "amount": 49700,  # $497.00 in cents
        "interval": "month",
        "features": [
            "Unlimited AI analyses",
            "White label option",
            "Custom integrations",
            "Dedicated account manager",
            "24/7 priority support",
            "Advanced analytics",
            "Training included"
        ]
    }
}

# Stripe webhook endpoint secret
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

# Trial period in days
TRIAL_PERIOD_DAYS = 14

def get_price_id(plan: str) -> str:
    """Get Stripe price ID for a plan"""
    if plan in STRIPE_PRODUCTS:
        return STRIPE_PRODUCTS[plan]["price_id"]
    return None

def get_plan_details(plan: str) -> dict:
    """Get full plan details"""
    return STRIPE_PRODUCTS.get(plan, None)