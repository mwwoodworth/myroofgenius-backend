"""
Recruitment Management Module - Task 44
Comprehensive recruitment and applicant tracking system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, UploadFile, File, Request
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from enum import Enum
import asyncpg
import uuid
import json
from decimal import Decimal

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Enums
class JobStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"
    FREELANCE = "freelance"

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class ApplicationStatus(str, Enum):
    NEW = "new"
    SCREENING = "screening"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    REFERENCE_CHECK = "reference_check"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    HIRED = "hired"

class InterviewType(str, Enum):
    PHONE = "phone"
    VIDEO = "video"
    IN_PERSON = "in_person"
    PANEL = "panel"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class OfferStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"

class CandidateSource(str, Enum):
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    REFERRAL = "referral"
    AGENCY = "agency"
    JOB_BOARD = "job_board"
    CAREER_FAIR = "career_fair"
    DIRECT = "direct"
    OTHER = "other"

# Pydantic Models
class JobPostingBase(BaseModel):
    title: str
    department: str
    location: str
    job_type: JobType
    experience_level: ExperienceLevel
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    description: str
    requirements: List[str]
    responsibilities: List[str]
    benefits: Optional[List[str]] = []
    remote_allowed: bool = False
    visa_sponsorship: bool = False
    hiring_manager_id: str
    target_hire_date: Optional[date] = None
    positions_available: int = 1

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    status: Optional[JobStatus] = None
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None

class JobPostingResponse(JobPostingBase):
    id: str
    job_code: str
    status: JobStatus
    posted_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    applications_count: int = 0
    views_count: int = 0
    created_at: datetime
    updated_at: datetime

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    location: str
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_experience: Optional[int] = None
    education_level: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    source: CandidateSource
    source_details: Optional[str] = None

class CandidateCreate(CandidateBase):
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = []

class CandidateResponse(CandidateBase):
    id: str
    resume_url: Optional[str] = None
    skills: List[str] = []
    tags: List[str] = []
    rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

class ApplicationBase(BaseModel):
    job_posting_id: str
    candidate_id: str
    cover_letter: Optional[str] = None
    expected_salary: Optional[Decimal] = None
    available_start_date: Optional[date] = None
    referral_employee_id: Optional[str] = None

class ApplicationCreate(BaseModel):
    job_posting_id: str
    candidate: CandidateCreate
    cover_letter: Optional[str] = None
    expected_salary: Optional[Decimal] = None
    available_start_date: Optional[date] = None
    referral_employee_id: Optional[str] = None

class ApplicationResponse(ApplicationBase):
    id: str
    application_number: str
    status: ApplicationStatus
    score: Optional[int] = None
    ranking: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class InterviewBase(BaseModel):
    application_id: str
    interview_type: InterviewType
    scheduled_date: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewers: List[str]  # List of employee IDs
    instructions: Optional[str] = None

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    status: Optional[InterviewStatus] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None
    recommendation: Optional[str] = None

class InterviewResponse(InterviewBase):
    id: str
    status: InterviewStatus
    feedback: Optional[str] = None
    rating: Optional[int] = None
    recommendation: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class OfferBase(BaseModel):
    application_id: str
    position_title: str
    department: str
    salary: Decimal
    bonus: Optional[Decimal] = None
    equity: Optional[str] = None
    start_date: date
    benefits: List[str]
    conditions: Optional[List[str]] = []
    expiry_date: date

class OfferCreate(OfferBase):
    pass

class OfferResponse(OfferBase):
    id: str
    offer_number: str
    status: OfferStatus
    sent_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    negotiation_notes: Optional[str] = None
    decline_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AssessmentBase(BaseModel):
    application_id: str
    assessment_type: str  # technical, personality, skills, etc.
    assessment_name: str
    provider: Optional[str] = None
    sent_date: datetime
    due_date: Optional[datetime] = None

class AssessmentResponse(AssessmentBase):
    id: str
    completed_date: Optional[datetime] = None
    score: Optional[Decimal] = None
    result: Optional[Dict] = None
    passed: Optional[bool] = None
    created_at: datetime

# Endpoints

# Job Postings
@router.post("/job-postings", response_model=JobPostingResponse)
async def create_job_posting(
    job: JobPostingCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a new job posting"""
    job_code = f"JOB-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    query = """
        INSERT INTO job_postings (
            job_code, title, department, location, job_type, experience_level,
            min_salary, max_salary, description, requirements, responsibilities,
            benefits, remote_allowed, visa_sponsorship, hiring_manager_id,
            target_hire_date, positions_available, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
        ) RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        job_code, job.title, job.department, job.location,
        job.job_type, job.experience_level, job.min_salary, job.max_salary,
        job.description, json.dumps(job.requirements), json.dumps(job.responsibilities),
        json.dumps(job.benefits) if job.benefits else None,
        job.remote_allowed, job.visa_sponsorship,
        uuid.UUID(job.hiring_manager_id), job.target_hire_date,
        job.positions_available, JobStatus.DRAFT
    )

    # Background task to post to job boards
    background_tasks.add_task(post_to_job_boards, str(result['id']))

    return {
        **job.dict(),
        "id": str(result['id']),
        "job_code": job_code,
        "status": JobStatus.DRAFT,
        "applications_count": 0,
        "views_count": 0,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/job-postings", response_model=List[JobPostingResponse])
async def list_job_postings(
    status: Optional[JobStatus] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all job postings with optional filters"""
    query = """
        SELECT
            jp.*,
            COUNT(DISTINCT a.id) as applications_count
        FROM job_postings jp
        LEFT JOIN applications a ON jp.id = a.job_posting_id
        WHERE 1=1
    """
    params = []
    param_count = 0

    if status:
        param_count += 1
        query += f" AND jp.status = ${param_count}"
        params.append(status)

    if department:
        param_count += 1
        query += f" AND jp.department = ${param_count}"
        params.append(department)

    if location:
        param_count += 1
        query += f" AND jp.location ILIKE ${param_count}"
        params.append(f"%{location}%")

    query += " GROUP BY jp.id ORDER BY jp.created_at DESC"

    param_count += 1
    query += f" LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "hiring_manager_id": str(row['hiring_manager_id']),
            "requirements": json.loads(row['requirements']) if row['requirements'] else [],
            "responsibilities": json.loads(row['responsibilities']) if row['responsibilities'] else [],
            "benefits": json.loads(row['benefits']) if row['benefits'] else []
        }
        for row in rows
    ]

@router.put("/job-postings/{job_id}/publish")
async def publish_job_posting(
    job_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Publish a job posting"""
    query = """
        UPDATE job_postings
        SET status = 'open', posted_date = NOW(), updated_at = NOW()
        WHERE id = $1 AND status = 'draft'
        RETURNING id
    """

    result = await conn.fetchrow(query, uuid.UUID(job_id))
    if not result:
        raise HTTPException(status_code=404, detail="Job posting not found or already published")

    return {"message": "Job posting published successfully", "id": str(result['id'])}

@router.put("/job-postings/{job_id}/close")
async def close_job_posting(
    job_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Close a job posting"""
    query = """
        UPDATE job_postings
        SET status = 'closed', closed_date = NOW(), updated_at = NOW()
        WHERE id = $1 AND status = 'open'
        RETURNING id
    """

    result = await conn.fetchrow(query, uuid.UUID(job_id))
    if not result:
        raise HTTPException(status_code=404, detail="Job posting not found or not open")

    return {"message": "Job posting closed successfully", "id": str(result['id'])}

# Candidates
@router.post("/candidates", response_model=CandidateResponse)
async def create_candidate(
    candidate: CandidateCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a new candidate profile"""
    query = """
        INSERT INTO candidates (
            first_name, last_name, email, phone, location,
            current_title, current_company, years_experience,
            education_level, linkedin_url, github_url, portfolio_url,
            source, source_details, resume_text, skills
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
        ) RETURNING id, created_at
    """

    try:
        result = await conn.fetchrow(
            query,
            candidate.first_name, candidate.last_name, candidate.email,
            candidate.phone, candidate.location, candidate.current_title,
            candidate.current_company, candidate.years_experience,
            candidate.education_level, str(candidate.linkedin_url) if candidate.linkedin_url else None,
            str(candidate.github_url) if candidate.github_url else None,
            str(candidate.portfolio_url) if candidate.portfolio_url else None,
            candidate.source, candidate.source_details, candidate.resume_text,
            json.dumps(candidate.skills) if candidate.skills else None
        )

        return {
            **candidate.dict(exclude={'resume_text'}),
            "id": str(result['id']),
            "skills": candidate.skills or [],
            "tags": [],
            "created_at": result['created_at']
        }
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Candidate with this email already exists")

@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    search: Optional[str] = None,
    skills: Optional[List[str]] = Query(None),
    min_experience: Optional[int] = None,
    source: Optional[CandidateSource] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all candidates with optional filters"""
    query = """
        SELECT * FROM candidates WHERE 1=1
    """
    params = []
    param_count = 0

    if search:
        param_count += 1
        query += f"""
            AND (first_name ILIKE ${param_count}
            OR last_name ILIKE ${param_count}
            OR email ILIKE ${param_count}
            OR current_title ILIKE ${param_count})
        """
        params.append(f"%{search}%")

    if skills:
        param_count += 1
        query += f" AND skills ?| ${param_count}"
        params.append(skills)

    if min_experience:
        param_count += 1
        query += f" AND years_experience >= ${param_count}"
        params.append(min_experience)

    if source:
        param_count += 1
        query += f" AND source = ${param_count}"
        params.append(source)

    query += " ORDER BY created_at DESC"

    param_count += 1
    query += f" LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "skills": json.loads(row['skills']) if row['skills'] else [],
            "tags": json.loads(row['tags']) if row['tags'] else []
        }
        for row in rows
    ]

# Applications
@router.post("/applications", response_model=ApplicationResponse)
async def submit_application(
    application: ApplicationCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Submit a new job application"""
    # First create or find candidate
    candidate_query = """
        INSERT INTO candidates (
            first_name, last_name, email, phone, location,
            current_title, current_company, years_experience,
            education_level, source, skills
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
        ON CONFLICT (email) DO UPDATE
        SET updated_at = NOW()
        RETURNING id
    """

    candidate_id = await conn.fetchval(
        candidate_query,
        application.candidate.first_name, application.candidate.last_name,
        application.candidate.email, application.candidate.phone,
        application.candidate.location, application.candidate.current_title,
        application.candidate.current_company, application.candidate.years_experience,
        application.candidate.education_level, application.candidate.source,
        json.dumps(application.candidate.skills) if application.candidate.skills else None
    )

    # Create application
    application_number = f"APP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    app_query = """
        INSERT INTO applications (
            application_number, job_posting_id, candidate_id, cover_letter,
            expected_salary, available_start_date, referral_employee_id, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8
        ) RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        app_query,
        application_number, uuid.UUID(application.job_posting_id),
        candidate_id, application.cover_letter, application.expected_salary,
        application.available_start_date,
        uuid.UUID(application.referral_employee_id) if application.referral_employee_id else None,
        ApplicationStatus.NEW
    )

    # Background tasks
    background_tasks.add_task(score_application, str(result['id']))
    background_tasks.add_task(notify_hiring_manager, str(result['id']))

    return {
        "id": str(result['id']),
        "application_number": application_number,
        "job_posting_id": application.job_posting_id,
        "candidate_id": str(candidate_id),
        "cover_letter": application.cover_letter,
        "expected_salary": application.expected_salary,
        "available_start_date": application.available_start_date,
        "referral_employee_id": application.referral_employee_id,
        "status": ApplicationStatus.NEW,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.get("/applications", response_model=List[ApplicationResponse])
async def list_applications(
    job_posting_id: Optional[str] = None,
    status: Optional[ApplicationStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List applications with optional filters"""
    query = """
        SELECT a.*, c.first_name, c.last_name, j.title as job_title
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN job_postings j ON a.job_posting_id = j.id
        WHERE 1=1
    """
    params = []
    param_count = 0

    if job_posting_id:
        param_count += 1
        query += f" AND a.job_posting_id = ${param_count}"
        params.append(uuid.UUID(job_posting_id))

    if status:
        param_count += 1
        query += f" AND a.status = ${param_count}"
        params.append(status)

    query += " ORDER BY a.created_at DESC"

    param_count += 1
    query += f" LIMIT ${param_count}"
    params.append(limit)

    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(skip)

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "job_posting_id": str(row['job_posting_id']),
            "candidate_id": str(row['candidate_id']),
            "referral_employee_id": str(row['referral_employee_id']) if row['referral_employee_id'] else None
        }
        for row in rows
    ]

@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: str,
    status: ApplicationStatus,
    rejection_reason: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update application status"""
    query = """
        UPDATE applications
        SET status = $1, rejection_reason = $2, updated_at = NOW()
        WHERE id = $3
        RETURNING id, candidate_id
    """

    result = await conn.fetchrow(
        query,
        status,
        rejection_reason,
        uuid.UUID(application_id)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Application not found")

    # Send notification to candidate
    if background_tasks:
        background_tasks.add_task(
            notify_candidate_status_change,
            str(result['id']),
            status
        )

    return {"message": "Application status updated", "id": str(result['id'])}

# Interviews
@router.post("/interviews", response_model=InterviewResponse)
async def schedule_interview(
    interview: InterviewCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Schedule an interview"""
    query = """
        INSERT INTO interviews (
            application_id, interview_type, scheduled_date, duration_minutes,
            location, meeting_link, interviewers, instructions, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9
        ) RETURNING id, created_at
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(interview.application_id), interview.interview_type,
        interview.scheduled_date, interview.duration_minutes,
        interview.location, interview.meeting_link,
        json.dumps(interview.interviewers), interview.instructions,
        InterviewStatus.SCHEDULED
    )

    # Send calendar invites
    background_tasks.add_task(
        send_interview_invites,
        str(result['id']),
        interview.interviewers
    )

    return {
        **interview.dict(),
        "id": str(result['id']),
        "status": InterviewStatus.SCHEDULED,
        "created_at": result['created_at']
    }

@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: str,
    update: InterviewUpdate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update interview details or feedback"""
    update_fields = []
    params = []
    param_count = 0

    for field, value in update.dict(exclude_unset=True).items():
        param_count += 1
        update_fields.append(f"{field} = ${param_count}")
        params.append(value)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    param_count += 1
    query = f"""
        UPDATE interviews
        SET {', '.join(update_fields)}, updated_at = NOW()
        WHERE id = ${param_count}
        RETURNING *
    """
    params.append(uuid.UUID(interview_id))

    result = await conn.fetchrow(query, *params)
    if not result:
        raise HTTPException(status_code=404, detail="Interview not found")

    return {
        **dict(result),
        "id": str(result['id']),
        "application_id": str(result['application_id']),
        "interviewers": json.loads(result['interviewers']) if result['interviewers'] else []
    }

@router.get("/interviews/schedule")
async def get_interview_schedule(
    start_date: date,
    end_date: Optional[date] = None,
    interviewer_id: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get interview schedule for a date range"""
    if not end_date:
        end_date = start_date + timedelta(days=7)

    query = """
        SELECT
            i.*,
            a.application_number,
            c.first_name || ' ' || c.last_name as candidate_name,
            j.title as job_title
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        JOIN candidates c ON a.candidate_id = c.id
        JOIN job_postings j ON a.job_posting_id = j.id
        WHERE i.scheduled_date >= $1 AND i.scheduled_date <= $2
    """
    params = [start_date, end_date]

    if interviewer_id:
        query += " AND $3 = ANY(i.interviewers::uuid[])"
        params.append(uuid.UUID(interviewer_id))

    query += " ORDER BY i.scheduled_date"

    rows = await conn.fetch(query, *params)

    return [
        {
            **dict(row),
            "id": str(row['id']),
            "application_id": str(row['application_id']),
            "interviewers": json.loads(row['interviewers']) if row['interviewers'] else []
        }
        for row in rows
    ]

# Offers
@router.post("/offers", response_model=OfferResponse)
async def create_offer(
    offer: OfferCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create a job offer"""
    offer_number = f"OFF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    query = """
        INSERT INTO offers (
            offer_number, application_id, position_title, department,
            salary, bonus, equity, start_date, benefits, conditions,
            expiry_date, status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        ) RETURNING id, created_at, updated_at
    """

    result = await conn.fetchrow(
        query,
        offer_number, uuid.UUID(offer.application_id),
        offer.position_title, offer.department,
        offer.salary, offer.bonus, offer.equity, offer.start_date,
        json.dumps(offer.benefits), json.dumps(offer.conditions) if offer.conditions else None,
        offer.expiry_date, OfferStatus.DRAFT
    )

    return {
        **offer.dict(),
        "id": str(result['id']),
        "offer_number": offer_number,
        "status": OfferStatus.DRAFT,
        "created_at": result['created_at'],
        "updated_at": result['updated_at']
    }

@router.put("/offers/{offer_id}/send")
async def send_offer(
    offer_id: str,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Send offer to candidate"""
    query = """
        UPDATE offers
        SET status = 'sent', sent_date = NOW(), updated_at = NOW()
        WHERE id = $1 AND status IN ('draft', 'approved')
        RETURNING id, application_id
    """

    result = await conn.fetchrow(query, uuid.UUID(offer_id))
    if not result:
        raise HTTPException(status_code=404, detail="Offer not found or not ready to send")

    # Send offer letter
    background_tasks.add_task(
        send_offer_letter,
        str(result['id']),
        str(result['application_id'])
    )

    return {"message": "Offer sent successfully", "id": str(result['id'])}

@router.put("/offers/{offer_id}/response")
async def record_offer_response(
    offer_id: str,
    accepted: bool,
    negotiation_notes: Optional[str] = None,
    decline_reason: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Record candidate's response to offer"""
    status = OfferStatus.ACCEPTED if accepted else OfferStatus.DECLINED

    query = """
        UPDATE offers
        SET status = $1, response_date = NOW(), negotiation_notes = $2,
            decline_reason = $3, updated_at = NOW()
        WHERE id = $4
        RETURNING id, application_id
    """

    result = await conn.fetchrow(
        query,
        status,
        negotiation_notes,
        decline_reason,
        uuid.UUID(offer_id)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Update application status if offer accepted
    if accepted:
        await conn.execute(
            "UPDATE applications SET status = 'hired' WHERE id = $1",
            result['application_id']
        )

    return {"message": f"Offer {status}", "id": str(result['id'])}

# Assessments
@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    assessment: AssessmentBase,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create and send assessment to candidate"""
    query = """
        INSERT INTO assessments (
            application_id, assessment_type, assessment_name,
            provider, sent_date, due_date
        ) VALUES (
            $1, $2, $3, $4, $5, $6
        ) RETURNING id, created_at
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(assessment.application_id),
        assessment.assessment_type, assessment.assessment_name,
        assessment.provider, assessment.sent_date, assessment.due_date
    )

    # Send assessment link to candidate
    background_tasks.add_task(
        send_assessment_link,
        str(result['id']),
        assessment.application_id
    )

    return {
        **assessment.dict(),
        "id": str(result['id']),
        "created_at": result['created_at']
    }

@router.put("/assessments/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: str,
    score: Decimal,
    result: Dict,
    passed: bool,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Record assessment completion"""
    query = """
        UPDATE assessments
        SET completed_date = NOW(), score = $1, result = $2, passed = $3
        WHERE id = $4
        RETURNING id
    """

    update_result = await conn.fetchrow(
        query,
        score,
        json.dumps(result),
        passed,
        uuid.UUID(assessment_id)
    )

    if not update_result:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return {"message": "Assessment completed", "id": str(update_result['id'])}

# Reporting
@router.get("/reports/pipeline")
async def get_recruitment_pipeline(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get recruitment pipeline report"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    query = """
        SELECT
            j.department,
            j.title,
            COUNT(DISTINCT a.id) as total_applications,
            COUNT(DISTINCT CASE WHEN a.status = 'screening' THEN a.id END) as screening,
            COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN a.id END) as interview,
            COUNT(DISTINCT CASE WHEN a.status = 'offer' THEN a.id END) as offer,
            COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.id END) as hired,
            AVG(EXTRACT(DAY FROM a.updated_at - a.created_at)) as avg_time_to_hire
        FROM job_postings j
        LEFT JOIN applications a ON j.id = a.job_posting_id
        WHERE a.created_at >= $1 AND a.created_at <= $2
        GROUP BY j.department, j.title
        ORDER BY total_applications DESC
    """

    rows = await conn.fetch(query, start_date, end_date)

    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "pipeline": [dict(row) for row in rows]
    }

@router.get("/reports/source-effectiveness")
async def get_source_effectiveness(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get candidate source effectiveness report"""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    query = """
        SELECT
            c.source,
            COUNT(DISTINCT c.id) as total_candidates,
            COUNT(DISTINCT a.id) as total_applications,
            COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN a.id END) as interviewed,
            COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.id END) as hired,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.id END) /
                  NULLIF(COUNT(DISTINCT a.id), 0), 2) as conversion_rate
        FROM candidates c
        LEFT JOIN applications a ON c.id = a.candidate_id
        WHERE c.created_at >= $1 AND c.created_at <= $2
        GROUP BY c.source
        ORDER BY hired DESC
    """

    rows = await conn.fetch(query, start_date, end_date)

    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "sources": [dict(row) for row in rows]
    }

# Helper functions
async def post_to_job_boards(job_id: str):
    """Post job to external job boards"""
    # Integration with Indeed, LinkedIn, etc.
    
async def score_application(application_id: str):
    """Score application based on requirements match"""
    # AI-based scoring logic
    
async def notify_hiring_manager(application_id: str):
    """Notify hiring manager of new application"""
    # Email notification
    
async def notify_candidate_status_change(application_id: str, status: str):
    """Notify candidate of application status change"""
    # Email notification
    
async def send_interview_invites(interview_id: str, interviewers: List[str]):
    """Send calendar invites for interview"""
    # Calendar integration
    
async def send_offer_letter(offer_id: str, application_id: str):
    """Generate and send offer letter"""
    # PDF generation and email
    
async def send_assessment_link(assessment_id: str, application_id: str):
    """Send assessment link to candidate"""
    # Email with assessment platform link
    