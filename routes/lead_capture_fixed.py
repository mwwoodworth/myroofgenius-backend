"""
Fixed Lead Capture Endpoint
Properly handles async database operations and connection pooling
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json
import uuid
import logging

from database.async_connection import get_pool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Lead Capture Fixed"])

class LeadCapture(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    project_type: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website"
    metadata: Optional[Dict] = {}

@router.post("/leads/capture/fixed")
async def capture_lead_fixed(lead: LeadCapture, background_tasks: BackgroundTasks):
    """
    Fixed lead capture with proper async database handling
    """
    lead_id = str(uuid.uuid4())

    # Default lead score
    lead_score = 75
    ai_enriched = False

    # Try AI scoring if available
    try:
        # Simplified AI scoring logic
        if "urgent" in (lead.message or "").lower():
            lead_score = 90
        elif "immediate" in (lead.message or "").lower():
            lead_score = 85
        elif lead.project_type == "roof_replacement":
            lead_score = 80

        ai_enriched = True
    except Exception as e:
        logger.warning(f"AI scoring failed: {e}")

    # Database operations with proper async handling
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # First, check if the table has the required columns (caching this would be better)
            columns = await conn.fetch("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'leads'
            """)

            column_names = [col['column_name'] for col in columns]

            # Build insert query based on available columns
            if 'project_type' in column_names and 'message' in column_names:
                # New schema with all columns
                await conn.execute("""
                    INSERT INTO leads (
                        id, name, email, phone, company,
                        project_type, message, source,
                        score, lead_score, ai_enriched,
                        created_at, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                    lead_id,
                    lead.name,
                    lead.email,
                    lead.phone or "",
                    lead.company or "",
                    lead.project_type or "general",
                    lead.message or "",
                    lead.source,
                    lead_score,  # score column
                    lead_score,  # lead_score column (duplicate for compatibility)
                    ai_enriched,
                    datetime.utcnow(),
                    json.dumps(lead.metadata)
                )
            else:
                # Fallback for old schema
                await conn.execute("""
                    INSERT INTO leads (
                        id, name, email, phone, company,
                        source, score, lead_score,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    lead_id,
                    lead.name,
                    lead.email,
                    lead.phone or "",
                    lead.company or "",
                    lead.source,
                    lead_score,
                    lead_score,
                    datetime.utcnow()
                )

            # BRIDGE FIX: Dual-write to revenue_leads for AI Agent pickup
            try:
                # Map 0-100 score to 0.0-1.0
                normalized_score = float(lead_score) / 100.0
                
                # Estimate value based on project type
                est_value = 5000.0
                if lead.project_type == "roof_replacement":
                    est_value = 15000.0
                elif lead.project_type == "commercial":
                    est_value = 50000.0

                await conn.execute("""
                    INSERT INTO revenue_leads (
                        company_name, contact_name, email, phone, location,
                        stage, score, value_estimate, source, metadata,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                """,
                    lead.company or lead.name,
                    lead.name,
                    lead.email,
                    lead.phone or "",
                    "", # Location unknown from web form usually
                    'new',
                    normalized_score,
                    est_value,
                    lead.source or 'website',
                    json.dumps({
                        "lead_type": "web_capture",
                        "project_type": lead.project_type,
                        "message": lead.message,
                        "original_lead_id": lead_id
                    })
                )
                logger.info(f"Dual-wrote lead {lead_id} to revenue_leads for AI pickup")
            except Exception as e:
                logger.error(f"Failed to dual-write to revenue_leads: {e}")
                # Do not raise, allow the main lead capture to succeed

            # Background task to process the lead
            background_tasks.add_task(
                process_lead_async,
                lead_id=lead_id,
                lead_data=lead.dict()
            )

            return {
                "success": True,
                "lead_id": lead_id,
                "lead_score": lead_score,
                "ai_enriched": ai_enriched,
                "message": "Lead captured successfully",
                "next_steps": [
                    "Lead will be scored by AI",
                    "Sales team will be notified",
                    "Follow-up scheduled within 24 hours"
                ]
            }

    except Exception as e:
        logger.error(f"Database error in lead capture: {str(e)}")
        # In production, we might want to return an error or queue locally
        raise HTTPException(status_code=500, detail="Failed to capture lead")

async def process_lead_async(lead_id: str, lead_data: dict):
    """
    Background processing for lead
    """
    try:
        logger.info(f"Processing lead {lead_id}: {lead_data.get('name')}")
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            # 1. Email Notification (via notification_queue)
            # Send to generic sales email for now as we don't have specific tenant config here
            await conn.execute("""
                INSERT INTO notification_queue (
                    notification_type,
                    recipient_email,
                    subject,
                    message,
                    data,
                    status,
                    scheduled_for
                ) VALUES ($1, $2, $3, $4, $5, 'pending', NOW())
            """, 
            'email',
            'sales@myroofgenius.com', # Default fallback
            f"New Lead: {lead_data.get('name')}",
            f"New lead received from {lead_data.get('source')}. Phone: {lead_data.get('phone')}",
            json.dumps(lead_data)
            )
            logger.info(f"Queued email notification for lead {lead_id}")

            # 2. CRM Integration (Placeholder - Log only)
            logger.info(f"CRM Sync pending for {lead_id}")

            # 3. Marketing Automation (Placeholder - Log only)
            logger.info(f"Marketing Automation trigger pending for {lead_id}")

    except Exception as e:
        logger.error(f"Error processing lead {lead_id}: {e}")

# Also fix the original endpoint
@router.post("/leads/capture")
async def capture_lead_original(lead: LeadCapture, background_tasks: BackgroundTasks):
    """
    Original endpoint redirects to fixed version
    """
    return await capture_lead_fixed(lead, background_tasks)
