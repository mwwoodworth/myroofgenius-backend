"""
Payment Reminders Module
Task 34: Payment reminders implementation

Automated payment reminder system with customizable templates,
scheduling, and multi-channel delivery (email, SMS, in-app).
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import json
import uuid
import asyncpg
import os
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

router = APIRouter()

# ==================== Enums ====================

class ReminderType(str, Enum):
    PAYMENT_DUE = "payment_due"
    OVERDUE = "overdue"
    FINAL_NOTICE = "final_notice"
    PAYMENT_PLAN = "payment_plan"
    UPCOMING_INSTALLMENT = "upcoming_installment"
    FAILED_PAYMENT = "failed_payment"
    THANK_YOU = "thank_you"

class ReminderChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PHONE = "phone"
    MAIL = "mail"

class ReminderStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"

class ReminderFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

# ==================== Pydantic Models ====================

class ReminderTemplate(BaseModel):
    """Reminder template configuration"""
    name: str = Field(description="Template name")
    type: ReminderType = Field(description="Reminder type")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Message body with placeholders")
    sms_message: Optional[str] = Field(default=None, description="SMS version of message")
    days_before_due: int = Field(default=3, description="Days before due date to send")
    is_active: bool = Field(default=True)

class ReminderSchedule(BaseModel):
    """Reminder scheduling configuration"""
    invoice_id: str = Field(description="Invoice ID")
    reminder_type: ReminderType
    send_date: date = Field(description="Date to send reminder")
    send_time: Optional[str] = Field(default="09:00", description="Time to send (HH:MM)")
    channels: List[ReminderChannel] = Field(default=[ReminderChannel.EMAIL])
    template_id: Optional[str] = None
    custom_message: Optional[str] = None

class BulkReminderRequest(BaseModel):
    """Bulk reminder sending request"""
    reminder_type: ReminderType
    filter_status: Optional[str] = Field(default=None, description="Filter by invoice status")
    days_overdue_min: Optional[int] = Field(default=None, ge=0)
    days_overdue_max: Optional[int] = Field(default=None, ge=0)
    min_amount: Optional[float] = Field(default=None, gt=0)
    customer_ids: Optional[List[str]] = None
    exclude_customer_ids: Optional[List[str]] = None
    channels: List[ReminderChannel] = Field(default=[ReminderChannel.EMAIL])
    test_mode: bool = Field(default=False, description="Preview without sending")

class ReminderSettings(BaseModel):
    """Customer reminder preferences"""
    customer_id: str
    enable_reminders: bool = Field(default=True)
    preferred_channel: ReminderChannel = Field(default=ReminderChannel.EMAIL)
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    reminder_frequency: ReminderFrequency = Field(default=ReminderFrequency.WEEKLY)
    quiet_hours_start: Optional[str] = Field(default="20:00")
    quiet_hours_end: Optional[str] = Field(default="09:00")
    language: str = Field(default="en")
    timezone: str = Field(default="America/New_York")

class ReminderCampaign(BaseModel):
    """Automated reminder campaign"""
    name: str = Field(description="Campaign name")
    description: Optional[str] = None
    trigger_conditions: Dict[str, Any] = Field(description="Conditions to trigger campaign")
    reminder_sequence: List[Dict[str, Any]] = Field(description="Sequence of reminders")
    is_active: bool = Field(default=True)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Reminder Templates ====================

@router.post("/templates", tags=["Payment Reminders"])
async def create_reminder_template(template: ReminderTemplate):
    """Create a reminder template"""
    try:
        conn = await get_db_connection()
        try:
            template_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO reminder_templates (
                    id, name, type, subject, body, sms_message,
                    days_before_due, is_active, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            """, uuid.UUID(template_id), template.name, template.type.value,
                template.subject, template.body, template.sms_message,
                template.days_before_due, template.is_active)
            
            return {
                "success": True,
                "template_id": template_id,
                "message": f"Template '{template.name}' created successfully"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", tags=["Payment Reminders"])
async def list_reminder_templates(
    type: Optional[ReminderType] = None,
    is_active: bool = True
):
    """List reminder templates"""
    try:
        conn = await get_db_connection()
        try:
            query = "SELECT * FROM reminder_templates WHERE is_active = $1"
            params = [is_active]
            
            if type:
                query += " AND type = $2"
                params.append(type.value)
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            return {
                "templates": [
                    {
                        "id": str(row['id']),
                        "name": row['name'],
                        "type": row['type'],
                        "subject": row['subject'],
                        "body": row['body'],
                        "sms_message": row['sms_message'],
                        "days_before_due": row['days_before_due'],
                        "is_active": row['is_active'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None
                    }
                    for row in rows
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Reminder Scheduling ====================

@router.post("/schedule", tags=["Payment Reminders"])
async def schedule_reminder(
    schedule: ReminderSchedule,
    background_tasks: BackgroundTasks
):
    """Schedule a payment reminder"""
    try:
        conn = await get_db_connection()
        try:
            # Verify invoice exists
            invoice = await conn.fetchrow("""
                SELECT i.*, c.email, c.phone
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.id = $1
            """, uuid.UUID(schedule.invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Create reminder record
            reminder_id = str(uuid.uuid4())
            scheduled_time = datetime.combine(
                schedule.send_date,
                datetime.strptime(schedule.send_time, "%H:%M").time()
            )
            
            await conn.execute("""
                INSERT INTO payment_reminders (
                    id, invoice_id, reminder_type, scheduled_time,
                    channels, template_id, custom_message, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, uuid.UUID(reminder_id), uuid.UUID(schedule.invoice_id),
                schedule.reminder_type.value, scheduled_time,
                json.dumps([c.value for c in schedule.channels]),
                uuid.UUID(schedule.template_id) if schedule.template_id else None,
                schedule.custom_message, ReminderStatus.SCHEDULED.value)
            
            # Schedule background task if immediate
            if schedule.send_date <= date.today():
                background_tasks.add_task(
                    send_reminder,
                    reminder_id,
                    invoice['email'],
                    invoice['phone']
                )
            
            return {
                "success": True,
                "reminder_id": reminder_id,
                "scheduled_time": scheduled_time.isoformat(),
                "message": f"Reminder scheduled for {schedule.send_date}"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-bulk", tags=["Payment Reminders"])
async def send_bulk_reminders(
    request: BulkReminderRequest,
    background_tasks: BackgroundTasks
):
    """Send bulk payment reminders"""
    try:
        conn = await get_db_connection()
        try:
            # Build query for target invoices
            query = """
                SELECT i.*, c.email, c.phone, c.customer_name
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.balance_cents > 0
            """
            params = []
            param_count = 0
            
            if request.filter_status:
                param_count += 1
                query += f" AND i.status = ${param_count}"
                params.append(request.filter_status)
            
            if request.days_overdue_min is not None:
                param_count += 1
                query += f" AND i.due_date <= CURRENT_DATE - INTERVAL '${param_count} days'"
                params.append(request.days_overdue_min)
            
            if request.min_amount:
                param_count += 1
                query += f" AND i.balance_cents >= ${param_count}"
                params.append(int(request.min_amount * 100))
            
            if request.customer_ids:
                param_count += 1
                query += f" AND i.customer_id = ANY(${param_count}::uuid[])"
                params.append([uuid.UUID(cid) for cid in request.customer_ids])
            
            if request.exclude_customer_ids:
                param_count += 1
                query += f" AND i.customer_id != ALL(${param_count}::uuid[])"
                params.append([uuid.UUID(cid) for cid in request.exclude_customer_ids])
            
            invoices = await conn.fetch(query, *params)
            
            if request.test_mode:
                # Return preview without sending
                return {
                    "test_mode": True,
                    "total_invoices": len(invoices),
                    "total_amount": sum(i['balance_cents'] for i in invoices) / 100,
                    "invoices": [
                        {
                            "invoice_number": inv['invoice_number'],
                            "customer_name": inv['customer_name'],
                            "balance": inv['balance_cents'] / 100,
                            "days_overdue": (date.today() - inv['due_date']).days if inv['due_date'] < date.today() else 0
                        }
                        for inv in invoices[:10]  # Limit preview
                    ]
                }
            
            # Send reminders
            sent_count = 0
            failed_count = 0
            
            for invoice in invoices:
                try:
                    reminder_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO payment_reminders (
                            id, invoice_id, reminder_type, scheduled_time,
                            channels, status, sent_at
                        ) VALUES ($1, $2, $3, NOW(), $4, $5, NOW())
                    """, uuid.UUID(reminder_id), invoice['id'],
                        request.reminder_type.value,
                        json.dumps([c.value for c in request.channels]),
                        ReminderStatus.SENT.value)
                    
                    # Queue background task
                    background_tasks.add_task(
                        send_reminder,
                        reminder_id,
                        invoice['email'],
                        invoice['phone']
                    )
                    
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send reminder for invoice {invoice['id']}: {e}")
                    failed_count += 1
            
            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_amount_reminded": sum(i['balance_cents'] for i in invoices[:sent_count]) / 100,
                "message": f"Sent {sent_count} reminders successfully"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error sending bulk reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Reminder Settings ====================

@router.post("/settings", tags=["Payment Reminders"])
async def update_reminder_settings(settings: ReminderSettings):
    """Update customer reminder preferences"""
    try:
        conn = await get_db_connection()
        try:
            # Upsert settings
            await conn.execute("""
                INSERT INTO customer_reminder_settings (
                    id, customer_id, enable_reminders, preferred_channel,
                    email_address, phone_number, reminder_frequency,
                    quiet_hours_start, quiet_hours_end, language, timezone
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (customer_id) DO UPDATE SET
                    enable_reminders = $3,
                    preferred_channel = $4,
                    email_address = $5,
                    phone_number = $6,
                    reminder_frequency = $7,
                    quiet_hours_start = $8,
                    quiet_hours_end = $9,
                    language = $10,
                    timezone = $11,
                    updated_at = NOW()
            """, uuid.uuid4(), uuid.UUID(settings.customer_id),
                settings.enable_reminders, settings.preferred_channel.value,
                settings.email_address, settings.phone_number,
                settings.reminder_frequency.value,
                settings.quiet_hours_start, settings.quiet_hours_end,
                settings.language, settings.timezone)
            
            return {
                "success": True,
                "message": "Reminder settings updated successfully"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/{customer_id}", tags=["Payment Reminders"])
async def get_reminder_settings(customer_id: str):
    """Get customer reminder preferences"""
    try:
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow("""
                SELECT * FROM customer_reminder_settings
                WHERE customer_id = $1
            """, uuid.UUID(customer_id))
            
            if not row:
                # Return defaults
                return {
                    "customer_id": customer_id,
                    "enable_reminders": True,
                    "preferred_channel": "email",
                    "reminder_frequency": "weekly",
                    "quiet_hours_start": "20:00",
                    "quiet_hours_end": "09:00",
                    "language": "en",
                    "timezone": "America/New_York"
                }
            
            return {
                "customer_id": str(row['customer_id']),
                "enable_reminders": row['enable_reminders'],
                "preferred_channel": row['preferred_channel'],
                "email_address": row['email_address'],
                "phone_number": row['phone_number'],
                "reminder_frequency": row['reminder_frequency'],
                "quiet_hours_start": row['quiet_hours_start'],
                "quiet_hours_end": row['quiet_hours_end'],
                "language": row['language'],
                "timezone": row['timezone']
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Reminder History ====================

@router.get("/history/{invoice_id}", tags=["Payment Reminders"])
async def get_reminder_history(invoice_id: str):
    """Get reminder history for an invoice"""
    try:
        conn = await get_db_connection()
        try:
            reminders = await conn.fetch("""
                SELECT * FROM payment_reminders
                WHERE invoice_id = $1
                ORDER BY created_at DESC
            """, uuid.UUID(invoice_id))
            
            return {
                "invoice_id": invoice_id,
                "total_reminders": len(reminders),
                "reminders": [
                    {
                        "id": str(r['id']),
                        "type": r['reminder_type'],
                        "scheduled_time": r['scheduled_time'].isoformat() if r['scheduled_time'] else None,
                        "sent_at": r['sent_at'].isoformat() if r['sent_at'] else None,
                        "channels": json.loads(r['channels']) if r['channels'] else [],
                        "status": r['status'],
                        "opened_at": r['opened_at'].isoformat() if r['opened_at'] else None,
                        "clicked_at": r['clicked_at'].isoformat() if r['clicked_at'] else None
                    }
                    for r in reminders
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting reminder history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", tags=["Payment Reminders"])
async def get_reminder_statistics(
    start_date: date,
    end_date: date
):
    """Get reminder statistics for a date range"""
    try:
        conn = await get_db_connection()
        try:
            # Overall statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
                    COUNT(DISTINCT invoice_id) as unique_invoices
                FROM payment_reminders
                WHERE sent_at BETWEEN $1 AND $2
            """, start_date, end_date)
            
            # By type breakdown
            by_type = await conn.fetch("""
                SELECT 
                    reminder_type,
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered
                FROM payment_reminders
                WHERE sent_at BETWEEN $1 AND $2
                GROUP BY reminder_type
            """, start_date, end_date)
            
            # Payment conversion
            conversion = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT pr.invoice_id) as reminded_invoices,
                    COUNT(DISTINCT CASE 
                        WHEN p.payment_date >= pr.sent_at 
                        AND p.payment_date <= pr.sent_at + INTERVAL '7 days'
                        THEN pr.invoice_id 
                    END) as paid_within_week
                FROM payment_reminders pr
                LEFT JOIN invoice_payments p ON pr.invoice_id = p.invoice_id
                WHERE pr.sent_at BETWEEN $1 AND $2
            """, start_date, end_date)
            
            conversion_rate = 0
            if conversion['reminded_invoices'] > 0:
                conversion_rate = (conversion['paid_within_week'] / conversion['reminded_invoices']) * 100
            
            return {
                "date_range": f"{start_date} to {end_date}",
                "summary": {
                    "total_sent": stats['total_sent'],
                    "delivery_rate": (stats['delivered'] / stats['total_sent'] * 100) if stats['total_sent'] > 0 else 0,
                    "open_rate": (stats['opened'] / stats['delivered'] * 100) if stats['delivered'] > 0 else 0,
                    "click_rate": (stats['clicked'] / stats['opened'] * 100) if stats['opened'] > 0 else 0,
                    "unique_invoices": stats['unique_invoices'],
                    "conversion_rate": conversion_rate
                },
                "by_type": [
                    {
                        "type": t['reminder_type'],
                        "count": t['count'],
                        "delivery_rate": (t['delivered'] / t['count'] * 100) if t['count'] > 0 else 0
                    }
                    for t in by_type
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Automated Campaigns ====================

@router.post("/campaigns", tags=["Payment Reminders"])
async def create_reminder_campaign(campaign: ReminderCampaign):
    """Create an automated reminder campaign"""
    try:
        conn = await get_db_connection()
        try:
            campaign_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO reminder_campaigns (
                    id, name, description, trigger_conditions,
                    reminder_sequence, is_active, start_date, end_date
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, uuid.UUID(campaign_id), campaign.name, campaign.description,
                json.dumps(campaign.trigger_conditions),
                json.dumps(campaign.reminder_sequence),
                campaign.is_active, campaign.start_date, campaign.end_date)
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "message": f"Campaign '{campaign.name}' created successfully"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns", tags=["Payment Reminders"])
async def list_reminder_campaigns(is_active: bool = True):
    """List reminder campaigns"""
    try:
        conn = await get_db_connection()
        try:
            campaigns = await conn.fetch("""
                SELECT * FROM reminder_campaigns
                WHERE is_active = $1
                ORDER BY created_at DESC
            """, is_active)
            
            return {
                "campaigns": [
                    {
                        "id": str(c['id']),
                        "name": c['name'],
                        "description": c['description'],
                        "trigger_conditions": json.loads(c['trigger_conditions']),
                        "reminder_sequence": json.loads(c['reminder_sequence']),
                        "is_active": c['is_active'],
                        "start_date": c['start_date'].isoformat() if c['start_date'] else None,
                        "end_date": c['end_date'].isoformat() if c['end_date'] else None,
                        "created_at": c['created_at'].isoformat() if c['created_at'] else None
                    }
                    for c in campaigns
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/activate", tags=["Payment Reminders"])
async def activate_campaign(campaign_id: str):
    """Activate/deactivate a reminder campaign"""
    try:
        conn = await get_db_connection()
        try:
            # Toggle activation status
            result = await conn.fetchval("""
                UPDATE reminder_campaigns
                SET is_active = NOT is_active,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING is_active
            """, uuid.UUID(campaign_id))
            
            if result is None:
                raise HTTPException(status_code=404, detail="Campaign not found")
            
            return {
                "success": True,
                "is_active": result,
                "message": f"Campaign {'activated' if result else 'deactivated'} successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Webhook Handlers ====================

@router.post("/webhook/email-status", tags=["Payment Reminders"])
async def handle_email_status_webhook(data: Dict[str, Any]):
    """Handle email delivery status webhooks"""
    try:
        conn = await get_db_connection()
        try:
            reminder_id = data.get('reminder_id')
            event_type = data.get('event')
            
            if event_type == 'delivered':
                await conn.execute("""
                    UPDATE payment_reminders
                    SET status = 'delivered',
                        delivered_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(reminder_id))
            elif event_type == 'opened':
                await conn.execute("""
                    UPDATE payment_reminders
                    SET opened_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(reminder_id))
            elif event_type == 'clicked':
                await conn.execute("""
                    UPDATE payment_reminders
                    SET clicked_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(reminder_id))
            elif event_type == 'bounced':
                await conn.execute("""
                    UPDATE payment_reminders
                    SET status = 'bounced'
                    WHERE id = $1
                """, uuid.UUID(reminder_id))
            
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

# ==================== Helper Functions ====================

async def send_reminder(reminder_id: str, email: str, phone: str):
    """Send a payment reminder (placeholder)"""
    logger.info(f"Sending reminder {reminder_id} to {email}")
    # Actual sending implementation would go here
    # This would integrate with email service, SMS provider, etc.

async def process_scheduled_reminders():
    """Process scheduled reminders (to be called by cron/scheduler)"""
    try:
        conn = await get_db_connection()
        try:
            # Get due reminders
            reminders = await conn.fetch("""
                SELECT r.*, i.*, c.email, c.phone
                FROM payment_reminders r
                JOIN invoices i ON r.invoice_id = i.id
                JOIN customers c ON i.customer_id = c.id
                WHERE r.status = 'scheduled'
                    AND r.scheduled_time <= NOW()
            """)
            
            for reminder in reminders:
                try:
                    # Send reminder
                    await send_reminder(
                        str(reminder['id']),
                        reminder['email'],
                        reminder['phone']
                    )
                    
                    # Update status
                    await conn.execute("""
                        UPDATE payment_reminders
                        SET status = 'sent',
                            sent_at = NOW()
                        WHERE id = $1
                    """, reminder['id'])
                except Exception as e:
                    logger.error(f"Failed to send reminder {reminder['id']}: {e}")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error processing scheduled reminders: {str(e)}")

def generate_reminder_message(template: str, invoice_data: Dict[str, Any]) -> str:
    """Generate reminder message from template"""
    # Replace placeholders in template
    message = template
    replacements = {
        "{customer_name}": invoice_data.get('customer_name', 'Customer'),
        "{invoice_number}": invoice_data.get('invoice_number', ''),
        "{amount_due}": f"${invoice_data.get('balance_cents', 0) / 100:.2f}",
        "{due_date}": invoice_data.get('due_date', '').isoformat() if invoice_data.get('due_date') else '',
        "{days_overdue}": str((date.today() - invoice_data.get('due_date')).days) if invoice_data.get('due_date') and invoice_data.get('due_date') < date.today() else '0',
        "{payment_link}": f"https://pay.example.com/invoice/{invoice_data.get('id', '')} RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *"
    }
    
    for key, value in replacements.items():
        message = message.replace(key, value)
    
    return message