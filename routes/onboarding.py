"""
Employee Onboarding Module - Task 45
Complete employee onboarding workflow and management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from enum import Enum
import asyncpg
import uuid
import json
from decimal import Decimal

router = APIRouter()

# Database connection
async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Enums
class OnboardingStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PAPERWORK_PENDING = "paperwork_pending"
    BACKGROUND_CHECK = "background_check"
    IT_SETUP = "it_setup"
    TRAINING = "training"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OnboardingStep(str, Enum):
    OFFER_ACCEPTED = "offer_accepted"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    BACKGROUND_CHECK = "background_check"
    I9_VERIFICATION = "i9_verification"
    TAX_FORMS = "tax_forms"
    BENEFITS_ENROLLMENT = "benefits_enrollment"
    IT_ACCOUNT_CREATION = "it_account_creation"
    EQUIPMENT_ASSIGNED = "equipment_assigned"
    WORKSPACE_SETUP = "workspace_setup"
    ORIENTATION_SCHEDULED = "orientation_scheduled"
    ORIENTATION_COMPLETED = "orientation_completed"
    TRAINING_SCHEDULED = "training_scheduled"
    TRAINING_COMPLETED = "training_completed"
    BUDDY_ASSIGNED = "buddy_assigned"
    FIRST_DAY_COMPLETE = "first_day_complete"
    FIRST_WEEK_COMPLETE = "first_week_complete"
    PROBATION_REVIEW = "probation_review"

class DocumentType(str, Enum):
    OFFER_LETTER = "offer_letter"
    CONTRACT = "contract"
    I9_FORM = "i9_form"
    W4_FORM = "w4_form"
    STATE_TAX_FORM = "state_tax_form"
    DIRECT_DEPOSIT = "direct_deposit"
    EMERGENCY_CONTACT = "emergency_contact"
    HANDBOOK_ACKNOWLEDGMENT = "handbook_acknowledgment"
    CONFIDENTIALITY_AGREEMENT = "confidentiality_agreement"
    BENEFITS_ENROLLMENT = "benefits_enrollment"
    PHOTO_ID = "photo_id"
    SSN_CARD = "ssn_card"
    WORK_AUTHORIZATION = "work_authorization"
    BACKGROUND_CHECK_CONSENT = "background_check_consent"
    DRUG_TEST_CONSENT = "drug_test_consent"

class EquipmentType(str, Enum):
    LAPTOP = "laptop"
    DESKTOP = "desktop"
    MONITOR = "monitor"
    PHONE = "phone"
    HEADSET = "headset"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    BADGE = "badge"
    KEYS = "keys"
    UNIFORM = "uniform"
    TOOLS = "tools"
    VEHICLE = "vehicle"
    SAFETY_EQUIPMENT = "safety_equipment"

# Pydantic Models
class OnboardingProcessBase(BaseModel):
    employee_id: str
    employee_name: str
    employee_email: EmailStr
    position: str
    department: str
    manager_id: str
    start_date: date
    orientation_date: Optional[date] = None
    buddy_id: Optional[str] = None
    hr_coordinator_id: Optional[str] = None
    it_coordinator_id: Optional[str] = None
    status: OnboardingStatus = OnboardingStatus.DRAFT
    notes: Optional[str] = None

class OnboardingProcessCreate(OnboardingProcessBase):
    salary: Optional[Decimal] = None
    office_location: Optional[str] = None

class OnboardingProcessUpdate(BaseModel):
    status: Optional[OnboardingStatus] = None
    orientation_date: Optional[date] = None
    buddy_id: Optional[str] = None
    notes: Optional[str] = None

class OnboardingProcessResponse(OnboardingProcessBase):
    id: str
    completed_steps: List[str]
    pending_steps: List[str]
    completion_percentage: int
    created_at: datetime
    updated_at: datetime

class OnboardingChecklistItem(BaseModel):
    step: OnboardingStep
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    completed: bool = False
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class OnboardingDocument(BaseModel):
    document_type: DocumentType
    filename: str
    uploaded_by: str
    uploaded_at: datetime
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None

class EquipmentAssignment(BaseModel):
    equipment_type: EquipmentType
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    assigned_date: date
    assigned_by: str
    condition: str = "new"
    notes: Optional[str] = None

class TrainingSchedule(BaseModel):
    training_name: str
    trainer: Optional[str] = None
    scheduled_date: date
    duration_hours: float
    location: Optional[str] = None
    completed: bool = False
    score: Optional[float] = None
    notes: Optional[str] = None

# CRUD Endpoints
@router.post("/process", response_model=OnboardingProcessResponse)
async def create_onboarding_process(
    process: OnboardingProcessCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new employee onboarding process"""
    query = """
        INSERT INTO employee_onboarding (
            employee_id, employee_name, employee_email, position,
            department, manager_id, start_date, orientation_date,
            buddy_id, hr_coordinator_id, it_coordinator_id,
            status, notes, salary, office_location
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        process.employee_id, process.employee_name, process.employee_email,
        process.position, process.department, process.manager_id,
        process.start_date, process.orientation_date, process.buddy_id,
        process.hr_coordinator_id, process.it_coordinator_id,
        process.status, process.notes,
        float(process.salary) if process.salary else None,
        process.office_location
    )

    # Create initial checklist
    await create_initial_checklist(conn, str(result['id']), process.employee_id)

    return {
        **process.dict(),
        "id": str(result['id']),
        "completed_steps": [],
        "pending_steps": [step.value for step in OnboardingStep],
        "completion_percentage": 0,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/process", response_model=List[OnboardingProcessResponse])
async def list_onboarding_processes(
    status: Optional[OnboardingStatus] = None,
    department: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all onboarding processes with filters"""
    query = """
        SELECT o.*,
               COUNT(DISTINCT c.step) FILTER (WHERE c.completed = true) as completed_steps_count,
               COUNT(DISTINCT c.step) as total_steps_count
        FROM employee_onboarding o
        LEFT JOIN onboarding_checklist c ON c.onboarding_id = o.id
        WHERE ($1::text IS NULL OR o.status = $1)
        AND ($2::text IS NULL OR o.department = $2)
        GROUP BY o.id
        ORDER BY o.start_date DESC
        LIMIT $3 OFFSET $4
    """

    rows = await conn.fetch(query, status, department, limit, skip)

    results = []
    for row in rows:
        completed = row['completed_steps_count'] or 0
        total = row['total_steps_count'] or len(OnboardingStep)

        results.append({
            "id": str(row['id']),
            "employee_id": row['employee_id'],
            "employee_name": row['employee_name'],
            "employee_email": row['employee_email'],
            "position": row['position'],
            "department": row['department'],
            "manager_id": row['manager_id'],
            "start_date": row['start_date'],
            "orientation_date": row['orientation_date'],
            "buddy_id": row['buddy_id'],
            "hr_coordinator_id": row['hr_coordinator_id'],
            "it_coordinator_id": row['it_coordinator_id'],
            "status": row['status'],
            "notes": row['notes'],
            "completed_steps": [],  # Would need another query to get actual steps
            "pending_steps": [],
            "completion_percentage": int((completed / total * 100)) if total > 0 else 0,
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        })

    return results

