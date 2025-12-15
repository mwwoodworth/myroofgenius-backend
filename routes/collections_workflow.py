"""
Collections Workflow Module
Task 37: Collections workflow implementation

Automated collections management with escalation levels,
agency integration, and recovery tracking.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import json
import uuid
import asyncpg
import os
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

router = APIRouter()

# ==================== Enums ====================

class CollectionStage(str, Enum):
    SOFT_REMINDER = "soft_reminder"      # 1-30 days overdue
    FIRM_REMINDER = "firm_reminder"      # 31-60 days
    FINAL_NOTICE = "final_notice"        # 61-90 days
    PRE_LEGAL = "pre_legal"              # 90-120 days
    LEGAL_ACTION = "legal_action"        # 120+ days
    EXTERNAL_AGENCY = "external_agency"  # Sent to collection agency
    WRITE_OFF = "write_off"              # Bad debt write-off
    RECOVERED = "recovered"               # Successfully collected

class CollectionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PROMISE_TO_PAY = "promise_to_pay"
    PAYMENT_PLAN = "payment_plan"
    DISPUTED = "disputed"
    LEGAL_PROCEEDINGS = "legal_proceedings"
    AGENCY_ASSIGNED = "agency_assigned"
    SETTLED = "settled"
    CLOSED = "closed"
    WRITTEN_OFF = "written_off"

class ContactMethod(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    LETTER = "letter"
    IN_PERSON = "in_person"
    LEGAL_NOTICE = "legal_notice"

class ContactResult(str, Enum):
    NO_ANSWER = "no_answer"
    LEFT_MESSAGE = "left_message"
    SPOKE_TO_CUSTOMER = "spoke_to_customer"
    PROMISED_PAYMENT = "promised_payment"
    REFUSED_PAYMENT = "refused_payment"
    DISPUTED = "disputed"
    REQUESTED_DOCUMENTS = "requested_documents"
    BANKRUPTCY = "bankruptcy"
    DECEASED = "deceased"

# ==================== Pydantic Models ====================

class CreateCollectionCase(BaseModel):
    """Create a new collection case"""
    customer_id: str = Field(description="Customer ID")
    invoice_ids: List[str] = Field(description="List of overdue invoice IDs")
    total_amount: float = Field(gt=0, description="Total amount to collect")
    initial_stage: CollectionStage = Field(default=CollectionStage.SOFT_REMINDER)
    assigned_to: Optional[str] = Field(default=None, description="Collector/agent ID")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10")
    notes: Optional[str] = None

class CollectionContact(BaseModel):
    """Record a collection contact attempt"""
    case_id: str
    contact_method: ContactMethod
    contact_result: ContactResult
    spoke_with: Optional[str] = Field(default=None, description="Person contacted")
    promise_date: Optional[date] = Field(default=None, description="Payment promise date")
    promise_amount: Optional[float] = Field(default=None, gt=0)
    notes: str = Field(description="Contact notes")
    follow_up_date: Optional[date] = None

class PaymentArrangement(BaseModel):
    """Setup payment arrangement"""
    case_id: str
    arrangement_type: str = Field(description="settlement, payment_plan, partial")
    total_amount: float = Field(gt=0, description="Total arrangement amount")
    down_payment: Optional[float] = Field(default=0, ge=0)
    installments: Optional[int] = Field(default=1, ge=1)
    frequency: Optional[str] = Field(default="monthly", description="weekly, biweekly, monthly")
    start_date: date
    notes: Optional[str] = None
    approved_by: Optional[str] = None

class EscalateCase(BaseModel):
    """Escalate collection case"""
    case_id: str
    new_stage: CollectionStage
    reason: str
    skip_stages: bool = Field(default=False, description="Skip intermediate stages")
    notes: Optional[str] = None

class CollectionAgency(BaseModel):
    """Collection agency information"""
    agency_name: str
    contact_person: str
    phone: str
    email: EmailStr
    address: str
    commission_rate: float = Field(ge=0, le=100, description="Commission percentage")
    specialties: List[str] = Field(default=[], description="Industry specialties")
    success_rate: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: bool = Field(default=True)

class AssignToAgency(BaseModel):
    """Assign case to collection agency"""
    case_id: str
    agency_id: str
    placement_amount: float = Field(gt=0)
    commission_rate: float = Field(ge=0, le=100)
    documentation: Optional[List[str]] = Field(default=[], description="Document IDs")
    special_instructions: Optional[str] = None

class DisputeResolution(BaseModel):
    """Resolve a disputed collection"""
    case_id: str
    resolution_type: str = Field(description="valid_debt, invalid_debt, partial_valid, documentation_provided")
    adjusted_amount: Optional[float] = Field(default=None, ge=0)
    resolution_notes: str
    supporting_documents: Optional[List[str]] = None
    resolved_by: Optional[str] = None

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Collection Cases ====================

@router.post("/cases/create", tags=["Collections Workflow"])
async def create_collection_case(
    case: CreateCollectionCase,
    background_tasks: BackgroundTasks
):
    """Create a new collection case"""
    try:
        conn = await get_db_connection()
        try:
            # Verify customer
            customer = await conn.fetchrow("""
                SELECT * FROM customers WHERE id = $1
            """, uuid.UUID(case.customer_id))
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Verify invoices
            invoice_uuids = [uuid.UUID(inv_id) for inv_id in case.invoice_ids]
            invoices = await conn.fetch("""
                SELECT id, invoice_number, balance_cents
                FROM invoices
                WHERE id = ANY($1::uuid[])
                    AND customer_id = $2
                    AND status IN ('overdue', 'partial')
            """, invoice_uuids, uuid.UUID(case.customer_id))
            
            if len(invoices) != len(case.invoice_ids):
                raise HTTPException(status_code=400, detail="Some invoices not found or not overdue")
            
            # Create collection case
            case_id = str(uuid.uuid4())
            case_number = f"COL-{datetime.now().strftime('%Y%m%d')}-{case_id[:8].upper()}"
            
            await conn.execute("""
                INSERT INTO collection_cases (
                    id, case_number, customer_id, total_amount,
                    outstanding_amount, stage, status, priority,
                    assigned_to, created_at, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), $10)
            """, uuid.UUID(case_id), case_number,
                uuid.UUID(case.customer_id), case.total_amount,
                case.total_amount, case.initial_stage.value,
                CollectionStatus.PENDING.value, case.priority,
                case.assigned_to, case.notes)
            
            # Link invoices to case
            for invoice in invoices:
                await conn.execute("""
                    INSERT INTO collection_case_invoices (
                        case_id, invoice_id, amount
                    ) VALUES ($1, $2, $3)
                """, uuid.UUID(case_id), invoice['id'],
                    invoice['balance_cents'] / 100.0)
            
            # Create first action
            await conn.execute("""
                INSERT INTO collection_actions (
                    case_id, action_type, action_date,
                    description, created_by
                ) VALUES ($1, 'case_created', NOW(), $2, $3)
            """, uuid.UUID(case_id),
                f"Collection case created for ${case.total_amount:.2f}",
                case.assigned_to)
            
            # Schedule first contact
            background_tasks.add_task(
                schedule_collection_contact,
                case_id,
                case.initial_stage.value
            )
            
            return {
                "success": True,
                "case_id": case_id,
                "case_number": case_number,
                "message": f"Collection case {case_number} created",
                "total_amount": case.total_amount,
                "invoice_count": len(invoices)
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collection case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/list", tags=["Collections Workflow"])
async def list_collection_cases(
    status: Optional[CollectionStatus] = None,
    stage: Optional[CollectionStage] = None,
    assigned_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    days_overdue_min: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List collection cases with filters"""
    try:
        conn = await get_db_connection()
        try:
            query = """
                SELECT 
                    cc.*,
                    c.customer_name,
                    c.email,
                    c.phone,
                    COUNT(DISTINCT cci.invoice_id) as invoice_count,
                    MIN(i.due_date) as oldest_due_date,
                    CURRENT_DATE - MIN(i.due_date) as max_days_overdue
                FROM collection_cases cc
                JOIN customers c ON cc.customer_id = c.id
                LEFT JOIN collection_case_invoices cci ON cc.id = cci.case_id
                LEFT JOIN invoices i ON cci.invoice_id = i.id
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                query += f" AND cc.status = ${param_count}"
                params.append(status.value)
            
            if stage:
                param_count += 1
                query += f" AND cc.stage = ${param_count}"
                params.append(stage.value)
            
            if assigned_to:
                param_count += 1
                query += f" AND cc.assigned_to = ${param_count}"
                params.append(assigned_to)
            
            if min_amount:
                param_count += 1
                query += f" AND cc.outstanding_amount >= ${param_count}"
                params.append(min_amount)
            
            if days_overdue_min:
                param_count += 1
                query += f" AND CURRENT_DATE - MIN(i.due_date) >= ${param_count}"
                params.append(days_overdue_min)
            
            query += f"""
                GROUP BY cc.id, c.customer_name, c.email, c.phone
                ORDER BY cc.priority DESC, cc.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            cases = await conn.fetch(query, *params)
            
            return {
                "cases": [
                    {
                        "case_id": str(case['id']),
                        "case_number": case['case_number'],
                        "customer_id": str(case['customer_id']),
                        "customer_name": case['customer_name'],
                        "email": case['email'],
                        "phone": case['phone'],
                        "total_amount": float(case['total_amount']),
                        "outstanding_amount": float(case['outstanding_amount']),
                        "stage": case['stage'],
                        "status": case['status'],
                        "priority": case['priority'],
                        "assigned_to": case['assigned_to'],
                        "invoice_count": case['invoice_count'],
                        "max_days_overdue": case['max_days_overdue'],
                        "created_at": case['created_at'].isoformat() if case['created_at'] else None
                    }
                    for case in cases
                ],
                "total": len(cases),
                "limit": limit,
                "offset": offset
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error listing collection cases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/{case_id}", tags=["Collections Workflow"])
async def get_collection_case(case_id: str):
    """Get collection case details"""
    try:
        conn = await get_db_connection()
        try:
            # Get case details
            case = await conn.fetchrow("""
                SELECT cc.*, c.customer_name, c.email, c.phone
                FROM collection_cases cc
                JOIN customers c ON cc.customer_id = c.id
                WHERE cc.id = $1
            """, uuid.UUID(case_id))
            
            if not case:
                raise HTTPException(status_code=404, detail="Collection case not found")
            
            # Get invoices
            invoices = await conn.fetch("""
                SELECT i.*, cci.amount as case_amount
                FROM collection_case_invoices cci
                JOIN invoices i ON cci.invoice_id = i.id
                WHERE cci.case_id = $1
            """, uuid.UUID(case_id))
            
            # Get contact history
            contacts = await conn.fetch("""
                SELECT * FROM collection_contacts
                WHERE case_id = $1
                ORDER BY contact_date DESC
                LIMIT 10
            """, uuid.UUID(case_id))
            
            # Get payment history
            payments = await conn.fetch("""
                SELECT p.*, i.invoice_number
                FROM collection_payments cp
                JOIN invoice_payments p ON cp.payment_id = p.id
                JOIN invoices i ON p.invoice_id = i.id
                WHERE cp.case_id = $1
                ORDER BY p.payment_date DESC
            """, uuid.UUID(case_id))
            
            # Get actions/notes
            actions = await conn.fetch("""
                SELECT * FROM collection_actions
                WHERE case_id = $1
                ORDER BY action_date DESC
                LIMIT 20
            """, uuid.UUID(case_id))
            
            return {
                "case_id": str(case['id']),
                "case_number": case['case_number'],
                "customer": {
                    "id": str(case['customer_id']),
                    "name": case['customer_name'],
                    "email": case['email'],
                    "phone": case['phone']
                },
                "amounts": {
                    "total": float(case['total_amount']),
                    "outstanding": float(case['outstanding_amount']),
                    "collected": float(case['total_amount'] - case['outstanding_amount'])
                },
                "stage": case['stage'],
                "status": case['status'],
                "priority": case['priority'],
                "assigned_to": case['assigned_to'],
                "invoices": [
                    {
                        "invoice_id": str(inv['id']),
                        "invoice_number": inv['invoice_number'],
                        "due_date": inv['due_date'].isoformat() if inv['due_date'] else None,
                        "amount": float(inv['case_amount']),
                        "balance": float(inv['balance_cents'] / 100)
                    }
                    for inv in invoices
                ],
                "contact_history": [
                    {
                        "contact_date": cont['contact_date'].isoformat() if cont['contact_date'] else None,
                        "method": cont['contact_method'],
                        "result": cont['contact_result'],
                        "notes": cont['notes']
                    }
                    for cont in contacts
                ],
                "payment_history": [
                    {
                        "payment_date": pay['payment_date'].isoformat() if pay['payment_date'] else None,
                        "amount": float(pay['amount']),
                        "invoice_number": pay['invoice_number']
                    }
                    for pay in payments
                ],
                "actions": [
                    {
                        "date": act['action_date'].isoformat() if act['action_date'] else None,
                        "type": act['action_type'],
                        "description": act['description']
                    }
                    for act in actions
                ],
                "created_at": case['created_at'].isoformat() if case['created_at'] else None,
                "updated_at": case['updated_at'].isoformat() if case['updated_at'] else None
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Contact Management ====================

@router.post("/contact", tags=["Collections Workflow"])
async def record_collection_contact(
    contact: CollectionContact,
    background_tasks: BackgroundTasks
):
    """Record a collection contact attempt"""
    try:
        conn = await get_db_connection()
        try:
            # Verify case exists
            case = await conn.fetchrow("""
                SELECT * FROM collection_cases WHERE id = $1
            """, uuid.UUID(contact.case_id))
            
            if not case:
                raise HTTPException(status_code=404, detail="Collection case not found")
            
            # Record contact
            contact_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO collection_contacts (
                    id, case_id, contact_date, contact_method,
                    contact_result, spoke_with, promise_date,
                    promise_amount, notes, follow_up_date
                ) VALUES ($1, $2, NOW(), $3, $4, $5, $6, $7, $8, $9)
            """, uuid.UUID(contact_id), uuid.UUID(contact.case_id),
                contact.contact_method.value, contact.contact_result.value,
                contact.spoke_with, contact.promise_date,
                contact.promise_amount, contact.notes, contact.follow_up_date)
            
            # Update case if promise made
            if contact.contact_result == ContactResult.PROMISED_PAYMENT:
                await conn.execute("""
                    UPDATE collection_cases
                    SET status = 'promise_to_pay',
                        last_contact_date = NOW(),
                        next_action_date = $2,
                        updated_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(contact.case_id), contact.promise_date)
                
                # Schedule follow-up
                if contact.promise_date:
                    background_tasks.add_task(
                        schedule_promise_followup,
                        contact.case_id,
                        contact.promise_date
                    )
            
            # Log action
            await conn.execute("""
                INSERT INTO collection_actions (
                    case_id, action_type, action_date, description
                ) VALUES ($1, $2, NOW(), $3)
            """, uuid.UUID(contact.case_id), 'contact_made',
                f"{contact.contact_method.value}: {contact.contact_result.value}")
            
            return {
                "success": True,
                "contact_id": contact_id,
                "message": "Contact recorded successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Payment Arrangements ====================

@router.post("/arrangement", tags=["Collections Workflow"])
async def create_payment_arrangement(
    arrangement: PaymentArrangement,
    background_tasks: BackgroundTasks
):
    """Create payment arrangement for collection case"""
    try:
        conn = await get_db_connection()
        try:
            # Verify case
            case = await conn.fetchrow("""
                SELECT * FROM collection_cases WHERE id = $1
            """, uuid.UUID(arrangement.case_id))
            
            if not case:
                raise HTTPException(status_code=404, detail="Collection case not found")
            
            # Create arrangement
            arrangement_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO payment_arrangements (
                    id, case_id, arrangement_type, total_amount,
                    down_payment, installments, frequency,
                    start_date, status, notes, approved_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', $9, $10)
            """, uuid.UUID(arrangement_id), uuid.UUID(arrangement.case_id),
                arrangement.arrangement_type, arrangement.total_amount,
                arrangement.down_payment, arrangement.installments,
                arrangement.frequency, arrangement.start_date,
                arrangement.notes, arrangement.approved_by)
            
            # Update case status
            await conn.execute("""
                UPDATE collection_cases
                SET status = 'payment_plan',
                    updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(arrangement.case_id))
            
            # Generate installment schedule
            if arrangement.installments and arrangement.installments > 1:
                installment_amount = (
                    arrangement.total_amount - (arrangement.down_payment or 0)
                ) / arrangement.installments
                
                current_date = arrangement.start_date
                for i in range(arrangement.installments):
                    await conn.execute("""
                        INSERT INTO arrangement_installments (
                            arrangement_id, installment_number,
                            due_date, amount, status
                        ) VALUES ($1, $2, $3, $4, 'pending')
                    """, uuid.UUID(arrangement_id), i + 1,
                        current_date, installment_amount)
                    
                    # Calculate next date
                    if arrangement.frequency == 'weekly':
                        current_date += timedelta(weeks=1)
                    elif arrangement.frequency == 'biweekly':
                        current_date += timedelta(weeks=2)
                    else:  # monthly
                        current_date += timedelta(days=30)
            
            # Log action
            await conn.execute("""
                INSERT INTO collection_actions (
                    case_id, action_type, action_date, description
                ) VALUES ($1, 'arrangement_created', NOW(), $2)
            """, uuid.UUID(arrangement.case_id),
                f"{arrangement.arrangement_type}: ${arrangement.total_amount:.2f}")
            
            return {
                "success": True,
                "arrangement_id": arrangement_id,
                "message": "Payment arrangement created successfully",
                "total_amount": arrangement.total_amount,
                "installments": arrangement.installments
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating arrangement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Escalation ====================

@router.post("/escalate", tags=["Collections Workflow"])
async def escalate_collection_case(
    escalation: EscalateCase,
    background_tasks: BackgroundTasks
):
    """Escalate collection case to next stage"""
    try:
        conn = await get_db_connection()
        try:
            # Get current case
            case = await conn.fetchrow("""
                SELECT * FROM collection_cases WHERE id = $1
            """, uuid.UUID(escalation.case_id))
            
            if not case:
                raise HTTPException(status_code=404, detail="Collection case not found")
            
            # Update case stage
            await conn.execute("""
                UPDATE collection_cases
                SET stage = $2,
                    escalation_date = NOW(),
                    updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(escalation.case_id), escalation.new_stage.value)
            
            # Log escalation
            await conn.execute("""
                INSERT INTO collection_escalations (
                    case_id, from_stage, to_stage,
                    escalation_date, reason, notes
                ) VALUES ($1, $2, $3, NOW(), $4, $5)
            """, uuid.UUID(escalation.case_id), case['stage'],
                escalation.new_stage.value, escalation.reason,
                escalation.notes)
            
            # Log action
            await conn.execute("""
                INSERT INTO collection_actions (
                    case_id, action_type, action_date, description
                ) VALUES ($1, 'escalated', NOW(), $2)
            """, uuid.UUID(escalation.case_id),
                f"Escalated to {escalation.new_stage.value}: {escalation.reason}")
            
            # Trigger stage-specific actions
            if escalation.new_stage == CollectionStage.LEGAL_ACTION:
                background_tasks.add_task(
                    prepare_legal_documentation,
                    escalation.case_id
                )
            elif escalation.new_stage == CollectionStage.EXTERNAL_AGENCY:
                background_tasks.add_task(
                    prepare_agency_placement,
                    escalation.case_id
                )
            
            return {
                "success": True,
                "case_id": escalation.case_id,
                "new_stage": escalation.new_stage.value,
                "message": f"Case escalated to {escalation.new_stage.value}"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Agency Management ====================

@router.post("/agencies", tags=["Collections Workflow"])
async def create_collection_agency(agency: CollectionAgency):
    """Register a collection agency"""
    try:
        conn = await get_db_connection()
        try:
            agency_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO collection_agencies (
                    id, agency_name, contact_person, phone, email,
                    address, commission_rate, specialties,
                    success_rate, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, uuid.UUID(agency_id), agency.agency_name,
                agency.contact_person, agency.phone, agency.email,
                agency.address, agency.commission_rate,
                json.dumps(agency.specialties), agency.success_rate,
                agency.is_active)
            
            return {
                "success": True,
                "agency_id": agency_id,
                "message": f"Agency {agency.agency_name} registered successfully"
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating agency: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assign-agency", tags=["Collections Workflow"])
async def assign_to_collection_agency(
    assignment: AssignToAgency,
    background_tasks: BackgroundTasks
):
    """Assign case to external collection agency"""
    try:
        conn = await get_db_connection()
        try:
            # Verify case and agency
            case = await conn.fetchrow("""
                SELECT * FROM collection_cases WHERE id = $1
            """, uuid.UUID(assignment.case_id))
            
            if not case:
                raise HTTPException(status_code=404, detail="Collection case not found")
            
            agency = await conn.fetchrow("""
                SELECT * FROM collection_agencies WHERE id = $1 AND is_active = true
            """, uuid.UUID(assignment.agency_id))
            
            if not agency:
                raise HTTPException(status_code=404, detail="Collection agency not found or inactive")
            
            # Create agency placement
            placement_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO agency_placements (
                    id, case_id, agency_id, placement_date,
                    placement_amount, commission_rate,
                    status, special_instructions
                ) VALUES ($1, $2, $3, NOW(), $4, $5, 'active', $6)
            """, uuid.UUID(placement_id), uuid.UUID(assignment.case_id),
                uuid.UUID(assignment.agency_id), assignment.placement_amount,
                assignment.commission_rate, assignment.special_instructions)
            
            # Update case
            await conn.execute("""
                UPDATE collection_cases
                SET stage = 'external_agency',
                    status = 'agency_assigned',
                    agency_id = $2,
                    updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(assignment.case_id), uuid.UUID(assignment.agency_id))
            
            # Log action
            await conn.execute("""
                INSERT INTO collection_actions (
                    case_id, action_type, action_date, description
                ) VALUES ($1, 'agency_assigned', NOW(), $2)
            """, uuid.UUID(assignment.case_id),
                f"Assigned to {agency['agency_name']} - Amount: ${assignment.placement_amount:.2f}")
            
            # Send placement notification
            background_tasks.add_task(
                notify_agency_placement,
                placement_id,
                agency['email']
            )
            
            return {
                "success": True,
                "placement_id": placement_id,
                "agency_name": agency['agency_name'],
                "message": "Case assigned to collection agency successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning to agency: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Reporting ====================

@router.get("/reports/summary", tags=["Collections Workflow"])
async def get_collections_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """Get collections performance summary"""
    try:
        conn = await get_db_connection()
        try:
            # Date range
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Overall statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_cases,
                    COUNT(CASE WHEN status = 'recovered' THEN 1 END) as recovered_cases,
                    COUNT(CASE WHEN status = 'written_off' THEN 1 END) as written_off_cases,
                    SUM(total_amount) as total_amount,
                    SUM(total_amount - outstanding_amount) as collected_amount,
                    SUM(CASE WHEN status = 'recovered' THEN total_amount ELSE 0 END) as recovered_amount,
                    AVG(CASE WHEN status = 'recovered' THEN 
                        EXTRACT(DAY FROM recovery_date - created_at) END) as avg_days_to_collect
                FROM collection_cases
                WHERE created_at BETWEEN $1 AND $2
            """, start_date, end_date)
            
            # By stage breakdown
            by_stage = await conn.fetch("""
                SELECT 
                    stage,
                    COUNT(*) as count,
                    SUM(outstanding_amount) as amount
                FROM collection_cases
                WHERE status NOT IN ('recovered', 'written_off', 'closed')
                GROUP BY stage
                ORDER BY 
                    CASE stage
                        WHEN 'soft_reminder' THEN 1
                        WHEN 'firm_reminder' THEN 2
                        WHEN 'final_notice' THEN 3
                        WHEN 'pre_legal' THEN 4
                        WHEN 'legal_action' THEN 5
                        WHEN 'external_agency' THEN 6
                        ELSE 7
                    END
            """)
            
            # Collector performance
            collector_stats = await conn.fetch("""
                SELECT 
                    assigned_to,
                    COUNT(*) as total_cases,
                    COUNT(CASE WHEN status = 'recovered' THEN 1 END) as recovered,
                    SUM(total_amount - outstanding_amount) as collected
                FROM collection_cases
                WHERE assigned_to IS NOT NULL
                    AND created_at BETWEEN $1 AND $2
                GROUP BY assigned_to
                ORDER BY collected DESC
                LIMIT 10
            """, start_date, end_date)
            
            recovery_rate = 0
            if stats['total_cases'] > 0:
                recovery_rate = (stats['recovered_cases'] / stats['total_cases']) * 100
            
            collection_rate = 0
            if stats['total_amount'] and stats['total_amount'] > 0:
                collection_rate = (stats['collected_amount'] / stats['total_amount']) * 100
            
            return {
                "period": f"{start_date} to {end_date}",
                "summary": {
                    "total_cases": stats['total_cases'] or 0,
                    "recovered_cases": stats['recovered_cases'] or 0,
                    "written_off_cases": stats['written_off_cases'] or 0,
                    "recovery_rate": recovery_rate,
                    "total_amount": float(stats['total_amount']) if stats['total_amount'] else 0,
                    "collected_amount": float(stats['collected_amount']) if stats['collected_amount'] else 0,
                    "collection_rate": collection_rate,
                    "avg_days_to_collect": int(stats['avg_days_to_collect']) if stats['avg_days_to_collect'] else 0
                },
                "by_stage": [
                    {
                        "stage": stage['stage'],
                        "count": stage['count'],
                        "amount": float(stage['amount']) if stage['amount'] else 0
                    }
                    for stage in by_stage
                ],
                "top_collectors": [
                    {
                        "collector": coll['assigned_to'],
                        "total_cases": coll['total_cases'],
                        "recovered": coll['recovered'],
                        "amount_collected": float(coll['collected']) if coll['collected'] else 0
                    }
                    for coll in collector_stats
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Helper Functions ====================

async def schedule_collection_contact(case_id: str, stage: str):
    """Schedule collection contact based on stage"""
    logger.info(f"Scheduling contact for case {case_id} at stage {stage}")
    # Implementation would integrate with scheduling system

async def schedule_promise_followup(case_id: str, promise_date: date):
    """Schedule follow-up for payment promise"""
    logger.info(f"Scheduling promise follow-up for case {case_id} on {promise_date}")
    # Implementation would integrate with scheduling system

async def prepare_legal_documentation(case_id: str):
    """Prepare documentation for legal action"""
    logger.info(f"Preparing legal documentation for case {case_id}")
    # Implementation would generate legal documents

async def prepare_agency_placement(case_id: str):
    """Prepare case for agency placement"""
    logger.info(f"Preparing agency placement for case {case_id}")
    # Implementation would compile case documentation

async def notify_agency_placement(placement_id: str, agency_email: str):
    """Notify agency of new placement"""
    logger.info(f"Notifying agency at {agency_email} of placement {placement_id} RETURNING * RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *")
    # Implementation would send email notification