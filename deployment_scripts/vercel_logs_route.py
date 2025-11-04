"""
Vercel Log Drain endpoint for frontend observability
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import hashlib
import hmac
from core.database import get_db

router = APIRouter()

# Webhook secret for verification
VERCEL_WEBHOOK_SECRET = "myroofgenius_log_drain_secret_2025_02_08_secure"

def verify_webhook_auth(auth_header: str) -> bool:
    """Verify webhook authorization"""
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.replace("Bearer ", "")
    return token == VERCEL_WEBHOOK_SECRET

async def process_log_entry(log_data: Dict[str, Any], db: Session):
    """Process individual log entry"""
    try:
        # Parse log entry based on Vercel format
        timestamp = log_data.get("timestamp", datetime.utcnow().isoformat())
        if isinstance(timestamp, int):
            # Convert milliseconds to datetime
            timestamp = datetime.fromtimestamp(timestamp / 1000)
        else:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Extract fields from Vercel log format
        log_entry = {
            "timestamp": timestamp,
            "type": log_data.get("type", "unknown"),
            "level": log_data.get("level", "info"),
            "message": log_data.get("message", ""),
            "source": log_data.get("source", ""),
            "environment": log_data.get("environment", "production"),
            "project_name": log_data.get("projectName", "myroofgenius"),
            "deployment_id": log_data.get("deploymentId"),
            "request_id": log_data.get("requestId"),
            "path": log_data.get("path") or log_data.get("pathname"),
            "status_code": log_data.get("statusCode") or log_data.get("status"),
            "method": log_data.get("method"),
            "user_agent": log_data.get("userAgent"),
            "ip_address": log_data.get("ip") or log_data.get("ipAddress"),
            "duration_ms": log_data.get("duration") or log_data.get("latency"),
            "memory_used_mb": log_data.get("memoryUsed"),
            "error_message": log_data.get("error", {}).get("message") if isinstance(log_data.get("error"), dict) else log_data.get("error"),
            "error_stack": log_data.get("error", {}).get("stack") if isinstance(log_data.get("error"), dict) else None,
            "raw_data": log_data
        }
        
        # Store in database (would need to create model)
        # For now, just process alerts
        await check_alert_conditions(log_data, db)
        
        # Log to console for debugging
        if log_entry["level"] == "error" or log_entry["status_code"] >= 400:
            print(f"⚠️ Vercel Error: {log_entry['path']} - {log_entry['status_code']} - {log_entry['error_message']}")
        
    except Exception as e:
        print(f"Error processing log entry: {str(e)}")

async def check_alert_conditions(log_data: Dict[str, Any], db: Session):
    """Check if log entry triggers any alerts"""
    
    # Alert on build failures
    if log_data.get("type") == "build" and log_data.get("status") == "error":
        print(f"🚨 Build Failed: {log_data.get('projectName')} - {log_data.get('message')}")
        
    # Alert on high error rates
    if log_data.get("level") == "error":
        print(f"❌ Frontend Error: {log_data.get('path')} - {log_data.get('error')}")
    
    # Alert on 404s for critical pages
    if log_data.get("statusCode") == 404 and log_data.get("path") in ["/profile", "/marketplace/cart"]:
        print(f"🔍 Critical 404: {log_data.get('path')}")
    
    # Alert on slow performance
    duration = log_data.get("duration") or log_data.get("latency")
    if duration and duration > 3000:  # 3 seconds
        print(f"🐌 Slow Request: {log_data.get('path')} took {duration}ms")

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
    # Verify authorization
    auth_header = request.headers.get("Authorization")
    if not verify_webhook_auth(auth_header):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Parse NDJSON
    logs_processed = 0
    errors = []
    
    try:
        body = await request.body()
        lines = body.decode('utf-8').strip().split('\n')
        
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
    
    print(f"📊 Processed {logs_processed} Vercel logs")
    
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
    
    # This would query the database once we have the model
    # For now, return mock data
    return {
        "time_range_hours": hours,
        "log_types": {
            "function": 450,
            "static": 1200,
            "edge": 300,
            "build": 5,
            "external": 150
        },
        "top_errors": [
            {"error": "Button is not exported", "count": 25},
            {"error": "404 Not Found", "count": 15}
        ],
        "top_404_pages": [
            {"path": "/marketplace/cart", "count": 8},
            {"path": "/profile", "count": 6}
        ],
        "avg_response_time_ms": 245,
        "total_logs": 2105
    }

@router.get("/logs/vercel/recent")
async def get_recent_vercel_logs(
    limit: int = 100,
    log_type: str = None,
    level: str = None,
    db: Session = Depends(get_db)
):
    """Get recent Vercel logs with filtering"""
    
    # This would query the database once we have the model
    # For now, return mock data showing our recent issues
    return {
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "function",
                "level": "error",
                "message": "Element type is invalid: expected a string but got: undefined",
                "path": "/marketplace/cart",
                "status_code": 500,
                "error_message": "Button is not exported from '@/components/ui/button'"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "type": "static",
                "level": "warning",
                "message": "404 Not Found",
                "path": "/profile",
                "status_code": 404
            }
        ],
        "count": 2
    }