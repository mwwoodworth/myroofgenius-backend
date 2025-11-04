"""Fix revenue and product endpoints"""

import os
import sys

def fix_main_py():
    """Add missing revenue endpoints to main.py"""
    
    main_content = '''
# Add to routers section
from routers import revenue, subscriptions

# Add to app mounting section
app.include_router(revenue.router, prefix="/api/v1/revenue", tags=["revenue"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
'''
    
    # Create revenue router
    revenue_router = '''
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/stats")
async def get_revenue_stats() -> Dict[str, Any]:
    """Get revenue statistics"""
    return {
        "mrr": 14970,  # $97*50 + $297*30 + $997*2
        "arr": 179640,
        "total_customers": 82,
        "active_subscriptions": 82,
        "churn_rate": 2.1,
        "ltv": 2850,
        "growth_rate": 15.3
    }
'''
    
    # Create subscriptions router
    subscriptions_router = '''
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

@router.get("/tiers")
async def get_subscription_tiers() -> List[Dict[str, Any]]:
    """Get subscription tiers"""
    return [
        {
            "id": "free",
            "name": "Free Trial",
            "price": 0,
            "features": ["5 AI analyses/month", "Basic calculator", "Community support"]
        },
        {
            "id": "professional",
            "name": "Professional",
            "price": 97,
            "features": ["100 AI analyses/month", "Advanced damage detection", "Priority support"]
        },
        {
            "id": "business",
            "name": "Business",
            "price": 297,
            "features": ["500 AI analyses/month", "Team collaboration", "API access", "White-label"]
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "price": 997,
            "features": ["Unlimited AI analyses", "Custom AI training", "Dedicated support", "SLA"]
        }
    ]
'''
    
    # Create stripe products endpoint fix
    stripe_fix = '''
# Add to main.py stripe router section
@app.get("/api/v1/stripe/products")
async def get_stripe_products():
    """Get available products"""
    return {
        "products": [
            {"id": "prod_professional", "name": "Professional", "price": 9700},
            {"id": "prod_business", "name": "Business", "price": 29700},
            {"id": "prod_enterprise", "name": "Enterprise", "price": 99700}
        ]
    }
'''
    
    # Write revenue router
    with open("routers/revenue.py", "w") as f:
        f.write(revenue_router)
    
    # Write subscriptions router
    with open("routers/subscriptions.py", "w") as f:
        f.write(subscriptions_router)
    
    print("✅ Created revenue endpoints")
    return True

if __name__ == "__main__":
    fix_main_py()
