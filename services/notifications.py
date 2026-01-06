# WeatherCraft ERP - Notification Service
# Handles email, SMS, and push notifications

import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from sqlalchemy import text
from sqlalchemy.orm import Session
import aiohttp

logger = logging.getLogger(__name__)

def _merge_config(base: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(base)
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                merged[key] = value
    return merged


def _default_email_config() -> Dict[str, Any]:
    return {
        "sendgrid_api_key": os.getenv("SENDGRID_API_KEY"),
        "sendgrid_from_email": os.getenv("SENDGRID_FROM_EMAIL"),
        "sendgrid_from_name": os.getenv("SENDGRID_FROM_NAME"),
        "smtp_server": os.getenv("SMTP_SERVER"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME"),
        "smtp_password": os.getenv("SMTP_PASSWORD"),
        "smtp_from_email": os.getenv("SMTP_FROM_EMAIL"),
        "smtp_from_name": os.getenv("SMTP_FROM_NAME"),
        "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
    }


def _default_sms_config() -> Dict[str, Any]:
    return {
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
        "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER"),
    }


def _default_push_config() -> Dict[str, Any]:
    return {
        "push_webhook_url": os.getenv("PUSH_WEBHOOK_URL"),
        "push_webhook_token": os.getenv("PUSH_WEBHOOK_TOKEN"),
    }


def _format_from_address(email: Optional[str], name: Optional[str]) -> Optional[str]:
    if not email:
        return None
    if name:
        return f"{name} <{email}>"
    return email


def _send_via_sendgrid_sync(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str],
    config: Dict[str, Any],
) -> bool:
    api_key = config.get("sendgrid_api_key")
    from_email = _format_from_address(
        config.get("sendgrid_from_email"),
        config.get("sendgrid_from_name"),
    )
    if not api_key or not from_email:
        logger.error("SendGrid not configured: missing API key or from address")
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except Exception as exc:
        logger.error("SendGrid dependency missing: %s", exc)
        return False

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content or text_content or "",
    )
    if text_content:
        message.plain_text_content = text_content

    try:
        client = SendGridAPIClient(api_key)
        response = client.send(message)
        if 200 <= response.status_code < 300:
            return True
        logger.error("SendGrid send failed: status=%s", response.status_code)
        return False
    except Exception as exc:
        logger.error("SendGrid send failed: %s", exc)
        return False


def _send_via_smtp_sync(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str],
    config: Dict[str, Any],
) -> bool:
    server = config.get("smtp_server")
    port = config.get("smtp_port")
    username = config.get("smtp_username")
    password = config.get("smtp_password")
    use_tls = bool(config.get("smtp_use_tls", True))
    from_email = _format_from_address(
        config.get("smtp_from_email"),
        config.get("smtp_from_name"),
    )
    if not server or not from_email:
        logger.error("SMTP not configured: missing server or from address")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, "plain"))
    if html_content:
        msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(server, port) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return False


def send_email_message(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send an email using SendGrid or SMTP based on configuration."""
    merged = _merge_config(_default_email_config(), config or {})
    if merged.get("sendgrid_api_key"):
        return _send_via_sendgrid_sync(to_email, subject, html_content, text_content, merged)
    if merged.get("smtp_server"):
        return _send_via_smtp_sync(to_email, subject, html_content, text_content, merged)
    logger.error("Email provider not configured")
    return False


async def send_sms_message(
    to_phone: str,
    message: str,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send SMS via Twilio when configured."""
    merged = _merge_config(_default_sms_config(), config or {})
    account_sid = merged.get("twilio_account_sid")
    auth_token = merged.get("twilio_auth_token")
    from_number = merged.get("twilio_from_number")
    if not account_sid or not auth_token or not from_number:
        logger.error("Twilio not configured: missing credentials or from number")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = {"To": to_phone, "From": from_number, "Body": message}
    try:
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(account_sid, auth_token)) as session:
            async with session.post(url, data=payload) as response:
                if 200 <= response.status < 300:
                    return True
                body = await response.text()
                logger.error("Twilio send failed: status=%s body=%s", response.status, body)
                return False
    except Exception as exc:
        logger.error("Twilio send failed: %s", exc)
        return False


