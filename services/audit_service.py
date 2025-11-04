"""
Audit Logging Service
Tracks all critical operations for compliance and security
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Request
import hashlib
import uuid

logger = logging.getLogger(__name__)

class AuditService:
    """Comprehensive audit logging service"""

    # Event types for categorization
    EVENT_TYPES = {
        "AUTH": "Authentication",
        "DATA": "Data Access",
        "MODIFY": "Data Modification",
        "DELETE": "Data Deletion",
        "ADMIN": "Administrative",
        "SYSTEM": "System Event",
        "SECURITY": "Security Event",
        "API": "API Access",
        "ERROR": "Error Event"
    }

    # Severity levels
    SEVERITY = {
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4
    }

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
        request: Optional[Request] = None
    ) -> bool:
        """Log an audit event to database"""
        try:
            # Extract request information if available
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent", "")[:500]
                request_method = request.method
                request_path = str(request.url.path)

            # Generate event ID
            event_id = str(uuid.uuid4())

            # Prepare details JSON
            event_details = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_id": event_id,
                "severity": severity,
                **(details or {})
            }

            # Insert audit log
            db.execute(
                text("""
                    INSERT INTO audit_logs (
                        id, event_type, action, user_id,
                        resource_type, resource_id,
                        details, severity,
                        ip_address, user_agent,
                        request_method, request_path,
                        created_at
                    ) VALUES (
                        :id, :event_type, :action, :user_id,
                        :resource_type, :resource_id,
                        :details::jsonb, :severity,
                        :ip_address, :user_agent,
                        :request_method, :request_path,
                        NOW()
                    )
                """),
                {
                    "id": event_id,
                    "event_type": event_type,
                    "action": action,
                    "user_id": user_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": json.dumps(event_details),
                    "severity": severity,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "request_method": request_method,
                    "request_path": request_path
                }
            )
            db.commit()

            # Log critical events to application logger
            if severity in ["ERROR", "CRITICAL"]:
                logger.error(f"Audit Event: {event_type} - {action} - {event_details}")

            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't fail the main operation if audit logging fails
            return False

    @staticmethod
    def log_login(db: Session, user_id: str, success: bool, request: Request, reason: str = None):
        """Log login attempt"""
        AuditService.log_event(
            db=db,
            event_type="AUTH",
            action="LOGIN_SUCCESS" if success else "LOGIN_FAILED",
            user_id=user_id,
            details={"reason": reason} if reason else None,
            severity="INFO" if success else "WARNING",
            request=request
        )

    @staticmethod
    def log_data_access(
        db: Session,
        user_id: str,
        table_name: str,
        operation: str,
        record_count: int = 1,
        request: Request = None
    ):
        """Log data access event"""
        AuditService.log_event(
            db=db,
            event_type="DATA",
            action=f"{operation.upper()}_{table_name.upper()}",
            user_id=user_id,
            resource_type=table_name,
            details={"record_count": record_count, "operation": operation},
            severity="INFO",
            request=request
        )

    @staticmethod
    def log_data_modification(
        db: Session,
        user_id: str,
        table_name: str,
        operation: str,
        record_id: str,
        old_values: Dict = None,
        new_values: Dict = None,
        request: Request = None
    ):
        """Log data modification event"""
        # Hash sensitive data if present
        if old_values:
            old_values = AuditService._sanitize_sensitive_data(old_values)
        if new_values:
            new_values = AuditService._sanitize_sensitive_data(new_values)

        AuditService.log_event(
            db=db,
            event_type="MODIFY",
            action=f"{operation.upper()}_{table_name.upper()}",
            user_id=user_id,
            resource_type=table_name,
            resource_id=record_id,
            details={
                "operation": operation,
                "old_values": old_values,
                "new_values": new_values
            },
            severity="WARNING" if operation == "DELETE" else "INFO",
            request=request
        )

    @staticmethod
    def log_security_event(
        db: Session,
        event: str,
        user_id: str = None,
        details: Dict = None,
        request: Request = None
    ):
        """Log security-related event"""
        AuditService.log_event(
            db=db,
            event_type="SECURITY",
            action=event,
            user_id=user_id,
            details=details,
            severity="CRITICAL",
            request=request
        )

    @staticmethod
    def log_api_call(
        db: Session,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        request: Request = None
    ):
        """Log API call for monitoring"""
        severity = "INFO"
        if status_code >= 500:
            severity = "ERROR"
        elif status_code >= 400:
            severity = "WARNING"

        AuditService.log_event(
            db=db,
            event_type="API",
            action=f"{method}_{endpoint}",
            user_id=user_id,
            details={
                "status_code": status_code,
                "response_time_ms": response_time_ms
            },
            severity=severity,
            request=request
        )

    @staticmethod
    def _sanitize_sensitive_data(data: Dict) -> Dict:
        """Sanitize sensitive fields in data"""
        sensitive_fields = [
            "password", "password_hash", "token", "secret",
            "api_key", "credit_card", "ssn", "bank_account"
        ]

        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                # Hash the value instead of storing plaintext
                sanitized[field] = hashlib.sha256(
                    str(sanitized[field]).encode()
                ).hexdigest()[:8] + "***"

        return sanitized

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """Get audit log for specific user"""
        try:
            result = db.execute(
                text("""
                    SELECT * FROM audit_logs
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"user_id": user_id, "limit": limit, "offset": offset}
            )

            return [dict(row._mapping) for row in result]

        except Exception as e:
            logger.error(f"Error fetching user activity: {e}")
            return []

    @staticmethod
    def get_security_events(
        db: Session,
        hours: int = 24,
        severity_min: str = "WARNING"
    ) -> list:
        """Get recent security events"""
        try:
            result = db.execute(
                text("""
                    SELECT * FROM audit_logs
                    WHERE event_type IN ('SECURITY', 'AUTH')
                    AND severity >= :severity
                    AND created_at > NOW() - INTERVAL :hours HOUR
                    ORDER BY created_at DESC
                """),
                {"severity": severity_min, "hours": hours}
            )

            return [dict(row._mapping) for row in result]

        except Exception as e:
            logger.error(f"Error fetching security events: {e}")
            return []

# Create global audit service instance
audit_service = AuditService()

# Export convenience functions
log_event = audit_service.log_event
log_login = audit_service.log_login
log_data_access = audit_service.log_data_access
log_data_modification = audit_service.log_data_modification
log_security_event = audit_service.log_security_event
log_api_call = audit_service.log_api_call