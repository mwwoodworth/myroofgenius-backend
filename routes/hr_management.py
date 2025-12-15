"""
HR Management Module - Task 43
Comprehensive human resources management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, time, timedelta
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
class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RETIRED = "retired"
    SUSPENDED = "suspended"

class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    TEMPORARY = "temporary"
    SEASONAL = "seasonal"

class Department(str, Enum):
    SALES = "sales"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HR = "hr"
    IT = "it"
    MARKETING = "marketing"
    CUSTOMER_SERVICE = "customer_service"
    WAREHOUSE = "warehouse"
    FIELD_SERVICE = "field_service"
    MANAGEMENT = "management"

class LeaveType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    BEREAVEMENT = "bereavement"
    JURY_DUTY = "jury_duty"
    MILITARY = "military"
    UNPAID = "unpaid"
    SABBATICAL = "sabbatical"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class BenefitType(str, Enum):
    HEALTH = "health"
    DENTAL = "dental"
    VISION = "vision"
    LIFE = "life"
    DISABILITY = "disability"
    RETIREMENT_401K = "401k"
    FSA = "fsa"
    HSA = "hsa"
    COMMUTER = "commuter"
    OTHER = "other"

class TrainingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReviewType(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    PROBATION = "probation"
    PROMOTION = "promotion"
    IMPROVEMENT = "improvement"
    EXIT = "exit"

# Pydantic Models
class EmployeeBase(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Department
    position: str
    employment_type: EmploymentType
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    hire_date: date
    birth_date: Optional[date] = None
    ssn_last4: Optional[str] = Field(None, max_length=4)
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    manager_id: Optional[str] = None
    salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[Department] = None
    position: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    manager_id: Optional[str] = None
    address: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PayrollBase(BaseModel):
    employee_id: str
    pay_period_start: date
    pay_period_end: date
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    holiday_hours: Decimal = Decimal("0")
    sick_hours: Decimal = Decimal("0")
    vacation_hours: Decimal = Decimal("0")
    gross_pay: Decimal
    deductions: Dict[str, Decimal] = {}
    net_pay: Decimal
    payment_method: str = "direct_deposit"
    payment_date: date

class PayrollCreate(PayrollBase):
    pass

class PayrollResponse(PayrollBase):
    id: str
    payroll_number: str
    status: str
    approved_by: Optional[str] = None
    created_at: datetime

class LeaveRequestBase(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None
    supporting_docs: Optional[List[str]] = []

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestUpdate(BaseModel):
    status: LeaveStatus
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None

class LeaveRequestResponse(LeaveRequestBase):
    id: str
    request_number: str
    status: LeaveStatus
    total_days: int
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    created_at: datetime

class BenefitEnrollment(BaseModel):
    employee_id: str
    benefit_type: BenefitType
    plan_name: str
    coverage_level: str  # self, spouse, family
    effective_date: date
    termination_date: Optional[date] = None
    employee_cost: Decimal
    employer_cost: Decimal
    dependents: Optional[List[Dict]] = []

class TimeEntry(BaseModel):
    employee_id: str
    work_date: date
    clock_in: time
    clock_out: Optional[time] = None
    break_minutes: int = 0
    project_id: Optional[str] = None
    notes: Optional[str] = None

class PerformanceReview(BaseModel):
    employee_id: str
    reviewer_id: str
    review_type: ReviewType
    review_period_start: date
    review_period_end: date
    overall_rating: int = Field(..., ge=1, le=5)
    ratings: Dict[str, int] = {}  # category -> rating
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    goals: Optional[List[str]] = []
    comments: Optional[str] = None

class TrainingRecord(BaseModel):
    employee_id: str
    training_name: str
    training_type: str  # online, classroom, on_the_job
    provider: Optional[str] = None
    start_date: date
    completion_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: TrainingStatus
    score: Optional[Decimal] = None
    certificate_number: Optional[str] = None
    cost: Optional[Decimal] = None

# Endpoints

# Employee Management
@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a new employee record"""
    query = """
        INSERT INTO employees (
            employee_code, first_name, last_name, email, phone,
            department, position, employment_type, employment_status,
            hire_date, birth_date, ssn_last4, manager_id,
            salary, hourly_rate, emergency_contact_name,
            emergency_contact_phone, address, city, state, postal_code
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
        ) RETURNING id, created_at, updated_at
    """

    try:
        result = await conn.fetchrow(
            query,
            employee.employee_code, employee.first_name, employee.last_name,
            employee.email, employee.phone, employee.department,
            employee.position, employee.employment_type, employee.employment_status,
            employee.hire_date, employee.birth_date, employee.ssn_last4,
            employee.manager_id, employee.salary, employee.hourly_rate,
            employee.emergency_contact_name, employee.emergency_contact_phone,
            employee.address, employee.city, employee.state, employee.postal_code
        )

        # Background task to set up employee accounts
        background_tasks.add_task(setup_employee_accounts, str(result['id']))

        return {
            **employee.dict(),
            "id": str(result['id']),
            "created_at": result['created_at'],
            "updated_at": result['updated_at']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(
    department: Optional[Department] = None,
    status: Optional[EmploymentStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all employees with optional filters"""
    query = """
        SELECT
            e.*,
            m.first_name || ' ' || m.last_name as manager_name
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.id
        WHERE 1=1
    """
    params = []
    param_count = 0

    if department:
        param_count += 1
        query += f" AND e.department = ${param_count}"
        params.append(department)

    if status:
        param_count += 1
        query += f" AND e.employment_status = ${param_count}"
        params.append(status)

    if search:
        param_count += 1
        query += f" AND (e.first_name ILIKE ${param_count} OR e.last_name ILIKE ${param_count} OR e.email ILIKE ${param_count})"
        params.append(f"%{search}%")

    param_count += 1
    query += f" ORDER BY e.last_name, e.first_name LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "manager_id": str(row['manager_id']) if row['manager_id'] else None
        }
        for row in rows
    ]

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee details by ID"""
    query = """
        SELECT
            e.*,
            m.first_name || ' ' || m.last_name as manager_name
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.id
        WHERE e.id = $1
    """

    row = await conn.fetchrow(query, uuid.UUID(employee_id))
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        **dict(row),
        "id": str(row['id']),
        "manager_id": str(row['manager_id']) if row['manager_id'] else None
    }

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee: EmployeeUpdate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update employee information"""
    update_fields = []
    params = []
    param_count = 0

    for field, value in employee.dict(exclude_unset=True).items():
        if value is not None:
            param_count += 1
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    param_count += 1
    query = f"""
        UPDATE employees
        SET {', '.join(update_fields)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING *
    """
    params.append(uuid.UUID(employee_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        **dict(result),
        "id": str(result['id'])
    }

# Payroll Management
@router.post("/payroll", response_model=PayrollResponse)
async def create_payroll(
    payroll: PayrollCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a new payroll record"""
    payroll_number = f"PAY-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    query = """
        INSERT INTO payroll (
            payroll_number, employee_id, pay_period_start, pay_period_end,
            regular_hours, overtime_hours, holiday_hours, sick_hours, vacation_hours,
            gross_pay, deductions, net_pay, payment_method, payment_date, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 'pending'
        ) RETURNING id, created_at
    """

    result = await conn.fetchrow(
        query,
        payroll_number, uuid.UUID(payroll.employee_id),
        payroll.pay_period_start, payroll.pay_period_end,
        payroll.regular_hours, payroll.overtime_hours,
        payroll.holiday_hours, payroll.sick_hours, payroll.vacation_hours,
        payroll.gross_pay, json.dumps({k: str(v) for k, v in payroll.deductions.items()}),
        payroll.net_pay, payroll.payment_method, payroll.payment_date
    )

    # Background task to process payroll
    background_tasks.add_task(process_payroll, str(result['id']))

    return {
        **payroll.dict(),
        "id": str(result['id']),
        "payroll_number": payroll_number,
        "status": "pending",
        "created_at": result['created_at']
    }

@router.get("/payroll", response_model=List[PayrollResponse])
async def list_payroll(
    employee_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List payroll records with optional filters"""
    query = "SELECT * FROM payroll WHERE 1=1"
    params = []
    param_count = 0

    if employee_id:
        param_count += 1
        query += f" AND employee_id = ${param_count}"
        params.append(uuid.UUID(employee_id))

    if start_date:
        param_count += 1
        query += f" AND pay_period_start >= ${param_count}"
        params.append(start_date)

    if end_date:
        param_count += 1
        query += f" AND pay_period_end <= ${param_count}"
        params.append(end_date)

    if status:
        param_count += 1
        query += f" AND status = ${param_count}"
        params.append(status)

    param_count += 1
    query += f" ORDER BY payment_date DESC LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id']),
            "deductions": json.loads(row['deductions']) if row['deductions'] else {}
        }
        for row in rows
    ]

@router.post("/payroll/{payroll_id}/approve")
async def approve_payroll(
    payroll_id: str,
    approved_by: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Approve a payroll record"""
    query = """
        UPDATE payroll
        SET status = 'approved', approved_by = $1, approved_at = NOW()
        WHERE id = $2 AND status = 'pending'
        RETURNING id
    """

    result = await conn.fetchrow(query, approved_by, uuid.UUID(payroll_id))
    if not result:
        raise HTTPException(status_code=404, detail="Payroll record not found or already processed")

    return {"message": "Payroll approved successfully", "id": str(result['id'])}

@router.post("/payroll/process")
async def process_payroll_batch(
    pay_period_end: date,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Process payroll for all employees for a pay period"""
    # Get all active employees
    query = """
        SELECT id, salary, hourly_rate
        FROM employees
        WHERE employment_status = 'active'
    """

    employees = await conn.fetch(query)

    payroll_records = []
    for emp in employees:
        # Calculate pay based on time entries
        time_query = """
            SELECT
                SUM(EXTRACT(EPOCH FROM (clock_out - clock_in - INTERVAL '1 minute' * break_minutes)) / 3600) as total_hours
            FROM time_entries
            WHERE employee_id = $1
                AND work_date >= $2
                AND work_date <= $3
        """

        pay_period_start = pay_period_end - timedelta(days=13)  # 2 week pay period

        hours = await conn.fetchval(
            time_query,
            emp['id'],
            pay_period_start,
            pay_period_end
        ) or 0

        # Calculate gross pay
        if emp['salary']:
            gross_pay = emp['salary'] / 26  # Bi-weekly
        else:
            regular_hours = min(hours, 80)
            overtime_hours = max(hours - 80, 0)
            gross_pay = (regular_hours * emp['hourly_rate']) + (overtime_hours * emp['hourly_rate'] * Decimal("1.5"))

        # Simple tax calculation (would be more complex in reality)
        deductions = {
            "federal_tax": gross_pay * Decimal("0.15"),
            "state_tax": gross_pay * Decimal("0.05"),
            "social_security": gross_pay * Decimal("0.062"),
            "medicare": gross_pay * Decimal("0.0145")
        }

        net_pay = gross_pay - sum(deductions.values())

        payroll_records.append({
            "employee_id": str(emp['id']),
            "pay_period_start": pay_period_start,
            "pay_period_end": pay_period_end,
            "regular_hours": min(hours, 80),
            "overtime_hours": max(hours - 80, 0),
            "gross_pay": gross_pay,
            "deductions": deductions,
            "net_pay": net_pay,
            "payment_date": pay_period_end + timedelta(days=5)
        })

    # Create payroll records
    for record in payroll_records:
        background_tasks.add_task(
            create_payroll_record,
            record,
            conn
        )

    return {
        "message": f"Processing payroll for {len(payroll_records)} employees",
        "pay_period_end": pay_period_end
    }

# Leave Management
@router.post("/leave-requests", response_model=LeaveRequestResponse)
async def create_leave_request(
    leave_request: LeaveRequestCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a new leave request"""
    request_number = f"LV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    total_days = (leave_request.end_date - leave_request.start_date).days + 1

    query = """
        INSERT INTO leave_requests (
            request_number, employee_id, leave_type, start_date, end_date,
            total_days, reason, supporting_docs, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, 'pending'
        ) RETURNING id, created_at
    """

    result = await conn.fetchrow(
        query,
        request_number, uuid.UUID(leave_request.employee_id),
        leave_request.leave_type, leave_request.start_date,
        leave_request.end_date, total_days, leave_request.reason,
        json.dumps(leave_request.supporting_docs) if leave_request.supporting_docs else None
    )

    # Notify manager
    background_tasks.add_task(notify_manager_leave_request, str(result['id']))

    return {
        **leave_request.dict(),
        "id": str(result['id']),
        "request_number": request_number,
        "status": LeaveStatus.PENDING,
        "total_days": total_days,
        "created_at": result['created_at']
    }

@router.get("/leave-requests", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    employee_id: Optional[str] = None,
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List leave requests with optional filters"""
    query = "SELECT * FROM leave_requests WHERE 1=1"
    params = []
    param_count = 0

    if employee_id:
        param_count += 1
        query += f" AND employee_id = ${param_count}"
        params.append(uuid.UUID(employee_id))

    if status:
        param_count += 1
        query += f" AND status = ${param_count}"
        params.append(status)

    if leave_type:
        param_count += 1
        query += f" AND leave_type = ${param_count}"
        params.append(leave_type)

    param_count += 1
    query += f" ORDER BY created_at DESC LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id']),
            "supporting_docs": json.loads(row['supporting_docs']) if row['supporting_docs'] else []
        }
        for row in rows
    ]

@router.put("/leave-requests/{request_id}", response_model=LeaveRequestResponse)
async def update_leave_request(
    request_id: str,
    update: LeaveRequestUpdate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update leave request status"""
    query = """
        UPDATE leave_requests
        SET status = $1, approved_by = $2, approval_notes = $3, approval_date = NOW()
        WHERE id = $4
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        update.status,
        update.approved_by,
        update.approval_notes,
        uuid.UUID(request_id)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Notify employee of decision
    background_tasks.add_task(notify_leave_decision, str(result['id']), update.status)

    return {
        **dict(result),
        "id": str(result['id']),
        "employee_id": str(result['employee_id'])
    }

# Benefits Management
@router.post("/benefits/enroll")
async def enroll_benefit(
    enrollment: BenefitEnrollment,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Enroll employee in benefits"""
    query = """
        INSERT INTO benefit_enrollments (
            employee_id, benefit_type, plan_name, coverage_level,
            effective_date, termination_date, employee_cost, employer_cost,
            dependents
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9
        ) RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(enrollment.employee_id),
        enrollment.benefit_type,
        enrollment.plan_name,
        enrollment.coverage_level,
        enrollment.effective_date,
        enrollment.termination_date,
        enrollment.employee_cost,
        enrollment.employer_cost,
        json.dumps(enrollment.dependents) if enrollment.dependents else None
    )

    return {
        "message": "Benefit enrollment successful",
        "enrollment_id": str(result['id'])
    }

@router.get("/benefits/employee/{employee_id}")
async def get_employee_benefits(
    employee_id: str,
    active_only: bool = True,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee's benefit enrollments"""
    query = """
        SELECT * FROM benefit_enrollments
        WHERE employee_id = $1
    """
    params = [uuid.UUID(employee_id)]

    if active_only:
        query += " AND (termination_date IS NULL OR termination_date > CURRENT_DATE)"

    query += " ORDER BY effective_date DESC"

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id']),
            "dependents": json.loads(row['dependents']) if row['dependents'] else []
        }
        for row in rows
    ]

# Time & Attendance
@router.post("/time-entries")
async def create_time_entry(
    entry: TimeEntry,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Record time entry for employee"""
    query = """
        INSERT INTO time_entries (
            employee_id, work_date, clock_in, clock_out,
            break_minutes, project_id, notes
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7
        ) RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(entry.employee_id),
        entry.work_date,
        entry.clock_in,
        entry.clock_out,
        entry.break_minutes,
        uuid.UUID(entry.project_id) if entry.project_id else None,
        entry.notes
    )

    return {
        "message": "Time entry recorded",
        "entry_id": str(result['id'])
    }

@router.get("/time-entries/employee/{employee_id}")
async def get_employee_time_entries(
    employee_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee's time entries"""
    query = """
        SELECT * FROM time_entries
        WHERE employee_id = $1
    """
    params = [uuid.UUID(employee_id)]
    param_count = 1

    if start_date:
        param_count += 1
        query += f" AND work_date >= ${param_count}"
        params.append(start_date)

    if end_date:
        param_count += 1
        query += f" AND work_date <= ${param_count}"
        params.append(end_date)

    query += " ORDER BY work_date DESC, clock_in DESC"

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id']),
            "project_id": str(row['project_id']) if row['project_id'] else None,
            "total_hours": calculate_hours(row['clock_in'], row['clock_out'], row['break_minutes'])
        }
        for row in rows
    ]

