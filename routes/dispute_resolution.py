"""
Dispute Resolution System
Task 38: Comprehensive dispute management for invoices, payments, and services
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, UploadFile, File
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid
import asyncpg
import logging
from decimal import Decimal
import json

from database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Enums for dispute management
class DisputeType(str, Enum):
    BILLING = "billing"
    SERVICE = "service"
    QUALITY = "quality"
    WARRANTY = "warranty"
    CONTRACT = "contract"
    PAYMENT = "payment"
    PRICING = "pricing"
    OTHER = "other"

class DisputeStatus(str, Enum):
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    PENDING_INFO = "pending_info"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    LEGAL = "legal"

class DisputePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResolutionType(str, Enum):
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"
    SERVICE_CREDIT = "service_credit"
    REPLACEMENT = "replacement"
    REPAIR = "repair"
    COMPENSATION = "compensation"
    APOLOGY = "apology"
    NO_ACTION = "no_action"
    LEGAL_SETTLEMENT = "legal_settlement"

class CommunicationMethod(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    IN_PERSON = "in_person"
    PORTAL = "portal"
    LETTER = "letter"
    VIDEO_CALL = "video_call"

class EvidenceType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    EMAIL = "email"
    INVOICE = "invoice"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    TESTIMONY = "testimony"
    EXPERT_REPORT = "expert_report"
    OTHER = "other"

# Pydantic models
class DisputeCreate(BaseModel):
    customer_id: str
    invoice_id: Optional[str] = None
    job_id: Optional[str] = None
    dispute_type: DisputeType
    priority: DisputePriority = DisputePriority.MEDIUM
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    disputed_amount: float = Field(ge=0)
    requested_resolution: Optional[str] = None
    contact_preference: CommunicationMethod = CommunicationMethod.EMAIL
    metadata: Optional[Dict[str, Any]] = None

class DisputeUpdate(BaseModel):
    status: Optional[DisputeStatus] = None
    priority: Optional[DisputePriority] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    requested_resolution: Optional[str] = None
    internal_notes: Optional[str] = None

class DisputeResponse(BaseModel):
    id: str
    dispute_number: str
    customer_id: str
    customer_name: Optional[str] = None
    invoice_id: Optional[str] = None
    job_id: Optional[str] = None
    dispute_type: DisputeType
    status: DisputeStatus
    priority: DisputePriority
    subject: str
    description: str
    disputed_amount: float
    requested_resolution: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None
    resolution_amount: Optional[float] = None
    resolution_notes: Optional[str] = None
    contact_preference: CommunicationMethod
    submitted_date: datetime
    acknowledged_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    days_to_resolve: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DisputeCommunication(BaseModel):
    dispute_id: str
    direction: str = Field(..., pattern="^(inbound|outbound)$")
    method: CommunicationMethod
    subject: Optional[str] = None
    message: str
    sender: str
    recipient: str
    attachments: Optional[List[str]] = None

class DisputeEvidence(BaseModel):
    dispute_id: str
    evidence_type: EvidenceType
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    submitted_by: str
    metadata: Optional[Dict[str, Any]] = None

class DisputeResolution(BaseModel):
    dispute_id: str
    resolution_type: ResolutionType
    resolution_amount: Optional[float] = None
    resolution_notes: str
    implementation_date: Optional[date] = None
    approved_by: str
    customer_accepted: bool = False
    follow_up_required: bool = False

class DisputeEscalation(BaseModel):
    dispute_id: str
    escalation_reason: str
    escalated_to: str
    urgency: str = Field(..., pattern="^(low|medium|high|critical)$")
    expected_resolution_date: Optional[date] = None
    notes: Optional[str] = None

class DisputeTemplate(BaseModel):
    template_name: str
    template_type: str  # acknowledgment, resolution, rejection, etc.
    subject: str
    content: str
    variables: List[str]
    is_active: bool = True

# Helper functions
def generate_dispute_number() -> str:
    """Generate unique dispute number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"DSP-{timestamp}-{random_suffix}"

