
# Add to fastapi-operator-env/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.auth import get_current_user
from core.database import get_db

router = APIRouter()

@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "name": current_user.get("name", "User"),
        "role": current_user.get("role", "user"),
        "created_at": current_user.get("created_at"),
        "subscription": {
            "plan": "Professional",
            "credits": 100,
            "usage": 45
        }
    }



# Add to fastapi-operator-env/api/v1/ai.py
import random
import uuid
from datetime import datetime

@router.post("/estimate")
async def create_ai_estimate(
    request: dict,
    db: Session = Depends(get_db)
):
    """Generate AI-powered roofing estimate"""
    
    # For now, return demo data
    roof_area = request.get("roof_area", 2500)
    material_type = request.get("material_type", "Asphalt Shingles")
    
    # Calculate costs
    material_cost = roof_area * random.uniform(3, 6)  # $3-6 per sq ft
    labor_cost = roof_area * random.uniform(2, 4)  # $2-4 per sq ft
    total_cost = material_cost + labor_cost
    
    return {
        "estimate_id": str(uuid.uuid4()),
        "total_cost": round(total_cost, 2),
        "materials": round(material_cost, 2),
        "labor": round(labor_cost, 2),
        "confidence": 0.89,
        "breakdown": {
            "roof_area": f"{roof_area} sq ft",
            "material_type": material_type,
            "complexity": "Medium",
            "duration": "3-5 days",
            "warranty": "25 years"
        },
        "ai_insights": {
            "market_comparison": "15% below market average",
            "quality_score": 8.5,
            "recommendations": [
                "Consider upgrading to architectural shingles",
                "Add ice/water shield for better protection",
                "Include ridge venting for improved airflow"
            ]
        },
        "created_at": datetime.utcnow().isoformat()
    }