# Performance Management
@router.post("/performance-reviews")
async def create_performance_review(
    review: PerformanceReview,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a performance review"""
    query = """
        INSERT INTO performance_reviews (
            employee_id, reviewer_id, review_type, review_period_start,
            review_period_end, overall_rating, ratings, strengths,
            improvements, goals, comments
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        ) RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(review.employee_id),
        uuid.UUID(review.reviewer_id),
        review.review_type,
        review.review_period_start,
        review.review_period_end,
        review.overall_rating,
        json.dumps(review.ratings),
        review.strengths,
        review.improvements,
        json.dumps(review.goals) if review.goals else None,
        review.comments
    )

    # Schedule follow-up
    background_tasks.add_task(schedule_review_followup, str(result['id']))

    return {
        "message": "Performance review created",
        "review_id": str(result['id'])
    }

@router.get("/performance-reviews/employee/{employee_id}")
async def get_employee_reviews(
    employee_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee's performance reviews"""
    query = """
        SELECT
            pr.*,
            e.first_name || ' ' || e.last_name as reviewer_name
        FROM performance_reviews pr
        JOIN employees e ON pr.reviewer_id = e.id
        WHERE pr.employee_id = $1
        ORDER BY pr.created_at DESC
    """

    rows = await conn.fetch(query, uuid.UUID(employee_id))

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id']),
            "reviewer_id": str(row['reviewer_id']),
            "ratings": json.loads(row['ratings']) if row['ratings'] else {},
            "goals": json.loads(row['goals']) if row['goals'] else []
        }
        for row in rows
    ]

