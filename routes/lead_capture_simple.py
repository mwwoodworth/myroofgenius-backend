"""
Simple Lead Capture Endpoint
Working implementation with shared database connection
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

from database import get_db

class LeadCaptureRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = "website"
    message: Optional[str] = None

class LeadCaptureResponse(BaseModel):
    id: str
    name: str
    email: str
    lead_score: int
    status: str
    message: str

@router.post("/lead-capture", response_model=LeadCaptureResponse)
def capture_lead(lead: LeadCaptureRequest, db: Session = Depends(get_db)):
    """
    Simple lead capture endpoint that works
    """
    try:
        # Generate lead ID
        lead_id = str(uuid.uuid4())

        # Calculate simple lead score
        lead_score = 50
        if lead.company:
            lead_score += 20
        if lead.phone:
            lead_score += 15
        if lead.message and len(lead.message) > 50:
            lead_score += 15

        # Insert into database
        query = text("""
            INSERT INTO leads (
                id, name, email, phone, company,
                source, message, lead_score, status, created_at
            ) VALUES (
                :id, :name, :email, :phone, :company,
                :source, :message, :lead_score, 'new', NOW()
            )
        """)

        db.execute(query, {
            "id": lead_id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company,
            "source": lead.source,
            "message": lead.message,
            "lead_score": lead_score
        })
        db.commit()

        return LeadCaptureResponse(
            id=lead_id,
            name=lead.name,
            email=lead.email,
            lead_score=lead_score,
            status="created",
            message="Lead captured successfully",
        )

    except Exception as e:
        logger.error(f"Lead capture error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to capture lead") from e

@router.get("/leads")
def get_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all captured leads
    """
    try:
        query = text("""
            SELECT id, name, email, phone, company,
                   source, lead_score, status, created_at
            FROM leads
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """)

        result = db.execute(query, {"limit": limit, "skip": skip})
        leads = []
        for row in result:
            leads.append({
                "id": str(row[0]),
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "company": row[4],
                "source": row[5],
                "lead_score": row[6],
                "status": row[7],
                "created_at": row[8].isoformat() if row[8] else None
            })

        return leads

    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        # Return empty list if table doesn't exist
        return []
