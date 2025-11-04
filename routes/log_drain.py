"""
Log Drain Endpoint for Real-Time Debugging
Provides access to application logs without needing Render dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import os
from collections import deque
from threading import Lock

router = APIRouter(prefix="/api/v1/logs", tags=["Logging"])

# In-memory log storage (last 1000 log entries)
log_buffer = deque(maxlen=1000)
log_lock = Lock()

class LogDrainHandler(logging.Handler):
    """Custom logging handler that stores logs in memory"""

    def emit(self, record):
        try:
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }

            with log_lock:
                log_buffer.append(log_entry)
        except Exception:
            self.handleError(record)

# Initialize log drain handler
log_drain_handler = LogDrainHandler()
log_drain_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_drain_handler.setFormatter(formatter)

# Add handler to root logger
logging.getLogger().addHandler(log_drain_handler)

@router.get("/recent")
async def get_recent_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of recent logs to return"),
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logger_name: Optional[str] = Query(None, description="Filter by logger name"),
    search: Optional[str] = Query(None, description="Search in log messages")
):
    """
    Get recent log entries from the application

    - **limit**: Number of logs to return (max 1000)
    - **level**: Filter by log level
    - **logger_name**: Filter by logger name
    - **search**: Search term in log messages
    """
    with log_lock:
        logs = list(log_buffer)

    # Apply filters
    if level:
        logs = [log for log in logs if log["level"] == level.upper()]

    if logger_name:
        logs = [log for log in logs if logger_name.lower() in log["logger"].lower()]

    if search:
        logs = [log for log in logs if search.lower() in log["message"].lower()]

    # Return most recent first
    logs.reverse()

    return {
        "total": len(logs),
        "limit": limit,
        "filters": {
            "level": level,
            "logger_name": logger_name,
            "search": search
        },
        "logs": logs[:limit]
    }

@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=500, description="Number of recent errors to return"),
    since_minutes: int = Query(60, ge=1, le=1440, description="Get errors from last N minutes")
):
    """
    Get recent ERROR and CRITICAL level logs

    - **limit**: Number of errors to return
    - **since_minutes**: Get errors from last N minutes
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=since_minutes)

    with log_lock:
        logs = list(log_buffer)

    # Filter for errors and recent time
    errors = [
        log for log in logs
        if log["level"] in ["ERROR", "CRITICAL"]
        and datetime.fromisoformat(log["timestamp"]) >= cutoff_time
    ]

    # Return most recent first
    errors.reverse()

    return {
        "total": len(errors),
        "since_minutes": since_minutes,
        "errors": errors[:limit]
    }

@router.get("/auth-errors")
async def get_auth_errors(limit: int = Query(20, ge=1, le=100)):
    """Get recent authentication-related errors"""

    with log_lock:
        logs = list(log_buffer)

    # Filter for auth-related errors
    auth_errors = [
        log for log in logs
        if (log["level"] in ["ERROR", "CRITICAL", "WARNING"])
        and ("auth" in log["logger"].lower() or "login" in log["message"].lower() or "token" in log["message"].lower())
    ]

    # Return most recent first
    auth_errors.reverse()

    return {
        "total": len(auth_errors),
        "auth_errors": auth_errors[:limit]
    }

@router.get("/stats")
async def get_log_stats():
    """Get statistics about logged messages"""

    with log_lock:
        logs = list(log_buffer)

    if not logs:
        return {
            "total_logs": 0,
            "by_level": {},
            "by_logger": {},
            "oldest": None,
            "newest": None
        }

    # Count by level
    by_level = {}
    by_logger = {}

    for log in logs:
        level = log["level"]
        logger = log["logger"]

        by_level[level] = by_level.get(level, 0) + 1
        by_logger[logger] = by_logger.get(logger, 0) + 1

    return {
        "total_logs": len(logs),
        "buffer_capacity": log_buffer.maxlen,
        "by_level": by_level,
        "top_loggers": dict(sorted(by_logger.items(), key=lambda x: x[1], reverse=True)[:10]),
        "oldest": logs[0]["timestamp"],
        "newest": logs[-1]["timestamp"]
    }

@router.get("/tail")
async def tail_logs(lines: int = Query(50, ge=1, le=500)):
    """
    Tail the logs (like 'tail -f' command)

    Returns the most recent N log lines
    """
    with log_lock:
        logs = list(log_buffer)

    # Return most recent first
    logs.reverse()

    return {
        "lines": lines,
        "logs": logs[:lines]
    }

@router.post("/clear")
async def clear_logs():
    """Clear the in-memory log buffer (admin only in production)"""

    with log_lock:
        log_buffer.clear()

    logging.info("Log buffer cleared via API endpoint")

    return {
        "status": "success",
        "message": "Log buffer cleared",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def log_drain_health():
    """Check log drain system health"""

    with log_lock:
        buffer_size = len(log_buffer)

    return {
        "status": "healthy",
        "buffer_size": buffer_size,
        "buffer_capacity": log_buffer.maxlen,
        "handler_active": log_drain_handler is not None
    }
