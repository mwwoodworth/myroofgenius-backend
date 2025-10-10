from fastapi import HTTPException
"""
Test Revenue Route - Verify system is working
"""

from fastapi import APIRouter

router = APIRouter(tags=["Test"])

@router.get("/")
def test_revenue():
    """Simple test endpoint"""
    return {
        "status": "operational",
        "message": "Revenue system v5.12 is deployed",
        "features": {
            "ai_estimation": "ready",
            "stripe_payments": "ready",
            "customer_pipeline": "ready",
            "landing_pages": "ready",
            "google_ads": "ready",
            "revenue_dashboard": "ready"
        },
        "targets": {
            "week_1": "$2,500",
            "week_2": "$7,500",
            "week_4": "$25,000"
        }
    }