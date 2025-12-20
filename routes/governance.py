from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from core.supabase_auth import get_current_user  # SUPABASE AUTH

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/governance", tags=["Governance"])


def _get_db_engine():
    from database import engine as db_engine

    if db_engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db_engine


def _maybe_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


@router.get("/notifications/rules")
async def get_notification_rules(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get all notification rules"""
    try:
        with _get_db_engine().connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, name, description, trigger_type, trigger_conditions,
                           priority, channels, recipients, is_active, created_at
                    FROM governance.notification_rules
                    WHERE is_active = true
                    ORDER BY priority DESC, name
                    """
                )
            ).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "description": r["description"],
                "trigger_type": r["trigger_type"],
                "trigger_conditions": _maybe_json(r.get("trigger_conditions")),
                "priority": r["priority"],
                "channels": _maybe_json(r.get("channels")),
                "recipients": _maybe_json(r.get("recipients")),
                "is_active": r["is_active"],
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting notification rules: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch notification rules")


@router.post("/notifications/send")
async def send_notification(
    notification: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Queue a notification for sending (no fake 'sent' response)."""
    recipients = notification.get("recipients")
    if not isinstance(recipients, list) or not recipients:
        raise HTTPException(status_code=400, detail="recipients must be a non-empty list")

    channels = notification.get("channels") or ["email"]
    if not isinstance(channels, list) or not channels:
        raise HTTPException(status_code=400, detail="channels must be a non-empty list")

    notification_id = str(uuid.uuid4())

    try:
        with _get_db_engine().connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO governance.notification_history (
                        notification_id, priority, channels, recipients,
                        subject, message, metadata, status, sent_at
                    ) VALUES (
                        :notification_id, :priority, :channels, :recipients,
                        :subject, :message, :metadata, :status, :sent_at
                    )
                    """
                ),
                {
                    "notification_id": notification_id,
                    "priority": notification.get("priority", "medium"),
                    "channels": json.dumps(channels),
                    "recipients": json.dumps(recipients),
                    "subject": notification.get("subject", "System Notification"),
                    "message": notification.get("message", ""),
                    "metadata": json.dumps(notification.get("metadata", {})),
                    "status": "queued",
                    "sent_at": None,
                },
            )
            conn.commit()

        return {"notification_id": notification_id, "status": "queued"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error queueing notification: %s", e)
        raise HTTPException(status_code=500, detail="Failed to queue notification")


@router.get("/approvals/pending")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get pending approval requests"""
    try:
        with _get_db_engine().connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        ar.id, ar.request_id, ar.request_type, ar.requester,
                        ar.subject, ar.details, ar.priority, ar.status,
                        ar.requested_at, ar.expires_at, aw.name as workflow_name
                    FROM governance.approval_requests ar
                    LEFT JOIN governance.approval_workflows aw ON ar.workflow_id = aw.id
                    WHERE ar.status = 'pending'
                      AND (ar.expires_at IS NULL OR ar.expires_at > NOW())
                    ORDER BY ar.priority DESC, ar.requested_at ASC
                    """
                )
            ).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "request_id": r["request_id"],
                "request_type": r["request_type"],
                "requester": r["requester"],
                "subject": r["subject"],
                "details": _maybe_json(r.get("details")),
                "priority": r["priority"],
                "status": r["status"],
                "requested_at": r["requested_at"].isoformat() if r.get("requested_at") else None,
                "expires_at": r["expires_at"].isoformat() if r.get("expires_at") else None,
                "workflow_name": r.get("workflow_name"),
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting pending approvals: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch approvals")


@router.post("/approvals/{request_id}/approve")
async def approve_request(
    request_id: str,
    approval_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Approve a request"""
    try:
        with _get_db_engine().connect() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE governance.approval_requests
                    SET status = 'approved',
                        decision = 'approved',
                        decided_by = :decided_by,
                        decision_notes = :decision_notes,
                        decided_at = :decided_at
                    WHERE request_id = :request_id AND status = 'pending'
                    """
                ),
                {
                    "decided_by": current_user.get("email"),
                    "decision_notes": approval_data.get("notes", ""),
                    "decided_at": datetime.utcnow(),
                    "request_id": request_id,
                },
            )
            conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found or already processed")

        return {"request_id": request_id, "status": "approved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error approving request: %s", e)
        raise HTTPException(status_code=500, detail="Failed to approve request")


