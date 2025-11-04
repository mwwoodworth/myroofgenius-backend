
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
