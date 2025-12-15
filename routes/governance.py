from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from datetime import datetime, timedelta
import psycopg2
import json
import uuid

router = APIRouter(prefix="/api/v1/governance", tags=["Governance"])

DB_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

@router.get("/notifications/rules")
async def get_notification_rules(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get all notification rules"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, description, trigger_type, trigger_conditions, 
                   priority, channels, recipients, is_active, created_at
            FROM governance.notification_rules
            WHERE is_active = true
            ORDER BY priority DESC, name
        """)
        
        rules = []
        for row in cur.fetchall():
            rules.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "trigger_type": row[3],
                "trigger_conditions": row[4],
                "priority": row[5],
                "channels": row[6],
                "recipients": row[7],
                "is_active": row[8],
                "created_at": row[9].isoformat() if row[9] else None
            })
        
        cur.close()
        conn.close()
        
        return rules
    except Exception as e:
        print(f"Error getting notification rules: {e}")
        return []

@router.post("/notifications/send")
async def send_notification(
    notification: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a notification"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        notification_id = str(uuid.uuid4())
        
        # Store notification in history
        cur.execute("""
            INSERT INTO governance.notification_history (
                notification_id, priority, channels, recipients,
                subject, message, metadata, status, sent_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            notification_id,
            notification.get('priority', 'medium'),
            json.dumps(notification.get('channels', ['email'])),
            json.dumps(notification.get('recipients', ['founder@brainops.com'])),
            notification.get('subject', 'System Notification'),
            notification.get('message', ''),
            json.dumps(notification.get('metadata', {})),
            'sent',
            datetime.utcnow()
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        
        
        return {
            "notification_id": notification_id,
            "status": "sent",
            "message": "Notification sent successfully"
        }
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/approvals/pending")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get pending approval requests"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                ar.id, ar.request_id, ar.request_type, ar.requester,
                ar.subject, ar.details, ar.priority, ar.status,
                ar.requested_at, ar.expires_at, aw.name as workflow_name
            FROM governance.approval_requests ar
            LEFT JOIN governance.approval_workflows aw ON ar.workflow_id = aw.id
            WHERE ar.status = 'pending' 
            AND (ar.expires_at IS NULL OR ar.expires_at > NOW())
            ORDER BY ar.priority DESC, ar.requested_at ASC
        """)
        
        approvals = []
        for row in cur.fetchall():
            approvals.append({
                "id": str(row[0]),
                "request_id": row[1],
                "request_type": row[2],
                "requester": row[3],
                "subject": row[4],
                "details": row[5],
                "priority": row[6],
                "status": row[7],
                "requested_at": row[8].isoformat() if row[8] else None,
                "expires_at": row[9].isoformat() if row[9] else None,
                "workflow_name": row[10]
            })
        
        cur.close()
        conn.close()
        
        return approvals
    except Exception as e:
        print(f"Error getting pending approvals: {e}")
        return []

@router.post("/approvals/{request_id}/approve")
async def approve_request(
    request_id: str,
    approval_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Approve a request"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE governance.approval_requests
            SET status = 'approved',
                decision = 'approved',
                decided_by = %s,
                decision_notes = %s,
                decided_at = %s
            WHERE request_id = %s AND status = 'pending'
        """, (
            current_user.get('email'),
            approval_data.get('notes', ''),
            datetime.utcnow(),
            request_id
        ))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "request_id": request_id,
            "status": "approved",
            "message": "Request approved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error approving request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approvals/{request_id}/reject")
async def reject_request(
    request_id: str,
    rejection_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reject a request"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE governance.approval_requests
            SET status = 'rejected',
                decision = 'rejected',
                decided_by = %s,
                decision_notes = %s,
                decided_at = %s
            WHERE request_id = %s AND status = 'pending'
        """, (
            current_user.get('email'),
            rejection_data.get('reason', ''),
            datetime.utcnow(),
            request_id
        ))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found or already processed")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "request_id": request_id,
            "status": "rejected",
            "message": "Request rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error rejecting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies")
async def get_policies(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get all governance policies"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, policy_key, policy_name, description, category,
                rules, enforcement_level, is_active, created_at
            FROM governance.policies
            WHERE is_active = true
            ORDER BY category, policy_name
        """)
        
        policies = []
        for row in cur.fetchall():
            policies.append({
                "id": str(row[0]),
                "policy_key": row[1],
                "policy_name": row[2],
                "description": row[3],
                "category": row[4],
                "rules": row[5],
                "enforcement_level": row[6],
                "is_active": row[7],
                "created_at": row[8].isoformat() if row[8] else None
            })
        
        cur.close()
        conn.close()
        
        return policies
    except Exception as e:
        print(f"Error getting policies: {e}")
        return []

@router.get("/dashboard/executive")
async def get_executive_dashboard(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get executive dashboard data"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Get latest metrics
        cur.execute("""
            SELECT 
                revenue_mtd, expenses_mtd, profit_margin, customer_count,
                churn_rate, nps_score, team_size, runway_months
            FROM governance.executive_metrics
            WHERE metric_date = CURRENT_DATE
            LIMIT 1
        """)
        
        metrics = cur.fetchone()
        
        # Get pending approvals count
        cur.execute("""
            SELECT COUNT(*) FROM governance.approval_requests
            WHERE status = 'pending'
        """)
        pending_approvals = cur.fetchone()[0] or 0
        
        # Get recent alerts
        cur.execute("""
            SELECT COUNT(*) FROM governance.notification_history
            WHERE priority IN ('critical', 'high')
            AND sent_at > NOW() - INTERVAL '24 hours'
        """)
        recent_alerts = cur.fetchone()[0] or 0
        
        cur.close()
        conn.close()
        
        dashboard_data = {
            "metrics": {
                "revenue_mtd": metrics[0] if metrics else 0,
                "expenses_mtd": metrics[1] if metrics else 0,
                "profit_margin": float(metrics[2]) if metrics and metrics[2] else 0,
                "customer_count": metrics[3] if metrics else 0,
                "churn_rate": float(metrics[4]) if metrics and metrics[4] else 0,
                "nps_score": metrics[5] if metrics else 0,
                "team_size": metrics[6] if metrics else 0,
                "runway_months": float(metrics[7]) if metrics and metrics[7] else 0
            },
            "alerts": {
                "pending_approvals": pending_approvals,
                "recent_critical_alerts": recent_alerts
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        print(f"Error getting executive dashboard: {e}")
        return {
            "metrics": {},
            "alerts": {},
            "error": str(e)
        }

@router.post("/workflows/create")
async def create_approval_workflow(
    workflow: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new approval workflow"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        workflow_id = str(uuid.uuid4())
        
        cur.execute("""
            INSERT INTO governance.approval_workflows (
                id, name, description, approval_level, approval_type,
                threshold_value, approval_chain, auto_approve_conditions,
                timeout_hours, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
        """, (
            workflow_id,
            workflow.get('name'),
            workflow.get('description'),
            workflow.get('approval_level', 'operational'),
            workflow.get('approval_type'),
            json.dumps(workflow.get('threshold')),
            json.dumps(workflow.get('approval_chain', [])),
            json.dumps(workflow.get('auto_approve')),
            workflow.get('timeout_hours', 48)
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "workflow_id": workflow_id,
            "status": "created",
            "message": "Approval workflow created successfully"
        }
        
    except Exception as e:
        print(f"Error creating workflow: {e} RETURNING * RETURNING *")
        raise HTTPException(status_code=500, detail=str(e))