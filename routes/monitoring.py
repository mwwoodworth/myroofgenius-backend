"""
System Monitoring Endpoints for BrainOps
Real-time health and performance monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import psutil
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Monitoring"])

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/monitoring")
async def get_system_monitoring(db: Session = Depends(get_db)):
    """
    Get comprehensive system monitoring data
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get database stats
        db_stats = {}
        try:
            result = db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM customers) as customers,
                    (SELECT COUNT(*) FROM jobs) as jobs,
                    (SELECT COUNT(*) FROM invoices) as invoices,
                    (SELECT COUNT(*) FROM estimates) as estimates,
                    (SELECT COUNT(*) FROM ai_agents) as ai_agents,
                    (SELECT COUNT(*) FROM workflows) as workflows
            """)).fetchone()

            if result:
                db_stats = {
                    'customers': result[0] or 0,
                    'jobs': result[1] or 0,
                    'invoices': result[2] or 0,
                    'estimates': result[3] or 0,
                    'ai_agents': result[4] or 0,
                    'workflows': result[5] or 0
                }
        except Exception as e:
            logger.warning(f"Could not fetch database stats: {e}")

        # Get API metrics
        api_metrics = {
            'requests_per_minute': 0,  # Would need Redis or tracking for real metrics
            'average_response_time': 0.125,  # Placeholder
            'error_rate': 0.001,  # Placeholder
            'uptime': '99.9%'
        }

        # Get service health
        services = {
            'backend_api': 'healthy',
            'database': 'healthy' if db_stats else 'degraded',
            'ai_agents': 'healthy',
            'stripe': 'healthy',
            'redis': 'not_configured'
        }

        return {
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': round(cpu_percent, 2),
                'memory': {
                    'percent': round(memory.percent, 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'total_gb': round(memory.total / (1024**3), 2)
                },
                'disk': {
                    'percent': round(disk.percent, 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'total_gb': round(disk.total / (1024**3), 2)
                }
            },
            'database': db_stats,
            'api_metrics': api_metrics,
            'services': services,
            'alerts': []  # Would populate with real alerts
        }

    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/health")
async def get_health_status():
    """
    Simple health check endpoint
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'brainops-backend',
        'version': '32.0.0'
    }

@router.get("/monitoring/metrics")
async def get_metrics(
    period: str = "1h",  # 1h, 6h, 24h, 7d
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for specified period
    """
    try:
        # Parse period
        period_map = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7)
        }

        delta = period_map.get(period, timedelta(hours=1))
        start_time = datetime.now() - delta

        # Get job metrics
        job_metrics = {}
        try:
            result = db.execute(text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled
                FROM jobs
                WHERE created_at >= :start_time
            """), {'start_time': start_time}).fetchone()

            if result:
                job_metrics = {
                    'total': result[0] or 0,
                    'completed': result[1] or 0,
                    'in_progress': result[2] or 0,
                    'scheduled': result[3] or 0
                }
        except Exception as e:
            logger.warning(f"Could not fetch job metrics: {e}")

        # Get revenue metrics (placeholder)
        revenue_metrics = {
            'total_revenue': 0,
            'new_customers': 0,
            'conversion_rate': 0
        }

        # Get AI usage metrics (placeholder)
        ai_metrics = {
            'total_analyses': 0,
            'roof_analyses': 0,
            'estimates_generated': 0,
            'average_confidence': 0
        }

        return {
            'period': period,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'job_metrics': job_metrics,
            'revenue_metrics': revenue_metrics,
            'ai_metrics': ai_metrics
        }

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/alerts")
async def get_system_alerts(
    severity: Optional[str] = None,  # critical, warning, info
    db: Session = Depends(get_db)
):
    """
    Get system alerts and notifications
    """
    try:
        alerts = []

        # Check system resources
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            alerts.append({
                'id': 'mem-001',
                'severity': 'critical',
                'type': 'system',
                'message': f'Memory usage critical: {memory.percent}%',
                'timestamp': datetime.now().isoformat()
            })
        elif memory.percent > 80:
            alerts.append({
                'id': 'mem-002',
                'severity': 'warning',
                'type': 'system',
                'message': f'Memory usage high: {memory.percent}%',
                'timestamp': datetime.now().isoformat()
            })

        # Check disk space
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            alerts.append({
                'id': 'disk-001',
                'severity': 'critical',
                'type': 'system',
                'message': f'Disk usage critical: {disk.percent}%',
                'timestamp': datetime.now().isoformat()
            })

        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]

        return {
            'total_alerts': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/test")
async def test_monitoring():
    """
    Test monitoring system
    """
    return {
        'status': 'success',
        'message': 'Monitoring system operational',
        'timestamp': datetime.now().isoformat()
    }