@router.post("/approvals/{request_id}/reject")
async def reject_request(
    request_id: str,
    rejection_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Reject a request"""
    try:
        with _get_db_engine().connect() as conn:
            result = conn.execute(
                text(
                    """
                    UPDATE governance.approval_requests
                    SET status = 'rejected',
                        decision = 'rejected',
                        decided_by = :decided_by,
                        decision_notes = :decision_notes,
                        decided_at = :decided_at
                    WHERE request_id = :request_id AND status = 'pending'
                    """
                ),
                {
                    "decided_by": current_user.get("email"),
                    "decision_notes": rejection_data.get("reason", ""),
                    "decided_at": datetime.utcnow(),
                    "request_id": request_id,
                },
            )
            conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Request not found or already processed")

        return {"request_id": request_id, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error rejecting request: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reject request")


@router.get("/policies")
async def get_policies(current_user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Get all governance policies"""
    try:
        with _get_db_engine().connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        id, policy_key, policy_name, description, category,
                        rules, enforcement_level, is_active, created_at
                    FROM governance.policies
                    WHERE is_active = true
                    ORDER BY category, policy_name
                    """
                )
            ).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "policy_key": r["policy_key"],
                "policy_name": r["policy_name"],
                "description": r["description"],
                "category": r["category"],
                "rules": _maybe_json(r.get("rules")),
                "enforcement_level": r["enforcement_level"],
                "is_active": r["is_active"],
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting policies: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch policies")


@router.get("/dashboard/executive")
async def get_executive_dashboard(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get executive dashboard data"""
    try:
        with _get_db_engine().connect() as conn:
            metrics = conn.execute(
                text(
                    """
                    SELECT
                        revenue_mtd, expenses_mtd, profit_margin, customer_count,
                        churn_rate, nps_score, team_size, runway_months
                    FROM governance.executive_metrics
                    WHERE metric_date = CURRENT_DATE
                    LIMIT 1
                    """
                )
            ).mappings().first()

            pending_approvals = conn.execute(
                text("SELECT COUNT(*) FROM governance.approval_requests WHERE status = 'pending'")
            ).scalar() or 0

            recent_alerts = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM governance.notification_history
                    WHERE priority IN ('critical', 'high')
                      AND sent_at > NOW() - INTERVAL '24 hours'
                    """
                )
            ).scalar() or 0

        return {
            "metrics": {
                "revenue_mtd": metrics["revenue_mtd"] if metrics else 0,
                "expenses_mtd": metrics["expenses_mtd"] if metrics else 0,
                "profit_margin": float(metrics["profit_margin"]) if metrics and metrics.get("profit_margin") else 0,
                "customer_count": metrics["customer_count"] if metrics else 0,
                "churn_rate": float(metrics["churn_rate"]) if metrics and metrics.get("churn_rate") else 0,
                "nps_score": metrics["nps_score"] if metrics else 0,
                "team_size": metrics["team_size"] if metrics else 0,
                "runway_months": float(metrics["runway_months"]) if metrics and metrics.get("runway_months") else 0,
            },
            "alerts": {"pending_approvals": pending_approvals, "recent_critical_alerts": recent_alerts},
            "last_updated": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting executive dashboard: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch executive dashboard")


@router.post("/workflows/create")
async def create_approval_workflow(
    workflow: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new approval workflow"""
    workflow_id = str(uuid.uuid4())
    try:
        with _get_db_engine().connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO governance.approval_workflows (
                        id, name, description, approval_level, approval_type,
                        threshold_value, approval_chain, auto_approve_conditions,
                        timeout_hours, is_active
                    ) VALUES (
                        :id, :name, :description, :approval_level, :approval_type,
                        :threshold_value, :approval_chain, :auto_approve_conditions,
                        :timeout_hours, true
                    )
                    """
                ),
                {
                    "id": workflow_id,
                    "name": workflow.get("name"),
                    "description": workflow.get("description"),
                    "approval_level": workflow.get("approval_level", "operational"),
                    "approval_type": workflow.get("approval_type"),
                    "threshold_value": json.dumps(workflow.get("threshold")),
                    "approval_chain": json.dumps(workflow.get("approval_chain", [])),
                    "auto_approve_conditions": json.dumps(workflow.get("auto_approve")),
                    "timeout_hours": workflow.get("timeout_hours", 48),
                },
            )
            conn.commit()

        return {"workflow_id": workflow_id, "status": "created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating workflow: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create approval workflow")
