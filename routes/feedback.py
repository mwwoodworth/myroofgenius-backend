"""
Feedback System Routes (NPS & Referrals)
Extracted from BrainStackStudio for BrainOps
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import hashlib
import secrets

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

# Get database connection
def get_db():
    """Get database connection"""
    from main import db_engine
    if not db_engine:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db_engine

# --- NPS Survey Models ---
class NPSSurveyRequest(BaseModel):
    """NPS survey submission"""
    score: int = Field(..., ge=0, le=10, description="NPS score from 0-10")
    feedback: Optional[str] = Field(None, max_length=1000)
    would_recommend: bool = Field(True)
    
class TestimonialRequest(BaseModel):
    """Testimonial submission"""
    testimonial: str = Field(..., min_length=10, max_length=500)
    use_case: str = Field(..., description="What they use BrainOps for")
    results: Optional[str] = Field(None, description="Measurable results achieved")
    company_name: Optional[str] = None
    role: Optional[str] = None
    permission_to_use: bool = Field(False, description="Permission to use publicly")

# --- Referral Models ---
class ReferralCodeRequest(BaseModel):
    """Request to generate or retrieve referral code"""
    org_id: Optional[str] = None

class ApplyReferralRequest(BaseModel):
    """Request to apply a referral code"""
    referral_code: str
    org_id: str

# --- NPS Endpoints ---
@router.post("/nps/survey")
async def submit_nps_survey(request: NPSSurveyRequest):
    """
    Submit NPS survey response
    0-6: Detractors, 7-8: Passives, 9-10: Promoters
    """
    try:
        from sqlalchemy import text
        engine = get_db()
        
        # Calculate NPS category
        category = "detractor" if request.score <= 6 else "passive" if request.score <= 8 else "promoter"
        
        with engine.connect() as conn:
            # Store NPS response
            result = conn.execute(text("""
                INSERT INTO nps_responses (
                    score, category, feedback, would_recommend,
                    created_at, metadata
                ) VALUES (
                    :score, :category, :feedback, :would_recommend,
                    NOW(), :metadata
                ) RETURNING id
            """), {
                "score": request.score,
                "category": category,
                "feedback": request.feedback,
                "would_recommend": request.would_recommend,
                "metadata": json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "api"
                })
            })
            conn.commit()
            response_id = result.fetchone()[0]
            
        # If promoter, generate referral code
        referral_code = None
        if category == "promoter":
            referral_code = generate_referral_code()
        
        return {
            "success": True,
            "response_id": response_id,
            "category": category,
            "message": get_nps_response_message(category),
            "referral_code": referral_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit survey: {str(e)}")

@router.post("/nps/testimonial")
async def submit_testimonial(request: TestimonialRequest):
    """
    Submit a testimonial
    Users who give permission get rewards
    """
    try:
        from sqlalchemy import text
        engine = get_db()
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO testimonials (
                    testimonial, use_case, results,
                    company_name, role, permission_to_use,
                    status, created_at, metadata
                ) VALUES (
                    :testimonial, :use_case, :results,
                    :company_name, :role, :permission_to_use,
                    'pending', NOW(), :metadata
                ) RETURNING id
            """), {
                "testimonial": request.testimonial,
                "use_case": request.use_case,
                "results": request.results,
                "company_name": request.company_name,
                "role": request.role,
                "permission_to_use": request.permission_to_use,
                "metadata": json.dumps({
                    "timestamp": datetime.utcnow().isoformat()
                })
            })
            conn.commit()
            testimonial_id = result.fetchone()[0]
            
        # Reward for permission
        reward = None
        if request.permission_to_use:
            reward = {
                "type": "credit",
                "amount": 50,
                "description": "Thank you for sharing your testimonial!"
            }
        
        return {
            "success": True,
            "testimonial_id": testimonial_id,
            "reward": reward,
            "message": "Thank you for your testimonial!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit testimonial: {str(e)}")

