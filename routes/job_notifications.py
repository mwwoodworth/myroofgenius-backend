"""
Job Notifications System
Handles notifications for job-related events
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
import json
from enum import Enum

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/notifications")

# ============================================================================
# NOTIFICATION TYPES AND MODELS
# ============================================================================

class NotificationType(str, Enum):
    STATUS_CHANGE = "status_change"
    ASSIGNMENT = "assignment"
    SCHEDULE_CHANGE = "schedule_change"
    TASK_COMPLETED = "task_completed"
    DOCUMENT_UPLOADED = "document_uploaded"
    COMMENT_ADDED = "comment_added"
    REMINDER = "reminder"
    DEADLINE_APPROACHING = "deadline_approaching"
    COST_OVERRUN = "cost_overrun"
    CUSTOMER_MESSAGE = "customer_message"
    SYSTEM_ALERT = "system_alert"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"
    SLACK = "slack"

class NotificationPreferences(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    slack_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    notification_types: Optional[List[NotificationType]] = None

class CreateNotification(BaseModel):
    job_id: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = {}
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    recipient_ids: Optional[List[str]] = None
    send_immediately: bool = True

class NotificationResponse(BaseModel):
    id: str
    job_id: str
    type: str
    priority: str
    title: str
    message: str
    metadata: Dict[str, Any]
    channels: List[str]
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    is_read: bool

# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@router.post("/{job_id}/send", response_model=dict)
async def send_job_notification(
    job_id: str,
    notification: CreateNotification,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Send a notification for a job"""
    try:
        # SECURITY: Verify job exists AND belongs to user's tenant
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        job = db.execute(
            text("SELECT id, job_number FROM jobs WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": job_id, "tenant_id": tenant_id}
        ).fetchone()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Create notification record
        notification_id = str(uuid4())

        # Store notification in database
        result = db.execute(
            text("""
                INSERT INTO job_notifications (
                    id, job_id, type, priority, title, message,
                    metadata, channels, created_by, created_at,
                    is_read, recipient_ids
                )
                VALUES (
                    :id, :job_id, :type, :priority, :title, :message,
                    :metadata::jsonb, :channels::jsonb, :created_by, NOW(),
                    false, :recipient_ids::jsonb
                )
                RETURNING id, created_at
            """),
            {
                "id": notification_id,
                "job_id": job_id,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "metadata": json.dumps(notification.metadata or {}),
                "channels": json.dumps([ch.value for ch in notification.channels]),
                "created_by": current_user["id"],
                "recipient_ids": json.dumps(notification.recipient_ids or [])
            }
        )
        db.commit()

        result = result.fetchone()

        # Send notification in background if requested
        if notification.send_immediately:
            background_tasks.add_task(
                process_notification,
                notification_id,
                notification.channels,
                db
            )

        return {
            "id": notification_id,
            "job_id": job_id,
            "status": "queued" if notification.send_immediately else "created",
            "created_at": result.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.get("/{job_id}/notifications", response_model=Dict[str, Any])
async def get_job_notifications(
    job_id: str,
    type: Optional[NotificationType] = None,
    priority: Optional[NotificationPriority] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get notifications for a job"""
    try:
        # SECURITY: Verify tenant access
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build query with tenant isolation via jobs table join
        query = """
            SELECT
                n.*,
                u.email as created_by_email
            FROM job_notifications n
            JOIN jobs j ON n.job_id = j.id AND j.tenant_id = :tenant_id
            LEFT JOIN users u ON n.created_by = u.id
            WHERE n.job_id = :job_id
        """
        params = {"job_id": job_id, "tenant_id": tenant_id}

        if type:
            query += " AND n.type = :type"
            params["type"] = type.value

        if priority:
            query += " AND n.priority = :priority"
            params["priority"] = priority.value

        if is_read is not None:
            query += " AND n.is_read = :is_read"
            params["is_read"] = is_read

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()

        # Get notifications
        query += " ORDER BY n.created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params)
        notifications = []

        for notif in result:
            notifications.append({
                "id": str(notif.id),
                "job_id": str(notif.job_id),
                "type": notif.type,
                "priority": notif.priority,
                "title": notif.title,
                "message": notif.message,
                "metadata": notif.metadata or {},
                "channels": notif.channels or [],
                "created_by": str(notif.created_by) if notif.created_by else None,
                "created_by_email": notif.created_by_email,
                "created_at": notif.created_at.isoformat(),
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "is_read": notif.is_read
            })

        return {
            "total": total,
            "notifications": notifications,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )

@router.put("/{job_id}/notifications/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    job_id: str,
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark a notification as read"""
    try:
        result = db.execute(
            text("""
                UPDATE job_notifications
                SET is_read = true,
                    read_at = NOW()
                WHERE id = :id AND job_id = :job_id
                RETURNING id, read_at
            """),
            {"id": notification_id, "job_id": job_id}
        )
        db.commit()

        notif = result.fetchone()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        return {
            "id": str(notif.id),
            "read_at": notif.read_at.isoformat(),
            "message": "Notification marked as read"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.post("/bulk-read", response_model=dict)
async def mark_multiple_notifications_read(
    notification_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark multiple notifications as read"""
    try:
        result = db.execute(
            text("""
                UPDATE job_notifications
                SET is_read = true,
                    read_at = NOW()
                WHERE id = ANY(:ids::uuid[])
                RETURNING id
            """),
            {"ids": notification_ids}
        )
        db.commit()

        updated_ids = [str(row.id) for row in result]

        return {
            "updated_count": len(updated_ids),
            "updated_ids": updated_ids,
            "message": f"Marked {len(updated_ids)} notifications as read"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> NotificationPreferences:
    """Get user's notification preferences"""
    try:
        result = db.execute(
            text("""
                SELECT * FROM user_notification_preferences
                WHERE user_id = :user_id
            """),
            {"user_id": current_user["id"]}
        ).fetchone()

        if result:
            return NotificationPreferences(
                email_enabled=result.email_enabled,
                sms_enabled=result.sms_enabled,
                push_enabled=result.push_enabled,
                slack_enabled=result.slack_enabled,
                quiet_hours_start=result.quiet_hours_start,
                quiet_hours_end=result.quiet_hours_end,
                notification_types=result.notification_types or []
            )
        else:
            # Return default preferences
            return NotificationPreferences()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )

@router.put("/preferences", response_model=dict)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update user's notification preferences"""
    try:
        # Upsert preferences
        db.execute(
            text("""
                INSERT INTO user_notification_preferences (
                    user_id, email_enabled, sms_enabled, push_enabled,
                    slack_enabled, quiet_hours_start, quiet_hours_end,
                    notification_types, updated_at
                )
                VALUES (
                    :user_id, :email_enabled, :sms_enabled, :push_enabled,
                    :slack_enabled, :quiet_hours_start, :quiet_hours_end,
                    :notification_types::jsonb, NOW()
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    email_enabled = EXCLUDED.email_enabled,
                    sms_enabled = EXCLUDED.sms_enabled,
                    push_enabled = EXCLUDED.push_enabled,
                    slack_enabled = EXCLUDED.slack_enabled,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    notification_types = EXCLUDED.notification_types,
                    updated_at = NOW()
            """),
            {
                "user_id": current_user["id"],
                "email_enabled": preferences.email_enabled,
                "sms_enabled": preferences.sms_enabled,
                "push_enabled": preferences.push_enabled,
                "slack_enabled": preferences.slack_enabled,
                "quiet_hours_start": preferences.quiet_hours_start,
                "quiet_hours_end": preferences.quiet_hours_end,
                "notification_types": json.dumps([t.value for t in preferences.notification_types] if preferences.notification_types else [])
            }
        )
        db.commit()

        return {"message": "Preferences updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

@router.get("/summary", response_model=Dict[str, Any])
async def get_notification_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get notification summary for current user"""
    try:
        # Get unread counts by type
        result = db.execute(
            text("""
                SELECT
                    type,
                    COUNT(*) as count,
                    MAX(priority) as max_priority
                FROM job_notifications
                WHERE (
                    created_by = :user_id
                    OR :user_id::text = ANY(recipient_ids::text[])
                )
                AND is_read = false
                GROUP BY type
            """),
            {"user_id": current_user["id"]}
        )

        by_type = {}
        for row in result:
            by_type[row.type] = {
                "count": row.count,
                "max_priority": row.max_priority
            }

        # Get total unread count
        total_unread = db.execute(
            text("""
                SELECT COUNT(*) FROM job_notifications
                WHERE (
                    created_by = :user_id
                    OR :user_id::text = ANY(recipient_ids::text[])
                )
                AND is_read = false
            """),
            {"user_id": current_user["id"]}
        ).scalar()

        # Get recent notifications
        recent = db.execute(
            text("""
                SELECT
                    n.*,
                    j.job_number
                FROM job_notifications n
                LEFT JOIN jobs j ON n.job_id = j.id
                WHERE (
                    n.created_by = :user_id
                    OR :user_id::text = ANY(n.recipient_ids::text[])
                )
                AND n.created_at > NOW() - INTERVAL '7 days'
                ORDER BY n.created_at DESC
                LIMIT 10
            """),
            {"user_id": current_user["id"]}
        )

        recent_notifications = []
        for notif in recent:
            recent_notifications.append({
                "id": str(notif.id),
                "job_id": str(notif.job_id),
                "job_number": notif.job_number,
                "type": notif.type,
                "priority": notif.priority,
                "title": notif.title,
                "created_at": notif.created_at.isoformat(),
                "is_read": notif.is_read
            })

        return {
            "total_unread": total_unread,
            "by_type": by_type,
            "recent_notifications": recent_notifications
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification summary: {str(e)}"
        )

# ============================================================================
# BACKGROUND TASK FUNCTIONS
# ============================================================================

def process_notification(
    notification_id: str,
    channels: List[NotificationChannel],
    db: Session
):
    """Process and send notification through specified channels"""
    try:
        # In production, this would integrate with:
        # - Email service (SendGrid, AWS SES)
        # - SMS service (Twilio)
        # - Push notification service (Firebase, OneSignal)
        # - Slack API

        # For now, just mark as sent
        db.execute(
            text("""
                UPDATE job_notifications
                SET sent_at = NOW()
                WHERE id = :id
            """),
            {"id": notification_id}
        )
        db.commit()

    except Exception as e:
        # Log error but don't raise to avoid breaking background task
        print(f"Error processing notification {notification_id}: {str(e)}")

@router.post("/setup-automated-notifications", response_model=dict)
async def setup_automated_notifications(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Setup automated notifications for common job events"""
    try:
        # Create notification rules for the job
        rules = [
            {
                "event": "status_change",
                "template": "Job {{job_number}} status changed to {{new_status}}",
                "priority": "medium"
            },
            {
                "event": "deadline_approaching",
                "template": "Job {{job_number}} deadline is in {{days}} days",
                "priority": "high"
            },
            {
                "event": "cost_overrun",
                "template": "Job {{job_number}} costs exceed budget by {{percentage}}%",
                "priority": "urgent"
            }
        ]

        for rule in rules:
            db.execute(
                text("""
                    INSERT INTO job_notification_rules (
                        job_id, event_type, template, priority,
                        created_by, created_at, is_active
                    )
                    VALUES (
                        :job_id, :event_type, :template, :priority,
                        :created_by, NOW(), true
                    )
                    ON CONFLICT (job_id, event_type) DO UPDATE SET
                        template = EXCLUDED.template,
                        priority = EXCLUDED.priority,
                        is_active = true
                """),
                {
                    "job_id": job_id,
                    "event_type": rule["event"],
                    "template": rule["template"],
                    "priority": rule["priority"],
                    "created_by": current_user["id"]
                }
            )

        db.commit()

        return {
            "message": f"Automated notifications setup for job {job_id}",
            "rules_created": len(rules)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup automated notifications: {str(e)} RETURNING *"
        )