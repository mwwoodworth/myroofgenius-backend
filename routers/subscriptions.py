
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