async def calculate_dispute_metrics(conn, customer_id: str = None) -> Dict[str, Any]:
    """Calculate dispute metrics"""
    where_clause = "WHERE customer_id = $1" if customer_id else ""
    params = [customer_id] if customer_id else []

    query = f"""
    SELECT
        COUNT(*) as total_disputes,
        COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_disputes,
        COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_disputes,
        COUNT(CASE WHEN status NOT IN ('resolved', 'rejected', 'withdrawn') THEN 1 END) as open_disputes,
        AVG(CASE
            WHEN resolved_date IS NOT NULL
            THEN EXTRACT(DAY FROM resolved_date - submitted_date)
            ELSE NULL
        END) as avg_resolution_days,
        SUM(disputed_amount) as total_disputed_amount,
        SUM(CASE WHEN resolution_amount IS NOT NULL THEN resolution_amount ELSE 0 END) as total_resolved_amount
    FROM disputes
    {where_clause}
    """

    result = await conn.fetchrow(query, *params)

    return {
        "total_disputes": result["total_disputes"] or 0,
        "resolved_disputes": result["resolved_disputes"] or 0,
        "rejected_disputes": result["rejected_disputes"] or 0,
        "open_disputes": result["open_disputes"] or 0,
        "resolution_rate": round((result["resolved_disputes"] / result["total_disputes"] * 100) if result["total_disputes"] > 0 else 0, 2),
        "avg_resolution_days": round(float(result["avg_resolution_days"]) if result["avg_resolution_days"] else 0, 1),
        "total_disputed_amount": float(result["total_disputed_amount"]) if result["total_disputed_amount"] else 0,
        "total_resolved_amount": float(result["total_resolved_amount"]) if result["total_resolved_amount"] else 0
    }

async def check_sla_compliance(conn, dispute_id: str) -> Dict[str, Any]:
    """Check if dispute is within SLA"""
    dispute = await conn.fetchrow("""
        SELECT priority, submitted_date, acknowledged_date, resolved_date
        FROM disputes
        WHERE id = $1
    """, uuid.UUID(dispute_id))

    if not dispute:
        return {"compliant": False, "message": "Dispute not found"}

    # Define SLA targets (in hours)
    sla_acknowledgment = {
        "critical": 2,
        "high": 4,
        "medium": 12,
        "low": 24
    }

    sla_resolution = {
        "critical": 24,
        "high": 72,
        "medium": 120,
        "low": 240
    }

    priority = dispute["priority"]
    now = datetime.now()

    # Check acknowledgment SLA
    ack_target = sla_acknowledgment[priority]
    if dispute["acknowledged_date"]:
        ack_hours = (dispute["acknowledged_date"] - dispute["submitted_date"]).total_seconds() / 3600
        ack_compliant = ack_hours <= ack_target
    else:
        hours_since = (now - dispute["submitted_date"]).total_seconds() / 3600
        ack_compliant = hours_since <= ack_target

    # Check resolution SLA
    res_target = sla_resolution[priority]
    if dispute["resolved_date"]:
        res_hours = (dispute["resolved_date"] - dispute["submitted_date"]).total_seconds() / 3600
        res_compliant = res_hours <= res_target
        status = "resolved"
    else:
        hours_since = (now - dispute["submitted_date"]).total_seconds() / 3600
        res_compliant = hours_since <= res_target
        status = "open"

    return {
        "compliant": ack_compliant and res_compliant,
        "acknowledgment_sla": ack_target,
        "acknowledgment_compliant": ack_compliant,
        "resolution_sla": res_target,
        "resolution_compliant": res_compliant,
        "status": status
    }

