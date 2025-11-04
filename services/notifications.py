# WeatherCraft ERP - Notification Service
# Handles email, SMS, and push notifications

import asyncio
import logging
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

class NotificationService:
    """Comprehensive notification service for all communication channels"""
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        self.db = db
        self.config = config or {}
        self.email_config = config.get('email', {}) if config else {}
        self.sms_config = config.get('sms', {}) if config else {}
        self.push_config = config.get('push', {}) if config else {}
    
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
            
            # For production, integrate with email service (SendGrid, AWS SES, etc.)
            # For now, log the email
            logger.info(f"Email to {notification['recipient_email']}: {subject}")
            
            # In production, uncomment and configure:
            # await self._send_via_sendgrid(notification['recipient_email'], subject, html_body)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def _send_sms(self, notification: Dict) -> bool:
        """Send SMS notification"""
        try:
            phone = notification['recipient_phone']
            message = notification['message']
            
            # For production, integrate with SMS service (Twilio, etc.)
            logger.info(f"SMS to {phone}: {message}")
            
            # In production, uncomment and configure:
            # await self._send_via_twilio(phone, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def _send_push(self, notification: Dict) -> bool:
        """Send push notification"""
        try:
            # For production, integrate with push service (Firebase, OneSignal, etc.)
            logger.info(f"Push notification: {notification['message']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str):
        """Send email via SendGrid API"""
        # Implementation for SendGrid
        pass
    
    async def _send_via_twilio(self, to_phone: str, message: str):
        """Send SMS via Twilio API"""
        # Implementation for Twilio
        pass
    
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