@router.get("/process/{process_id}", response_model=OnboardingProcessResponse)
async def get_onboarding_process(
    process_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific onboarding process details"""
    query = """
        SELECT * FROM employee_onboarding WHERE id = $1
    """

    row = await conn.fetchrow(query, uuid.UUID(process_id))
    if not row:
        raise HTTPException(status_code=404, detail="Onboarding process not found")

    # Get checklist status
    checklist_query = """
        SELECT step, completed FROM onboarding_checklist
        WHERE onboarding_id = $1
    """
    checklist_rows = await conn.fetch(checklist_query, uuid.UUID(process_id))

    completed_steps = [r['step'] for r in checklist_rows if r['completed']]
    pending_steps = [r['step'] for r in checklist_rows if not r['completed']]

    total_steps = len(checklist_rows) if checklist_rows else len(OnboardingStep)
    completed_count = len(completed_steps)

    return {
        "id": str(row['id']),
        "employee_id": row['employee_id'],
        "employee_name": row['employee_name'],
        "employee_email": row['employee_email'],
        "position": row['position'],
        "department": row['department'],
        "manager_id": row['manager_id'],
        "start_date": row['start_date'],
        "orientation_date": row['orientation_date'],
        "buddy_id": row['buddy_id'],
        "hr_coordinator_id": row['hr_coordinator_id'],
        "it_coordinator_id": row['it_coordinator_id'],
        "status": row['status'],
        "notes": row['notes'],
        "completed_steps": completed_steps,
        "pending_steps": pending_steps,
        "completion_percentage": int((completed_count / total_steps * 100)) if total_steps > 0 else 0,
        "created_at": row['created_at'],
        "updated_at": row['updated_at']
    }

@router.patch("/process/{process_id}", response_model=OnboardingProcessResponse)
async def update_onboarding_process(
    process_id: str,
    update: OnboardingProcessUpdate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update onboarding process"""
    updates = []
    values = []
    idx = 1

    for field, value in update.dict(exclude_unset=True).items():
        updates.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    values.append(uuid.UUID(process_id))
    query = f"""
        UPDATE employee_onboarding
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = ${idx}
        RETURNING *
    """

    row = await conn.fetchrow(query, *values)
    if not row:
        raise HTTPException(status_code=404, detail="Onboarding process not found")

    return await get_onboarding_process(process_id, conn)

@router.post("/process/{process_id}/checklist")
async def update_checklist_item(
    process_id: str,
    item: OnboardingChecklistItem,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update onboarding checklist item"""
    query = """
        INSERT INTO onboarding_checklist (
            onboarding_id, step, description, assigned_to,
            due_date, completed, completed_by, completed_at, notes
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (onboarding_id, step)
        DO UPDATE SET
            completed = $6,
            completed_by = $7,
            completed_at = $8,
            notes = $9,
            updated_at = NOW()
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(process_id), item.step, item.description,
        item.assigned_to, item.due_date, item.completed,
        item.completed_by, item.completed_at, item.notes
    )

    # Check if all steps are complete to update status
    await check_and_update_status(conn, process_id)

    return {"message": "Checklist item updated", "item": dict(result)}

@router.post("/process/{process_id}/documents")
async def upload_document(
    process_id: str,
    document: OnboardingDocument,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Record document upload for onboarding"""
    query = """
        INSERT INTO onboarding_documents (
            onboarding_id, document_type, filename, uploaded_by,
            uploaded_at, verified, verified_by, verified_at,
            expiry_date, notes
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(process_id), document.document_type, document.filename,
        document.uploaded_by, document.uploaded_at, document.verified,
        document.verified_by, document.verified_at,
        document.expiry_date, document.notes
    )

    return {"message": "Document recorded", "document_id": str(result['id'])}

@router.get("/process/{process_id}/documents")
async def list_documents(
    process_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all documents for an onboarding process"""
    query = """
        SELECT * FROM onboarding_documents
        WHERE onboarding_id = $1
        ORDER BY uploaded_at DESC
    """

    rows = await conn.fetch(query, uuid.UUID(process_id))

    return [dict(row) for row in rows]

@router.post("/process/{process_id}/equipment")
async def assign_equipment(
    process_id: str,
    equipment: EquipmentAssignment,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Assign equipment to new employee"""
    query = """
        INSERT INTO onboarding_equipment (
            onboarding_id, equipment_type, asset_tag, serial_number,
            model, assigned_date, assigned_by, condition, notes
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(process_id), equipment.equipment_type, equipment.asset_tag,
        equipment.serial_number, equipment.model, equipment.assigned_date,
        equipment.assigned_by, equipment.condition, equipment.notes
    )

    return {"message": "Equipment assigned", "assignment_id": str(result['id'])}

@router.post("/process/{process_id}/training")
async def schedule_training(
    process_id: str,
    training: TrainingSchedule,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Schedule training for new employee"""
    query = """
        INSERT INTO onboarding_training (
            onboarding_id, training_name, trainer, scheduled_date,
            duration_hours, location, completed, score, notes
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(process_id), training.training_name, training.trainer,
        training.scheduled_date, training.duration_hours, training.location,
        training.completed, training.score, training.notes
    )

    return {"message": "Training scheduled", "training_id": str(result['id'])}

@router.get("/dashboard/stats")
async def get_onboarding_stats(
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get onboarding dashboard statistics"""
    query = """
        SELECT
            COUNT(*) FILTER (WHERE status = 'in_progress') as active_onboardings,
            COUNT(*) FILTER (WHERE status = 'completed' AND
                updated_at > NOW() - INTERVAL '30 days') as completed_this_month,
            COUNT(*) FILTER (WHERE start_date > NOW() AND
                start_date < NOW() + INTERVAL '30 days') as starting_soon,
            COUNT(*) FILTER (WHERE status = 'paperwork_pending') as paperwork_pending,
            AVG(EXTRACT(day FROM (
                CASE
                    WHEN status = 'completed' THEN updated_at
                    ELSE NOW()
                END - created_at
            ))) as avg_onboarding_days
        FROM employee_onboarding
        WHERE created_at > NOW() - INTERVAL '90 days'
    """

    result = await conn.fetchrow(query)

    return {
        "active_onboardings": result['active_onboardings'] or 0,
        "completed_this_month": result['completed_this_month'] or 0,
        "starting_soon": result['starting_soon'] or 0,
        "paperwork_pending": result['paperwork_pending'] or 0,
        "avg_onboarding_days": round(result['avg_onboarding_days'] or 0, 1)
    }

@router.post("/process/{process_id}/complete-step/{step}")
async def complete_onboarding_step(
    process_id: str,
    step: OnboardingStep,
    completed_by: str = Query(..., description="User completing the step"),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Mark an onboarding step as complete"""
    query = """
        UPDATE onboarding_checklist
        SET completed = true,
            completed_by = $1,
            completed_at = NOW(),
            updated_at = NOW()
        WHERE onboarding_id = $2 AND step = $3
        RETURNING *
    """

    result = await conn.fetchrow(
        query, completed_by, uuid.UUID(process_id), step
    )

    if not result:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    # Check if all steps are complete
    await check_and_update_status(conn, process_id)

    return {"message": f"Step {step} marked as complete"}

# Helper Functions
async def create_initial_checklist(conn: asyncpg.Connection, onboarding_id: str, employee_id: str):
    """Create initial onboarding checklist"""
    checklist_items = [
        (OnboardingStep.OFFER_ACCEPTED, "Offer letter signed and accepted", 0),
        (OnboardingStep.DOCUMENTS_SUBMITTED, "All required documents submitted", 2),
        (OnboardingStep.BACKGROUND_CHECK, "Background check completed", 5),
        (OnboardingStep.I9_VERIFICATION, "I-9 employment verification", 1),
        (OnboardingStep.TAX_FORMS, "W-4 and state tax forms completed", 1),
        (OnboardingStep.BENEFITS_ENROLLMENT, "Benefits enrollment completed", 3),
        (OnboardingStep.IT_ACCOUNT_CREATION, "IT accounts and email created", 2),
        (OnboardingStep.EQUIPMENT_ASSIGNED, "Equipment assigned and configured", 3),
        (OnboardingStep.WORKSPACE_SETUP, "Workspace prepared", 1),
        (OnboardingStep.ORIENTATION_SCHEDULED, "Orientation scheduled", 1),
        (OnboardingStep.ORIENTATION_COMPLETED, "Orientation completed", 7),
        (OnboardingStep.TRAINING_SCHEDULED, "Training schedule created", 2),
        (OnboardingStep.TRAINING_COMPLETED, "Initial training completed", 14),
        (OnboardingStep.BUDDY_ASSIGNED, "Buddy/mentor assigned", 1),
        (OnboardingStep.FIRST_DAY_COMPLETE, "First day activities complete", 1),
        (OnboardingStep.FIRST_WEEK_COMPLETE, "First week check-in complete", 7),
        (OnboardingStep.PROBATION_REVIEW, "Probation period review", 90),
    ]

    for step, description, days_from_start in checklist_items:
        query = """
            INSERT INTO onboarding_checklist (
                onboarding_id, step, description, due_date, completed
            ) VALUES ($1, $2, $3, CURRENT_DATE + INTERVAL '%s days', false)
        """ % days_from_start

        await conn.execute(
            query,
            uuid.UUID(onboarding_id), step.value, description
        )

async def check_and_update_status(conn: asyncpg.Connection, process_id: str):
    """Check checklist completion and update onboarding status"""
    query = """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE completed = true) as completed
        FROM onboarding_checklist
        WHERE onboarding_id = $1
    """

    result = await conn.fetchrow(query, uuid.UUID(process_id))

    if result['total'] > 0 and result['completed'] == result['total']:
        # All steps completed
        update_query = """
            UPDATE employee_onboarding
            SET status = 'completed', updated_at = NOW()
            WHERE id = $1
        """
        await conn.execute(update_query, uuid.UUID(process_id))
    elif result['completed'] > 0:
        # Some steps completed
        update_query = """
            UPDATE employee_onboarding
            SET status = 'in_progress', updated_at = NOW()
            WHERE id = $1 AND status = 'draft'
        """
        await conn.execute(update_query, uuid.UUID(process_id))

@router.get("/upcoming-tasks")
async def get_upcoming_tasks(
    days_ahead: int = Query(7, description="Days to look ahead"),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get upcoming onboarding tasks"""
    query = """
        SELECT
            c.*,
            o.employee_name,
            o.position
        FROM onboarding_checklist c
        JOIN employee_onboarding o ON o.id = c.onboarding_id
        WHERE c.completed = false
        AND c.due_date BETWEEN NOW() AND NOW() + INTERVAL '%s days'
        ORDER BY c.due_date, o.employee_name
    """ % days_ahead

    rows = await conn.fetch(query)

    return [
        {
            "onboarding_id": str(row['onboarding_id']),
            "employee_name": row['employee_name'],
            "position": row['position'],
            "step": row['step'],
            "description": row['description'],
            "due_date": row['due_date'],
            "assigned_to": row['assigned_to']
        }
        for row in rows
    ]