# API Endpoints
@router.post("/disputes", response_model=DisputeResponse)
async def create_dispute(
    dispute: DisputeCreate,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Create new dispute"""
    try:
        dispute_id = str(uuid.uuid4())
        dispute_number = generate_dispute_number()

        # Get customer name
        customer = await conn.fetchrow(
            "SELECT name FROM customers WHERE id = $1",
            uuid.UUID(dispute.customer_id)
        )

        # Create dispute
        result = await conn.fetchrow("""
            INSERT INTO disputes (
                id, dispute_number, customer_id, invoice_id, job_id,
                dispute_type, status, priority, subject, description,
                disputed_amount, requested_resolution, contact_preference,
                submitted_date, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING *
        """,
            uuid.UUID(dispute_id),
            dispute_number,
            uuid.UUID(dispute.customer_id),
            uuid.UUID(dispute.invoice_id) if dispute.invoice_id else None,
            uuid.UUID(dispute.job_id) if dispute.job_id else None,
            dispute.dispute_type,
            DisputeStatus.SUBMITTED,
            dispute.priority,
            dispute.subject,
            dispute.description,
            dispute.disputed_amount,
            dispute.requested_resolution,
            dispute.contact_preference,
            datetime.now(),
            json.dumps(dispute.metadata) if dispute.metadata else None
        )

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "created",
            f"Dispute created: {dispute.subject}",
            "customer"
        )

        # Send acknowledgment in background
        background_tasks.add_task(
            send_dispute_acknowledgment,
            dispute_id,
            dispute.customer_id,
            dispute_number
        )

        response = DisputeResponse(**dict(result))
        if customer:
            response.customer_name = customer["name"]

        return response

    except Exception as e:
        logger.error(f"Error creating dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disputes", response_model=List[DisputeResponse])
async def get_disputes(
    status: Optional[DisputeStatus] = None,
    priority: Optional[DisputePriority] = None,
    dispute_type: Optional[DisputeType] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    conn = Depends(get_db_connection)
):
    """Get disputes with filters"""
    try:
        # Build query
        query = """
            SELECT d.*, c.name as customer_name
            FROM disputes d
            LEFT JOIN customers c ON d.customer_id = c.id
            WHERE 1=1
        """
        params = []
        param_count = 0

        if status:
            param_count += 1
            query += f" AND d.status = ${param_count}"
            params.append(status)

        if priority:
            param_count += 1
            query += f" AND d.priority = ${param_count}"
            params.append(priority)

        if dispute_type:
            param_count += 1
            query += f" AND d.dispute_type = ${param_count}"
            params.append(dispute_type)

        if customer_id:
            param_count += 1
            query += f" AND d.customer_id = ${param_count}"
            params.append(uuid.UUID(customer_id))

        if assigned_to:
            param_count += 1
            query += f" AND d.assigned_to = ${param_count}"
            params.append(assigned_to)

        if date_from:
            param_count += 1
            query += f" AND d.submitted_date >= ${param_count}"
            params.append(datetime.combine(date_from, datetime.min.time()))

        if date_to:
            param_count += 1
            query += f" AND d.submitted_date <= ${param_count}"
            params.append(datetime.combine(date_to, datetime.max.time()))

        query += f" ORDER BY d.created_at DESC LIMIT {limit} OFFSET {offset}"

        rows = await conn.fetch(query, *params)

        return [DisputeResponse(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching disputes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: str,
    conn = Depends(get_db_connection)
):
    """Get dispute details"""
    try:
        result = await conn.fetchrow("""
            SELECT d.*, c.name as customer_name
            FROM disputes d
            LEFT JOIN customers c ON d.customer_id = c.id
            WHERE d.id = $1
        """, uuid.UUID(dispute_id))

        if not result:
            raise HTTPException(status_code=404, detail="Dispute not found")

        return DisputeResponse(**dict(result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/disputes/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: str,
    update: DisputeUpdate,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Update dispute"""
    try:
        # Build update query
        update_fields = []
        params = []
        param_count = 0

        if update.status is not None:
            param_count += 1
            update_fields.append(f"status = ${param_count}")
            params.append(update.status)

            # Set acknowledged date if status changes from submitted
            if update.status == DisputeStatus.ACKNOWLEDGED:
                param_count += 1
                update_fields.append(f"acknowledged_date = ${param_count}")
                params.append(datetime.now())

            # Set resolved date if resolved
            if update.status in [DisputeStatus.RESOLVED, DisputeStatus.REJECTED]:
                param_count += 1
                update_fields.append(f"resolved_date = ${param_count}")
                params.append(datetime.now())

        if update.priority is not None:
            param_count += 1
            update_fields.append(f"priority = ${param_count}")
            params.append(update.priority)

        if update.assigned_to is not None:
            param_count += 1
            update_fields.append(f"assigned_to = ${param_count}")
            params.append(update.assigned_to)

        if update.description is not None:
            param_count += 1
            update_fields.append(f"description = ${param_count}")
            params.append(update.description)

        if update.requested_resolution is not None:
            param_count += 1
            update_fields.append(f"requested_resolution = ${param_count}")
            params.append(update.requested_resolution)

        if update.internal_notes is not None:
            param_count += 1
            update_fields.append(f"internal_notes = ${param_count}")
            params.append(update.internal_notes)

        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.now())

        param_count += 1
        params.append(uuid.UUID(dispute_id))

        query = f"""
            UPDATE disputes
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """

        result = await conn.fetchrow(query, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "updated",
            f"Dispute updated: {', '.join(update_fields)}",
            "staff"
        )

        # Send notification if status changed
        if update.status:
            background_tasks.add_task(
                send_status_notification,
                dispute_id,
                update.status
            )

        return DisputeResponse(**dict(result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disputes/{dispute_id}/communications")
async def add_communication(
    dispute_id: str,
    communication: DisputeCommunication,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Add communication to dispute"""
    try:
        comm_id = str(uuid.uuid4())

        await conn.execute("""
            INSERT INTO dispute_communications (
                id, dispute_id, direction, method, subject,
                message, sender, recipient, attachments
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            uuid.UUID(comm_id),
            uuid.UUID(dispute_id),
            communication.direction,
            communication.method,
            communication.subject,
            communication.message,
            communication.sender,
            communication.recipient,
            json.dumps(communication.attachments) if communication.attachments else None
        )

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "communication",
            f"{communication.direction} {communication.method} communication added",
            communication.sender
        )

        return {"message": "Communication added successfully", "id": comm_id}

    except Exception as e:
        logger.error(f"Error adding communication: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disputes/{dispute_id}/evidence")
async def add_evidence(
    dispute_id: str,
    evidence: DisputeEvidence,
    conn = Depends(get_db_connection)
):
    """Add evidence to dispute"""
    try:
        evidence_id = str(uuid.uuid4())

        await conn.execute("""
            INSERT INTO dispute_evidence (
                id, dispute_id, evidence_type, title, description,
                file_url, submitted_by, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            uuid.UUID(evidence_id),
            uuid.UUID(dispute_id),
            evidence.evidence_type,
            evidence.title,
            evidence.description,
            evidence.file_url,
            evidence.submitted_by,
            json.dumps(evidence.metadata) if evidence.metadata else None
        )

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "evidence_added",
            f"Evidence added: {evidence.title}",
            evidence.submitted_by
        )

        return {"message": "Evidence added successfully", "id": evidence_id}

    except Exception as e:
        logger.error(f"Error adding evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    resolution: DisputeResolution,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Resolve dispute"""
    try:
        # Update dispute with resolution
        result = await conn.fetchrow("""
            UPDATE disputes
            SET status = 'resolved',
                resolution_type = $1,
                resolution_amount = $2,
                resolution_notes = $3,
                resolved_date = $4,
                resolution_approved_by = $5,
                customer_accepted = $6,
                updated_at = NOW()
            WHERE id = $7
            RETURNING *
        """,
            resolution.resolution_type,
            resolution.resolution_amount,
            resolution.resolution_notes,
            datetime.now(),
            resolution.approved_by,
            resolution.customer_accepted,
            uuid.UUID(dispute_id)
        )

        if not result:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # Create resolution record
        resolution_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO dispute_resolutions (
                id, dispute_id, resolution_type, resolution_amount,
                resolution_notes, implementation_date, approved_by,
                customer_accepted, follow_up_required
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            uuid.UUID(resolution_id),
            uuid.UUID(dispute_id),
            resolution.resolution_type,
            resolution.resolution_amount,
            resolution.resolution_notes,
            resolution.implementation_date,
            resolution.approved_by,
            resolution.customer_accepted,
            resolution.follow_up_required
        )

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "resolved",
            f"Dispute resolved: {resolution.resolution_type}",
            resolution.approved_by
        )

        # Send resolution notification
        background_tasks.add_task(
            send_resolution_notification,
            dispute_id,
            resolution.resolution_type,
            resolution.resolution_notes
        )

        # Process refund if applicable
        if resolution.resolution_type in [ResolutionType.FULL_REFUND, ResolutionType.PARTIAL_REFUND]:
            background_tasks.add_task(
                process_refund,
                dispute_id,
                resolution.resolution_amount
            )

        return {"message": "Dispute resolved successfully", "resolution_id": resolution_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disputes/{dispute_id}/escalate")
async def escalate_dispute(
    dispute_id: str,
    escalation: DisputeEscalation,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Escalate dispute"""
    try:
        # Update dispute status
        result = await conn.fetchrow("""
            UPDATE disputes
            SET status = 'escalated',
                assigned_to = $1,
                priority = CASE
                    WHEN $2 = 'critical' THEN 'critical'
                    WHEN $2 = 'high' AND priority != 'critical' THEN 'high'
                    ELSE priority
                END,
                updated_at = NOW()
            WHERE id = $3
            RETURNING *
        """,
            escalation.escalated_to,
            escalation.urgency,
            uuid.UUID(dispute_id)
        )

        if not result:
            raise HTTPException(status_code=404, detail="Dispute not found")

        # Create escalation record
        escalation_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO dispute_escalations (
                id, dispute_id, escalation_reason, escalated_to,
                urgency, expected_resolution_date, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            uuid.UUID(escalation_id),
            uuid.UUID(dispute_id),
            escalation.escalation_reason,
            escalation.escalated_to,
            escalation.urgency,
            escalation.expected_resolution_date,
            escalation.notes
        )

        # Log activity
        await conn.execute("""
            INSERT INTO dispute_activities (
                dispute_id, activity_type, description, performed_by
            ) VALUES ($1, $2, $3, $4)
        """,
            uuid.UUID(dispute_id),
            "escalated",
            f"Dispute escalated to {escalation.escalated_to}: {escalation.escalation_reason}",
            "system"
        )

        # Send escalation notifications
        background_tasks.add_task(
            send_escalation_notification,
            dispute_id,
            escalation.escalated_to,
            escalation.urgency
        )

        return {"message": "Dispute escalated successfully", "escalation_id": escalation_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating dispute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disputes/{dispute_id}/timeline")
async def get_dispute_timeline(
    dispute_id: str,
    conn = Depends(get_db_connection)
):
    """Get dispute timeline"""
    try:
        # Get all activities
        activities = await conn.fetch("""
            SELECT activity_type, description, performed_by, created_at
            FROM dispute_activities
            WHERE dispute_id = $1
            ORDER BY created_at ASC
        """, uuid.UUID(dispute_id))

        # Get communications
        communications = await conn.fetch("""
            SELECT direction, method, subject, sender, created_at
            FROM dispute_communications
            WHERE dispute_id = $1
            ORDER BY created_at ASC
        """, uuid.UUID(dispute_id))

        # Combine and sort timeline
        timeline = []

        for activity in activities:
            timeline.append({
                "type": "activity",
                "subtype": activity["activity_type"],
                "description": activity["description"],
                "user": activity["performed_by"],
                "timestamp": activity["created_at"]
            })

        for comm in communications:
            timeline.append({
                "type": "communication",
                "subtype": comm["method"],
                "description": f"{comm['direction']} communication: {comm['subject'] or 'No subject'}",
                "user": comm["sender"],
                "timestamp": comm["created_at"]
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disputes/{dispute_id}/sla")
async def check_dispute_sla(
    dispute_id: str,
    conn = Depends(get_db_connection)
):
    """Check dispute SLA compliance"""
    try:
        return await check_sla_compliance(conn, dispute_id)
    except Exception as e:
        logger.error(f"Error checking SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disputes/analytics/summary")
async def get_dispute_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    conn = Depends(get_db_connection)
):
    """Get dispute analytics"""
    try:
        # Overall metrics
        metrics = await calculate_dispute_metrics(conn)

        # Type breakdown
        type_query = """
            SELECT dispute_type, COUNT(*) as count
            FROM disputes
            WHERE 1=1
        """
        params = []
        param_count = 0

        if date_from:
            param_count += 1
            type_query += f" AND submitted_date >= ${param_count}"
            params.append(datetime.combine(date_from, datetime.min.time()))

        if date_to:
            param_count += 1
            type_query += f" AND submitted_date <= ${param_count}"
            params.append(datetime.combine(date_to, datetime.max.time()))

        type_query += " GROUP BY dispute_type"

        type_breakdown = await conn.fetch(type_query, *params)

        # Resolution breakdown
        resolution_breakdown = await conn.fetch("""
            SELECT resolution_type, COUNT(*) as count, SUM(resolution_amount) as total_amount
            FROM disputes
            WHERE status = 'resolved' AND resolution_type IS NOT NULL
            GROUP BY resolution_type
        """)

        # Trend data (last 30 days)
        trend_data = await conn.fetch("""
            SELECT
                DATE(submitted_date) as date,
                COUNT(*) as new_disputes,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_disputes
            FROM disputes
            WHERE submitted_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(submitted_date)
            ORDER BY date
        """)

        return {
            "metrics": metrics,
            "type_breakdown": [dict(row) for row in type_breakdown],
            "resolution_breakdown": [
                {
                    "type": row["resolution_type"],
                    "count": row["count"],
                    "total_amount": float(row["total_amount"]) if row["total_amount"] else 0
                }
                for row in resolution_breakdown
            ],
            "trend_data": [dict(row) for row in trend_data]
        }

    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def send_dispute_acknowledgment(dispute_id: str, customer_id: str, dispute_number: str):
    """Send dispute acknowledgment email"""
    logger.info(f"Sending acknowledgment for dispute {dispute_number}")
    # Implementation would send actual email

async def send_status_notification(dispute_id: str, new_status: str):
    """Send status change notification"""
    logger.info(f"Sending status notification for dispute {dispute_id}: {new_status}")
    # Implementation would send actual notification

async def send_resolution_notification(dispute_id: str, resolution_type: str, notes: str):
    """Send resolution notification"""
    logger.info(f"Sending resolution notification for dispute {dispute_id}")
    # Implementation would send actual notification

async def send_escalation_notification(dispute_id: str, escalated_to: str, urgency: str):
    """Send escalation notification"""
    logger.info(f"Sending escalation notification for dispute {dispute_id} to {escalated_to}")
    # Implementation would send actual notification

async def process_refund(dispute_id: str, amount: float):
    """Process refund for resolved dispute"""
    logger.info(f"Processing refund of ${amount} for dispute {dispute_id} RETURNING * RETURNING *")
    # Implementation would process actual refund