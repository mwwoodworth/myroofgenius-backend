#!/usr/bin/env python3
"""
Create Vercel log drain endpoint for the backend
"""

VERCEL_LOGS_ROUTE = '''"""
Vercel Log Drain endpoint for frontend observability
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
import json
import hashlib
import hmac
from core.database import get_db
from db.business_models import VercelLog, AlertEvent
from services.memory_service import MemoryService
from services.notification_service import send_slack_alert, send_email_alert

router = APIRouter()

# Webhook secret for verification
VERCEL_WEBHOOK_SECRET = "myroofgenius_log_drain_secret_2025_02_08_secure"

def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verify Vercel webhook signature"""
    expected_sig = hmac.new(
        VERCEL_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

async def process_log_entry(log_data: Dict[str, Any], db: Session):
    """Process individual log entry"""
    try:
        # Create log record
        log_entry = VercelLog(
            timestamp=datetime.fromisoformat(log_data.get("timestamp", datetime.utcnow().isoformat())),
            type=log_data.get("type", "unknown"),
            level=log_data.get("level", "info"),
            message=log_data.get("message", ""),
            source=log_data.get("source", ""),
            environment=log_data.get("environment", "production"),
            project_name=log_data.get("projectName", "myroofgenius"),
            deployment_id=log_data.get("deploymentId"),
            request_id=log_data.get("requestId"),
            path=log_data.get("path"),
            status_code=log_data.get("statusCode"),
            method=log_data.get("method"),
            user_agent=log_data.get("userAgent"),
            ip_address=log_data.get("ip"),
            duration_ms=log_data.get("duration"),
            memory_used_mb=log_data.get("memoryUsed"),
            error_message=log_data.get("error", {}).get("message"),
            error_stack=log_data.get("error", {}).get("stack"),
            raw_data=log_data
        )
        db.add(log_entry)
        
        # Check for alerts
        await check_alert_conditions(log_data, db)
        
    except Exception as e:
        print(f"Error processing log entry: {str(e)}")

async def check_alert_conditions(log_data: Dict[str, Any], db: Session):
    """Check if log entry triggers any alerts"""
    
    # Alert on build failures
    if log_data.get("type") == "build" and log_data.get("status") == "failed":
        await send_slack_alert(
            f"🚨 Build Failed: {log_data.get('projectName')}",
            f"Deployment {log_data.get('deploymentId')} failed: {log_data.get('error', {}).get('message')}"
        )
        
    # Alert on high error rates
    if log_data.get("level") == "error":
        # Count recent errors
        recent_errors = db.query(VercelLog).filter(
            VercelLog.level == "error",
            VercelLog.timestamp > datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        ).count()
        
        if recent_errors > 50:  # More than 50 errors in current hour
            await send_slack_alert(
                "⚠️ High Error Rate Detected",
                f"Frontend has logged {recent_errors} errors in the past hour"
            )
    
    # Alert on security threats
    if log_data.get("source") == "firewall":
        ip = log_data.get("ip")
        if ip:
            # Count firewall blocks from this IP
            block_count = db.query(VercelLog).filter(
                VercelLog.source == "firewall",
                VercelLog.ip_address == ip,
                VercelLog.timestamp > datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            if block_count > 10:
                await send_slack_alert(
                    "🛡️ Potential Security Threat",
                    f"IP {ip} has been blocked {block_count} times today"
                )

@router.post("/logs/vercel")
async def receive_vercel_logs(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive log drain data from Vercel
    
    Vercel sends logs as NDJSON (newline-delimited JSON)
    """
    # Verify signature if provided
    signature = request.headers.get("X-Vercel-Signature")
    body = await request.body()
    
    if signature and not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse NDJSON
    logs_processed = 0
    errors = []
    
    try:
        lines = body.decode('utf-8').strip().split('\\n')
        
        for line in lines:
            if not line:
                continue
                
            try:
                log_data = json.loads(line)
                background_tasks.add_task(process_log_entry, log_data, db)
                logs_processed += 1
                
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {str(e)}")
                
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    # Store in memory system for AI analysis
    memory_service = MemoryService(db)
    await memory_service.create_memory(
        user_id="system",
        title=f"Vercel Logs Received - {logs_processed} entries",
        content=f"Processed {logs_processed} log entries from Vercel. Errors: {len(errors)}",
        memory_type="system_log",
        tags=["vercel", "logs", "frontend"],
        meta_data={
            "logs_processed": logs_processed,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    db.commit()
    
    return {
        "status": "success",
        "logs_processed": logs_processed,
        "errors": errors if errors else None
    }

@router.get("/logs/vercel/stats")
async def get_vercel_log_stats(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get Vercel log statistics"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get log counts by type
    type_counts = db.query(
        VercelLog.type,
        func.count(VercelLog.id).label('count')
    ).filter(
        VercelLog.timestamp > cutoff_time
    ).group_by(VercelLog.type).all()
    
    # Get error summary
    error_counts = db.query(
        VercelLog.error_message,
        func.count(VercelLog.id).label('count')
    ).filter(
        VercelLog.level == 'error',
        VercelLog.timestamp > cutoff_time
    ).group_by(VercelLog.error_message).order_by(
        func.count(VercelLog.id).desc()
    ).limit(10).all()
    
    # Get 404 pages
    not_found_pages = db.query(
        VercelLog.path,
        func.count(VercelLog.id).label('count')
    ).filter(
        VercelLog.status_code == 404,
        VercelLog.timestamp > cutoff_time
    ).group_by(VercelLog.path).order_by(
        func.count(VercelLog.id).desc()
    ).limit(10).all()
    
    # Get performance metrics
    avg_duration = db.query(
        func.avg(VercelLog.duration_ms).label('avg_duration')
    ).filter(
        VercelLog.duration_ms.isnot(None),
        VercelLog.timestamp > cutoff_time
    ).scalar()
    
    return {
        "time_range_hours": hours,
        "log_types": {t: c for t, c in type_counts},
        "top_errors": [{"error": e, "count": c} for e, c in error_counts],
        "top_404_pages": [{"path": p, "count": c} for p, c in not_found_pages],
        "avg_response_time_ms": avg_duration,
        "total_logs": sum(c for _, c in type_counts)
    }

@router.get("/logs/vercel/recent")
async def get_recent_vercel_logs(
    limit: int = 100,
    log_type: str = None,
    level: str = None,
    db: Session = Depends(get_db)
):
    """Get recent Vercel logs with filtering"""
    
    query = db.query(VercelLog)
    
    if log_type:
        query = query.filter(VercelLog.type == log_type)
    
    if level:
        query = query.filter(VercelLog.level == level)
    
    logs = query.order_by(VercelLog.timestamp.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "type": log.type,
                "level": log.level,
                "message": log.message,
                "path": log.path,
                "status_code": log.status_code,
                "duration_ms": log.duration_ms,
                "error_message": log.error_message
            }
            for log in logs
        ],
        "count": len(logs)
    }
'''