async def send_push_message(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send push notification via webhook when configured."""
    merged = _merge_config(_default_push_config(), config or {})
    webhook_url = merged.get("push_webhook_url")
    token = merged.get("push_webhook_token")
    if not webhook_url:
        logger.error("Push webhook not configured")
        return False

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"message": message, "data": data or {}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if 200 <= response.status < 300:
                    return True
                body = await response.text()
                logger.error("Push webhook failed: status=%s body=%s", response.status, body)
                return False
    except Exception as exc:
        logger.error("Push webhook failed: %s", exc)
        return False

class NotificationService:
    """Comprehensive notification service for all communication channels"""
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        self.db = db
        self.config = config or {}
        self.email_config = _merge_config(_default_email_config(), self.config.get('email'))
        self.sms_config = _merge_config(_default_sms_config(), self.config.get('sms'))
        self.push_config = _merge_config(_default_push_config(), self.config.get('push'))
    
    async def process_queue(self):
        """Process pending notifications from queue"""
        try:
            # Get pending notifications
            query = """
            SELECT * FROM notification_queue
            WHERE status = 'pending'
            AND scheduled_for <= NOW()
            ORDER BY scheduled_for
            LIMIT 50
            """
            
            result = self.db.execute(text(query))
            notifications = [dict(row) for row in result]
            
            for notification in notifications:
                await self._process_notification(notification)
            
            return len(notifications)
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
            return 0
    
    async def _process_notification(self, notification: Dict):
        """Process a single notification"""
        try:
            # Update status to sending
            self._update_notification_status(notification['id'], 'sending')
            
            # Send based on type
            if notification['notification_type'] == 'email':
                success = await self._send_email(notification)
            elif notification['notification_type'] == 'sms':
                success = await self._send_sms(notification)
            elif notification['notification_type'] == 'push':
                success = await self._send_push(notification)
            else:
                logger.warning(f"Unknown notification type: {notification['notification_type']}")
                success = False
            
            # Update status
            if success:
                self._update_notification_status(notification['id'], 'sent', sent_at=datetime.now())
            else:
                self._update_notification_status(
                    notification['id'], 
                    'failed', 
                    error="Failed to send notification"
                )
            
        except Exception as e:
            logger.error(f"Error processing notification {notification['id']}: {e}")
            self._update_notification_status(notification['id'], 'failed', error=str(e))
    
    async def _send_email(self, notification: Dict) -> bool:
        """Send email notification"""
        try:
            recipient = notification.get('recipient_email')
            if not recipient:
                logger.error("Notification missing recipient_email")
                return False
            # Get template if specified
            if notification.get('template_id'):
                template = self._get_email_template(notification['template_id'])
                if template:
                    subject = self._render_template(template['subject'], notification.get('data', {}))
                    html_body = self._render_template(template['html_body'], notification.get('data', {}))
                    text_body = self._render_template(template['text_body'], notification.get('data', {}))
                else:
                    subject = notification.get('subject', 'Notification')
                    html_body = notification.get('message', '')
                    text_body = notification.get('message', '')
            else:
                subject = notification.get('subject', 'Notification')
                html_body = notification.get('message', '')
                text_body = notification.get('message', '')

            return await asyncio.to_thread(
                send_email_message,
                recipient,
                subject,
                html_body,
                text_body,
                self.email_config,
            )
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def _send_sms(self, notification: Dict) -> bool:
        """Send SMS notification"""
        try:
            phone = notification.get('recipient_phone')
            message = notification.get('message')
            if not phone or not message:
                logger.error("Notification missing recipient_phone or message")
                return False

            return await send_sms_message(phone, message, self.sms_config)
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def _send_push(self, notification: Dict) -> bool:
        """Send push notification"""
        try:
            message = notification.get('message', '')
            if not message:
                logger.error("Notification missing message for push")
                return False
            payload = notification.get('data') if isinstance(notification.get('data'), dict) else {}
            return await send_push_message(message, payload, self.push_config)
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str):
        """Send email via SendGrid API"""
        return await asyncio.to_thread(
            _send_via_sendgrid_sync,
            to_email,
            subject,
            html_content,
            None,
            self.email_config,
        )
    
    async def _send_via_twilio(self, to_phone: str, message: str):
        """Send SMS via Twilio API"""
        return await send_sms_message(to_phone, message, self.sms_config)
    
    def _get_email_template(self, template_id: str) -> Optional[Dict]:
        """Get email template from database"""
        query = "SELECT * FROM email_templates WHERE id = :template_id"
        result = self.db.execute(text(query), {'template_id': template_id})
        row = result.fetchone()
        return dict(row) if row else None
    
    def _render_template(self, template: str, data: Dict) -> str:
        """Render template with data"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                data = {}
        
        # Simple template rendering - replace {{variable}} with values
        import re
        pattern = r'\{\{(\w+)\}\}'
        
        def replace(match):
            key = match.group(1)
            return str(data.get(key, ''))
        
        return re.sub(pattern, replace, template)
    
    def _update_notification_status(
        self, 
        notification_id: str, 
        status: str, 
        sent_at: Optional[datetime] = None,
        error: Optional[str] = None
    ):
        """Update notification status in database"""
        query = """
        UPDATE notification_queue
        SET status = :status,
            sent_at = :sent_at,
            error_message = :error,
            attempts = attempts + 1
        WHERE id = :id
        """
        
        self.db.execute(text(query), {
            'id': notification_id,
            'status': status,
            'sent_at': sent_at,
            'error': error
        })
        self.db.commit()
    
    async def send_lead_notification(self, lead_id: str, notification_type: str):
        """Send notification for lead events"""
        # Get lead data
        query = """
        SELECT l.*, c.name as customer_name, c.email, c.phone
        FROM leads l
        LEFT JOIN customers c ON l.customer_id = c.id
        WHERE l.id = :lead_id
        """
        
        result = self.db.execute(text(query), {'lead_id': lead_id})
        lead = result.fetchone()
        
        if not lead:
            return
        
        lead_data = dict(lead)
        
        # Determine notification based on type
        if notification_type == 'new_lead':
            await self._queue_notification(
                'email',
                self.config.get('sales_email', 'sales@weathercraft.com'),
                subject=f"New Lead: {lead_data.get('customer_name', 'Unknown')}",
                message=f"A new lead has been created with score {lead_data.get('score', 0)}",
                data=lead_data
            )
        elif notification_type == 'lead_assigned':
            # Notify assigned user
            if lead_data.get('assigned_to'):
                user_query = "SELECT email FROM users WHERE id = :user_id"
                user_result = self.db.execute(text(user_query), {'user_id': lead_data['assigned_to']})
                user = user_result.fetchone()
                
                if user:
                    await self._queue_notification(
                        'email',
                        user['email'],
                        subject=f"Lead Assigned: {lead_data.get('customer_name', 'Unknown')}",
                        message="You have been assigned a new lead",
                        data=lead_data
                    )
    
    async def send_job_notification(self, job_id: str, notification_type: str):
        """Send notification for job events"""
        # Get job data
        query = """
        SELECT j.*, c.name as customer_name, c.email, c.phone
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        WHERE j.id = :job_id
        """
        
        result = self.db.execute(text(query), {'job_id': job_id})
        job = result.fetchone()
        
        if not job:
            return
        
        job_data = dict(job)
        
        # Send appropriate notification
        if notification_type == 'job_scheduled':
            if job_data.get('email'):
                await self._queue_notification(
                    'email',
                    job_data['email'],
                    subject=f"Job Scheduled: {job_data['job_number']}",
                    message=f"Your roofing job has been scheduled for {job_data.get('start_date', 'TBD')}",
                    data=job_data
                )
        elif notification_type == 'job_completed':
            if job_data.get('email'):
                await self._queue_notification(
                    'email',
                    job_data['email'],
                    subject=f"Job Completed: {job_data['job_number']}",
                    message="Your roofing job has been completed. Thank you for your business!",
                    data=job_data
                )
    
    async def send_invoice_notification(self, invoice_id: str, notification_type: str):
        """Send notification for invoice events"""
        # Get invoice data
        query = """
        SELECT i.*, c.name as customer_name, c.email
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        WHERE i.id = :invoice_id
        """
        
        result = self.db.execute(text(query), {'invoice_id': invoice_id})
        invoice = result.fetchone()
        
        if not invoice:
            return
        
        invoice_data = dict(invoice)
        
        # Send appropriate notification
        if notification_type == 'invoice_sent' and invoice_data.get('email'):
            await self._queue_notification(
                'email',
                invoice_data['email'],
                subject=f"Invoice {invoice_data['invoice_number']}",
                message=f"Your invoice for ${invoice_data['total_amount']} is now available",
                data=invoice_data
            )
        elif notification_type == 'payment_reminder' and invoice_data.get('email'):
            await self._queue_notification(
                'email',
                invoice_data['email'],
                subject=f"Payment Reminder: Invoice {invoice_data['invoice_number']}",
                message=f"This is a reminder that invoice {invoice_data['invoice_number']} for ${invoice_data['balance_due']} is due",
                data=invoice_data
            )
    
    async def _queue_notification(
        self, 
        notification_type: str,
        recipient: str,
        subject: str = None,
        message: str = None,
        data: Dict = None,
        template_id: str = None
    ):
        """Queue a notification for sending"""
        query = """
        INSERT INTO notification_queue (
            notification_type,
            recipient_email,
            recipient_phone,
            subject,
            message,
            data,
            template_id,
            status,
            scheduled_for
        ) VALUES (
            :notification_type,
            :recipient_email,
            :recipient_phone,
            :subject,
            :message,
            :data,
            :template_id,
            'pending',
            NOW()
        )
        """
        
        params = {
            'notification_type': notification_type,
            'recipient_email': recipient if notification_type == 'email' else None,
            'recipient_phone': recipient if notification_type == 'sms' else None,
            'subject': subject,
            'message': message,
            'data': json.dumps(data) if data else None,
            'template_id': template_id
        }
        
        self.db.execute(text(query), params)
        self.db.commit()


class NotificationScheduler:
    """Background scheduler for notification processing"""
    
    def __init__(self, notification_service: NotificationService):
        self.service = notification_service
        self.running = False
    
    async def start(self):
        """Start the notification scheduler"""
        self.running = True
        logger.info("Notification scheduler started")
        
        while self.running:
            try:
                # Process queue
                count = await self.service.process_queue()
                
                if count > 0:
                    logger.info(f"Processed {count} notifications")
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def stop(self):
        """Stop the notification scheduler"""
        self.running = False
        logger.info("Notification scheduler stopped")
