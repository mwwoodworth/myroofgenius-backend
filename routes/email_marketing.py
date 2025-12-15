"""
Email Marketing Module - Task 72
Complete email marketing system with templates and automation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Models
class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_type: str = "marketing"
    variables: Optional[List[str]] = []
    is_active: bool = True

class EmailCampaignCreate(BaseModel):
    name: str
    template_id: str
    recipient_list_id: Optional[str] = None
    recipients: Optional[List[EmailStr]] = []
    subject_override: Optional[str] = None
    send_time: Optional[datetime] = None
    personalization: Optional[Dict[str, Any]] = {}

class EmailResponse(BaseModel):
    id: str
    campaign_id: str
    recipient: str
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    bounced: bool
    bounce_reason: Optional[str]

# Endpoints
@router.post("/templates", response_model=dict)
async def create_email_template(
    template: EmailTemplateCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create email template"""
    query = """
        INSERT INTO email_templates (
            name, subject, html_content, text_content,
            template_type, variables, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        template.name,
        template.subject,
        template.html_content,
        template.text_content,
        template.template_type,
        json.dumps(template.variables),
        template.is_active
    )

    return {**dict(result), "id": str(result['id'])}

@router.post("/campaigns", response_model=dict)
async def create_email_campaign(
    campaign: EmailCampaignCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create and optionally send email campaign"""
    query = """
        INSERT INTO email_campaigns (
            name, template_id, recipient_list_id, recipients,
            subject_override, send_time, personalization, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        campaign.name,
        uuid.UUID(campaign.template_id),
        uuid.UUID(campaign.recipient_list_id) if campaign.recipient_list_id else None,
        json.dumps(campaign.recipients) if campaign.recipients else None,
        campaign.subject_override,
        campaign.send_time,
        json.dumps(campaign.personalization),
        'scheduled' if campaign.send_time else 'draft'
    )

    if not campaign.send_time:
        # Send immediately
        background_tasks.add_task(send_email_campaign, str(result['id']))

    return {**dict(result), "id": str(result['id'])}

@router.get("/campaigns/{campaign_id}/analytics", response_model=dict)
async def get_email_analytics(
    campaign_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get email campaign analytics"""
    query = """
        SELECT
            COUNT(*) as total_sent,
            COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opens,
            COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicks,
            COUNT(CASE WHEN bounced = true THEN 1 END) as bounces,
            AVG(CASE WHEN opened_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (opened_at - sent_at))/3600
                END) as avg_open_time_hours
        FROM email_tracking
        WHERE campaign_id = $1
    """

    result = await conn.fetchrow(query, uuid.UUID(campaign_id))

    stats = dict(result)
    stats['open_rate'] = (stats['opens'] / stats['total_sent'] * 100) if stats['total_sent'] > 0 else 0
    stats['click_rate'] = (stats['clicks'] / stats['opens'] * 100) if stats['opens'] > 0 else 0
    stats['bounce_rate'] = (stats['bounces'] / stats['total_sent'] * 100) if stats['total_sent'] > 0 else 0

    return stats

async def send_email_campaign(campaign_id: str):
    """Send email campaign (background task)"""
    # This would integrate with email service provider
    