VERCEL_LOG_MODEL = '''# Add to business_models.py

class VercelLog(Base):
    """Store Vercel log drain data"""
    __tablename__ = "vercel_logs"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # build, function, static, etc
    level = Column(String(20), nullable=False, index=True)  # info, warning, error
    message = Column(Text)
    source = Column(String(50))  # edge, external, firewall, etc
    environment = Column(String(50), default="production")
    project_name = Column(String(100))
    deployment_id = Column(String(100), index=True)
    request_id = Column(String(100))
    path = Column(String(500), index=True)
    status_code = Column(Integer, index=True)
    method = Column(String(10))
    user_agent = Column(Text)
    ip_address = Column(String(50), index=True)
    duration_ms = Column(Integer)
    memory_used_mb = Column(Integer)
    error_message = Column(Text)
    error_stack = Column(Text)
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_vercel_logs_timestamp_type', 'timestamp', 'type'),
        Index('idx_vercel_logs_error_lookup', 'timestamp', 'level', 'status_code'),
        Index('idx_vercel_logs_performance', 'timestamp', 'duration_ms'),
        {"extend_existing": True}
    )
'''

CREATE_TABLE_SQL = '''-- Create Vercel logs table
CREATE TABLE IF NOT EXISTS vercel_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    type VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT,
    source VARCHAR(50),
    environment VARCHAR(50) DEFAULT 'production',
    project_name VARCHAR(100),
    deployment_id VARCHAR(100),
    request_id VARCHAR(100),
    path VARCHAR(500),
    status_code INTEGER,
    method VARCHAR(10),
    user_agent TEXT,
    ip_address VARCHAR(50),
    duration_ms INTEGER,
    memory_used_mb INTEGER,
    error_message TEXT,
    error_stack TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_vercel_logs_timestamp_type ON vercel_logs(timestamp, type);
CREATE INDEX idx_vercel_logs_error_lookup ON vercel_logs(timestamp, level, status_code);
CREATE INDEX idx_vercel_logs_performance ON vercel_logs(timestamp, duration_ms);
CREATE INDEX idx_vercel_logs_deployment ON vercel_logs(deployment_id);
CREATE INDEX idx_vercel_logs_path ON vercel_logs(path);
CREATE INDEX idx_vercel_logs_ip ON vercel_logs(ip_address);

-- Create alert rules table
CREATE TABLE IF NOT EXISTS vercel_alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    condition_type VARCHAR(50) NOT NULL, -- error_rate, build_failure, performance, security
    threshold_value INTEGER NOT NULL,
    threshold_window_minutes INTEGER DEFAULT 60,
    alert_channels JSONB, -- {slack: true, email: true, webhook: "url"}
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default alert rules
INSERT INTO vercel_alert_rules (name, condition_type, threshold_value, alert_channels) VALUES
('High Error Rate', 'error_rate', 50, '{"slack": true, "email": false}'),
('Build Failures', 'build_failure', 1, '{"slack": true, "email": true}'),
('Slow Response Time', 'performance', 3000, '{"slack": true, "email": false}'),
('Security Threats', 'security', 10, '{"slack": true, "email": true}');
'''

print("Files to create:")
print("1. Backend route: /fastapi-operator-env/routes/vercel_logs.py")
print("2. Model update: Add VercelLog to business_models.py")
print("3. Database migration: Create vercel_logs table")
print("\n" + "="*80)
print("ROUTE FILE CONTENT:")
print("="*80)
print(VERCEL_LOGS_ROUTE)
print("\n" + "="*80)
print("MODEL TO ADD:")
print("="*80)
print(VERCEL_LOG_MODEL)
print("\n" + "="*80)
print("SQL TO RUN:")
print("="*80)
print(CREATE_TABLE_SQL)