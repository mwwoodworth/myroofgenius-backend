"""
Job Lifecycle Management
Complete job lifecycle from creation to completion with status transitions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import json
from uuid import uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_modification, log_data_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["Job Lifecycle"])

# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class JobStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    INVOICED = "invoiced"

class JobPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class JobType(str, Enum):
    INSTALLATION = "installation"
    REPAIR = "repair"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    CONSULTATION = "consultation"
    WARRANTY = "warranty"
    EMERGENCY = "emergency"

class JobCreate(BaseModel):
    customer_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_type: JobType
    priority: JobPriority = JobPriority.MEDIUM
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    estimated_cost: Optional[float] = Field(None, ge=0)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    assigned_crew_id: Optional[str] = None
    assigned_employees: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}

    @validator('scheduled_end')
    def validate_dates(cls, v, values):
        if v and 'scheduled_start' in values and values['scheduled_start']:
            if v < values['scheduled_start']:
                raise ValueError('Scheduled end must be after scheduled start')
        return v

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[JobType] = None
    priority: Optional[JobPriority] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    assigned_crew_id: Optional[str] = None
    assigned_employees: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class JobStatusTransition(BaseModel):
    new_status: JobStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    effective_date: Optional[datetime] = None

class JobNote(BaseModel):
    content: str
    is_internal: bool = False
    attachments: Optional[List[str]] = []

# ============================================================================
# JOB LIFECYCLE ENDPOINTS
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_job(
    job: JobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Create a new job"""
    try:
        job_id = str(uuid4())
        
        # Verify customer exists
        customer = db.execute(
            text("SELECT id, name FROM customers WHERE id = :id"),
            {"id": job.customer_id}
        ).fetchone()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Create job
        db.execute(
            text("""
                INSERT INTO jobs (
                    id, customer_id, title, description,
                    job_type, priority, status,
                    scheduled_start, scheduled_end,
                    estimated_hours, estimated_cost,
                    service_address, service_city, service_state, service_zip,
                    assigned_crew_id, tags, custom_fields,
                    created_at, created_by, updated_at
                )
                VALUES (
                    :id, :customer_id, :title, :description,
                    :job_type, :priority, :status,
                    :scheduled_start, :scheduled_end,
                    :estimated_hours, :estimated_cost,
                    :address, :city, :state, :zip,
                    :crew_id, :tags::jsonb, :custom_fields::jsonb,
                    NOW(), :created_by, NOW()
                )
            """),
            {
                "id": job_id,
                "customer_id": job.customer_id,
                "title": job.title,
                "description": job.description,
                "job_type": job.job_type,
                "priority": job.priority,
                "status": JobStatus.DRAFT if not job.scheduled_start else JobStatus.SCHEDULED,
                "scheduled_start": job.scheduled_start,
                "scheduled_end": job.scheduled_end,
                "estimated_hours": job.estimated_hours,
                "estimated_cost": job.estimated_cost,
                "address": job.address,
                "city": job.city,
                "state": job.state,
                "zip": job.zip_code,
                "crew_id": job.assigned_crew_id,
                "tags": json.dumps(job.tags or []),
                "custom_fields": json.dumps(job.custom_fields or {}),
                "created_by": current_user["id"]
            }
        )
        
        # Add assigned employees
        if job.assigned_employees:
            for employee_id in job.assigned_employees:
                db.execute(
                    text("""
                        INSERT INTO employee_jobs (id, employee_id, job_id, assigned_at)
                        VALUES (:id, :employee_id, :job_id, NOW())
                    """),
                    {
                        "id": str(uuid4()),
                        "employee_id": employee_id,
                        "job_id": job_id
                    }
                )
        
        # Create initial status history
        db.execute(
            text("""
                INSERT INTO job_status_history (
                    id, job_id, from_status, to_status,
                    changed_by, changed_at, reason
                )
                VALUES (
                    :id, :job_id, NULL, :status,
                    :user_id, NOW(), 'Job created'
                )
            """),
            {
                "id": str(uuid4()),
                "job_id": job_id,
                "status": JobStatus.DRAFT if not job.scheduled_start else JobStatus.SCHEDULED,
                "user_id": current_user["id"]
            }
        )
        
        db.commit()
        
        # Log creation
        log_data_modification(
            db, current_user["id"], "jobs", "create",
            job_id, new_values=job.dict()
        )
        
        return {
            "id": job_id,
            "message": "Job created successfully",
            "status": JobStatus.DRAFT if not job.scheduled_start else JobStatus.SCHEDULED
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")

@router.put("/{job_id}/status", response_model=dict)
async def transition_job_status(
    job_id: str,
    transition: JobStatusTransition,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Transition job to a new status with validation"""
    try:
        # Get current job status
        job = db.execute(
            text("SELECT id, status, customer_id FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        current_status = job.status
        new_status = transition.new_status
        
        # Validate status transition
        valid_transitions = {
            JobStatus.DRAFT: [JobStatus.SCHEDULED, JobStatus.CANCELLED],
            JobStatus.SCHEDULED: [JobStatus.IN_PROGRESS, JobStatus.ON_HOLD, JobStatus.CANCELLED],
            JobStatus.IN_PROGRESS: [JobStatus.ON_HOLD, JobStatus.COMPLETED, JobStatus.CANCELLED],
            JobStatus.ON_HOLD: [JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
            JobStatus.COMPLETED: [JobStatus.INVOICED],
            JobStatus.CANCELLED: [],
            JobStatus.INVOICED: []
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {current_status} to {new_status}"
            )
        
        # Update job status
        update_fields = {"status": new_status, "updated_at": "NOW()"}
        
        # Set specific fields based on status
        if new_status == JobStatus.IN_PROGRESS:
            update_fields["actual_start"] = "NOW()"
        elif new_status == JobStatus.COMPLETED:
            update_fields["completed_at"] = "NOW()"
        elif new_status == JobStatus.CANCELLED:
            update_fields["cancelled_at"] = "NOW()"
        
        query = f"""
            UPDATE jobs
            SET status = :status,
                {', '.join([f'{k} = {v}' if v == 'NOW()' else f'{k} = :{k}' for k, v in update_fields.items() if k != 'status'])},
                updated_at = NOW()
            WHERE id = :id
        """
        
        db.execute(
            text(query),
            {"id": job_id, "status": new_status}
        )
        
        # Record status history
        db.execute(
            text("""
                INSERT INTO job_status_history (
                    id, job_id, from_status, to_status,
                    changed_by, changed_at, reason, notes
                )
                VALUES (
                    :id, :job_id, :from_status, :to_status,
                    :user_id, :changed_at, :reason, :notes
                )
            """),
            {
                "id": str(uuid4()),
                "job_id": job_id,
                "from_status": current_status,
                "to_status": new_status,
                "user_id": current_user["id"],
                "changed_at": transition.effective_date or datetime.utcnow(),
                "reason": transition.reason,
                "notes": transition.notes
            }
        )
        
        # Trigger side effects based on status
        if new_status == JobStatus.COMPLETED:
            # Create notification for invoicing
            db.execute(
                text("""
                    INSERT INTO notifications (
                        id, user_id, type, title, message,
                        resource_type, resource_id, created_at
                    )
                    VALUES (
                        :id, :user_id, 'job_completed',
                        'Job Completed', :message,
                        'job', :job_id, NOW()
                    )
                """),
                {
                    "id": str(uuid4()),
                    "user_id": current_user["id"],
                    "message": f"Job {job_id} has been completed and is ready for invoicing",
                    "job_id": job_id
                }
            )
        
        db.commit()
        
        # Log modification
        log_data_modification(
            db, current_user["id"], "jobs", "status_change",
            job_id, old_values={"status": current_status},
            new_values={"status": new_status}
        )
        
        return {
            "message": "Job status updated successfully",
            "old_status": current_status,
            "new_status": new_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error transitioning job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job status")

@router.get("/{job_id}/lifecycle", response_model=dict)
async def get_job_lifecycle(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get complete job lifecycle history"""
    try:
        # Get job details
        job = db.execute(
            text("""
                SELECT j.*, c.name as customer_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                WHERE j.id = :id
            """),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job_dict = dict(job._mapping)
        job_dict["id"] = str(job_dict["id"])
        job_dict["customer_id"] = str(job_dict["customer_id"])
        
        # Get status history
        history = db.execute(
            text("""
                SELECT h.*, u.name as changed_by_name
                FROM job_status_history h
                LEFT JOIN users u ON h.changed_by = u.id
                WHERE h.job_id = :job_id
                ORDER BY h.changed_at DESC
            """),
            {"job_id": job_id}
        ).fetchall()
        
        status_history = []
        for row in history:
            entry = dict(row._mapping)
            entry["id"] = str(entry["id"])
            entry["job_id"] = str(entry["job_id"])
            if entry["changed_by"]:
                entry["changed_by"] = str(entry["changed_by"])
            status_history.append(entry)
        
        # Get job events
        events = db.execute(
            text("""
                SELECT * FROM (
                    SELECT 'created' as event_type, created_at as event_date,
                           'Job created' as description,
                           created_by as user_id
                    FROM jobs WHERE id = :job_id
                    
                    UNION ALL
                    
                    SELECT 'note_added' as event_type, created_at as event_date,
                           'Note added' as description,
                           created_by as user_id
                    FROM job_notes WHERE job_id = :job_id
                    
                    UNION ALL
                    
                    SELECT 'document_uploaded' as event_type, created_at as event_date,
                           'Document uploaded: ' || name as description,
                           created_by as user_id
                    FROM documents WHERE job_id = :job_id
                    
                    UNION ALL
                    
                    SELECT 'invoice_created' as event_type, created_at as event_date,
                           'Invoice created: ' || invoice_number as description,
                           created_by as user_id
                    FROM invoices WHERE job_id = :job_id
                ) events
                ORDER BY event_date DESC
            """),
            {"job_id": job_id}
        ).fetchall()
        
        event_timeline = []
        for row in events:
            event = dict(row._mapping)
            event["event_date"] = event["event_date"].isoformat() if event["event_date"] else None
            if event.get("user_id"):
                event["user_id"] = str(event["user_id"])
            event_timeline.append(event)
        
        # Calculate lifecycle metrics
        metrics = {
            "total_duration_days": None,
            "time_to_start_days": None,
            "execution_time_days": None,
            "status_changes": len(status_history),
            "current_phase": _get_job_phase(job.status)
        }
        
        if job.created_at and job.completed_at:
            metrics["total_duration_days"] = (job.completed_at - job.created_at).days
        
        if job.created_at and job.actual_start:
            metrics["time_to_start_days"] = (job.actual_start - job.created_at).days
        
        if job.actual_start and job.completed_at:
            metrics["execution_time_days"] = (job.completed_at - job.actual_start).days
        
        log_data_access(db, current_user["id"], "jobs", "lifecycle", 1)
        
        return {
            "job": job_dict,
            "status_history": status_history,
            "event_timeline": event_timeline,
            "metrics": metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job lifecycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job lifecycle")

@router.post("/{job_id}/notes", response_model=dict)
async def add_job_note(
    job_id: str,
    note: JobNote,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Add a note to a job"""
    try:
        # Verify job exists
        job = db.execute(
            text("SELECT id FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        note_id = str(uuid4())
        
        db.execute(
            text("""
                INSERT INTO job_notes (
                    id, job_id, content, is_internal,
                    attachments, created_by, created_at
                )
                VALUES (
                    :id, :job_id, :content, :is_internal,
                    :attachments::jsonb, :user_id, NOW()
                )
            """),
            {
                "id": note_id,
                "job_id": job_id,
                "content": note.content,
                "is_internal": note.is_internal,
                "attachments": json.dumps(note.attachments or []),
                "user_id": current_user["id"]
            }
        )
        
        db.commit()
        
        return {"id": note_id, "message": "Note added successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding job note: {e}")
        raise HTTPException(status_code=500, detail="Failed to add note")

@router.get("/{job_id}/notes", response_model=dict)
async def get_job_notes(
    job_id: str,
    include_internal: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get all notes for a job"""
    try:
        query = """
            SELECT n.*, u.name as created_by_name
            FROM job_notes n
            LEFT JOIN users u ON n.created_by = u.id
            WHERE n.job_id = :job_id
        """
        
        if not include_internal:
            query += " AND n.is_internal = FALSE"
        
        query += " ORDER BY n.created_at DESC"
        
        result = db.execute(text(query), {"job_id": job_id})
        
        notes = []
        for row in result:
            note = dict(row._mapping)
            note["id"] = str(note["id"])
            note["job_id"] = str(note["job_id"])
            if note["created_by"]:
                note["created_by"] = str(note["created_by"])
            notes.append(note)
        
        return {"notes": notes, "count": len(notes)}
    
    except Exception as e:
        logger.error(f"Error fetching job notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notes")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_job_phase(status: str) -> str:
    """Get the lifecycle phase based on status"""
    phase_map = {
        JobStatus.DRAFT: "Planning",
        JobStatus.SCHEDULED: "Scheduled",
        JobStatus.IN_PROGRESS: "Execution",
        JobStatus.ON_HOLD: "Paused",
        JobStatus.COMPLETED: "Completion",
        JobStatus.CANCELLED: "Cancelled",
        JobStatus.INVOICED: "Closed"
    }
    return phase_map.get(status, "Unknown RETURNING * RETURNING *")