@router.get("/nps/analytics")
async def get_nps_analytics():
    """Get NPS analytics"""
    try:
        from sqlalchemy import text
        engine = get_db()
        
        with engine.connect() as conn:
            # Get NPS scores
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN category = 'promoter' THEN 1 END) as promoters,
                    COUNT(CASE WHEN category = 'passive' THEN 1 END) as passives,
                    COUNT(CASE WHEN category = 'detractor' THEN 1 END) as detractors,
                    AVG(score) as avg_score
                FROM nps_responses
                WHERE created_at > NOW() - INTERVAL '90 days'
            """))
            stats = result.fetchone()
            
            # Calculate NPS score
            if stats[0] > 0:
                nps = ((stats[1] / stats[0]) - (stats[3] / stats[0])) * 100
            else:
                nps = 0
            
        return {
            "nps_score": round(nps, 1),
            "total_responses": stats[0],
            "promoters": stats[1],
            "passives": stats[2],
            "detractors": stats[3],
            "average_score": round(stats[4], 1) if stats[4] else 0,
            "trend": "improving"  # Would calculate from historical data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

# --- Referral Endpoints ---
@router.post("/referrals/generate")
async def generate_referral_code_endpoint():
    """Generate or retrieve referral code"""
    try:
        code = generate_referral_code()
        link = f"https://myroofgenius.com/signup?ref={code}"
        
        return {
            "referral_code": code,
            "referral_link": link,
            "share_message": f"Get 20% off BrainOps with my code: {code}",
            "stats": {
                "total_referrals": 0,
                "successful_referrals": 0,
                "total_earned": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")

@router.post("/referrals/apply")
async def apply_referral_code(request: ApplyReferralRequest):
    """Apply a referral code to a new signup"""
    try:
        from sqlalchemy import text
        engine = get_db()
        
        # Validate code format
        if not validate_referral_code(request.referral_code):
            return {
                "valid": False,
                "message": "Invalid referral code format"
            }
        
        # Store referral application
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO referral_applications (
                    referral_code, org_id, status,
                    discount_percentage, discount_months,
                    created_at
                ) VALUES (
                    :code, :org_id, 'pending',
                    20, 3, NOW()
                )
            """), {
                "code": request.referral_code,
                "org_id": request.org_id
            })
            conn.commit()
        
        return {
            "valid": True,
            "message": "Referral code applied successfully",
            "discount_percentage": 20,
            "discount_months": 3
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply code: {str(e)}")

@router.get("/referrals/validate/{code}")
async def validate_referral(code: str):
    """Validate if a referral code is valid"""
    valid = validate_referral_code(code)
    
    if valid:
        return {
            "valid": True,
            "message": "Valid referral code",
            "discount_percentage": 20,
            "discount_months": 3
        }
    else:
        return {
            "valid": False,
            "message": "Invalid referral code"
        }

@router.get("/testimonials")
async def get_public_testimonials(limit: int = Query(default=10, ge=1, le=50)):
    """Get approved public testimonials"""
    try:
        from sqlalchemy import text
        engine = get_db()
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    testimonial, use_case, results,
                    company_name, role, created_at
                FROM testimonials
                WHERE permission_to_use = true
                AND status = 'approved'
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"limit": limit})
            
            testimonials = []
            for row in result:
                testimonials.append({
                    "testimonial": row[0],
                    "use_case": row[1],
                    "results": row[2],
                    "company_name": row[3],
                    "role": row[4],
                    "date": row[5].isoformat() if row[5] else None
                })
        
        return {
            "testimonials": testimonials,
            "total": len(testimonials)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get testimonials: {str(e)}")

# --- Helper Functions ---
def generate_referral_code():
    """Generate a unique referral code"""
    # Generate random code
    code = secrets.token_urlsafe(6).upper()
    # Add prefix for branding
    return f"BRAIN-{code}"

def validate_referral_code(code: str):
    """Validate referral code format"""
    return code and code.startswith("BRAIN-") and len(code) == 14

def get_nps_response_message(category: str):
    """Get appropriate message based on NPS category"""
    messages = {
        "promoter": "Thank you! We're thrilled you love BrainOps. Here's a referral code to share!",
        "passive": "Thank you for your feedback. We're working hard to improve your experience.",
        "detractor": "We appreciate your honesty. We'd love to learn more about how we can improve."
    }
    return messages.get(category, "Thank you for your feedback! RETURNING *")