# Training Management
@router.post("/training")
async def create_training_record(
    training: TrainingRecord,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a training record"""
    query = """
        INSERT INTO training_records (
            employee_id, training_name, training_type, provider,
            start_date, completion_date, expiry_date, status,
            score, certificate_number, cost
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        ) RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(training.employee_id),
        training.training_name,
        training.training_type,
        training.provider,
        training.start_date,
        training.completion_date,
        training.expiry_date,
        training.status,
        training.score,
        training.certificate_number,
        training.cost
    )

    return {
        "message": "Training record created",
        "training_id": str(result['id'])
    }

@router.get("/training/employee/{employee_id}")
async def get_employee_training(
    employee_id: str,
    include_expired: bool = False,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee's training records"""
    query = """
        SELECT * FROM training_records
        WHERE employee_id = $1
    """
    params = [uuid.UUID(employee_id)]

    if not include_expired:
        query += " AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)"

    query += " ORDER BY start_date DESC"

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "employee_id": str(row['employee_id'])
        }
        for row in rows
    ]

# Reporting endpoints
@router.get("/reports/headcount")
async def get_headcount_report(
    as_of_date: Optional[date] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get headcount report by department"""
    if not as_of_date:
        as_of_date = date.today()

    query = """
        SELECT
            department,
            employment_type,
            COUNT(*) as count,
            COUNT(CASE WHEN employment_status = 'active' THEN 1 END) as active_count
        FROM employees
        WHERE hire_date <= $1
            AND (termination_date IS NULL OR termination_date > $1)
        GROUP BY department, employment_type
        ORDER BY department, employment_type
    """

    rows = await conn.fetch(query, as_of_date)

    return {
        "as_of_date": as_of_date,
        "total_headcount": sum(row['active_count'] for row in rows),
        "by_department": [dict(row) for row in rows]
    }

@router.get("/reports/leave-balance/{employee_id}")
async def get_leave_balance(
    employee_id: str,
    year: Optional[int] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get employee's leave balance"""
    if not year:
        year = datetime.now().year

    # Get leave entitlements
    entitlement_query = """
        SELECT * FROM leave_entitlements
        WHERE employee_id = $1 AND year = $2
    """

    entitlements = await conn.fetch(entitlement_query, uuid.UUID(employee_id), year)

    # Get used leave
    used_query = """
        SELECT
            leave_type,
            SUM(total_days) as days_used
        FROM leave_requests
        WHERE employee_id = $1
            AND status = 'approved'
            AND EXTRACT(YEAR FROM start_date) = $2
        GROUP BY leave_type
    """

    used = await conn.fetch(used_query, uuid.UUID(employee_id), year)
    used_dict = {row['leave_type']: row['days_used'] for row in used}

    balances = []
    for ent in entitlements:
        leave_type = ent['leave_type']
        entitled = ent['days_entitled']
        used_days = used_dict.get(leave_type, 0)

        balances.append({
            "leave_type": leave_type,
            "entitled": entitled,
            "used": used_days,
            "remaining": entitled - used_days
        })

    return {
        "employee_id": employee_id,
        "year": year,
        "balances": balances
    }

# Helper functions
def calculate_hours(clock_in: time, clock_out: Optional[time], break_minutes: int) -> float:
    """Calculate total worked hours"""
    if not clock_out:
        return 0

    start = datetime.combine(date.today(), clock_in)
    end = datetime.combine(date.today(), clock_out)

    if end < start:  # Overnight shift
        end += timedelta(days=1)

    total_minutes = (end - start).total_seconds() / 60
    worked_minutes = total_minutes - break_minutes

    return round(worked_minutes / 60, 2)

async def setup_employee_accounts(employee_id: str):
    """Background task to set up new employee accounts"""
    # This would integrate with various systems
    # - Email account creation
    # - System access provisioning
    # - Badge/access card generation
    # etc.
    
async def process_payroll(payroll_id: str):
    """Background task to process payroll"""
    # This would handle actual payment processing
    
async def create_payroll_record(record: dict, conn: asyncpg.Connection):
    """Create individual payroll record"""
    # Implementation for batch payroll creation
    
async def notify_manager_leave_request(request_id: str):
    """Notify manager of new leave request"""
    # Send email/notification to manager
    
async def notify_leave_decision(request_id: str, status: str):
    """Notify employee of leave request decision"""
    # Send email/notification to employee
    
async def schedule_review_followup(review_id: str):
    """Schedule follow-up for performance review"""
    # Create calendar reminder, tasks, etc.
    