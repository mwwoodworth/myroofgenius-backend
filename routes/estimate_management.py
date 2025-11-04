"""
Estimate Management System
Handles creation, management, and conversion of estimates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from enum import Enum
import logging

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/estimates", tags=["Estimates"])

# ============================================================================
# ESTIMATE MODELS
# ============================================================================

class EstimateStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class EstimateLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    unit: Optional[str] = "each"
    discount_percent: Optional[float] = 0
    tax_rate: Optional[float] = 0
    notes: Optional[str] = None

class EstimateCreate(BaseModel):
    customer_id: str
    job_site_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    valid_until: Optional[date] = None
    line_items: List[EstimateLineItem] = []
    discount_amount: Optional[float] = 0
    tax_rate: Optional[float] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    is_template: bool = False

class EstimateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    valid_until: Optional[date] = None
    status: Optional[EstimateStatus] = None
    discount_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    notes: Optional[str] = None
    terms: Optional[str] = None

class EstimateResponse(BaseModel):
    id: str
    estimate_number: str
    customer_id: str
    customer_name: str
    title: str
    description: Optional[str]
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    valid_until: Optional[date]
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    line_items_count: int

# ============================================================================
# ESTIMATE ENDPOINTS
# ============================================================================

@router.post("/", response_model=EstimateResponse)
async def create_estimate(
    estimate: EstimateCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EstimateResponse:
    """Create a new estimate"""
    try:
        # Verify customer exists
        customer = db.execute(
            text("SELECT id, name, email FROM customers WHERE id = :id"),
            {"id": estimate.customer_id}
        ).fetchone()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        # Generate estimate number
        estimate_count = db.execute(
            text("SELECT COUNT(*) FROM estimates WHERE created_at >= DATE_TRUNC('year', CURRENT_DATE)")
        ).scalar()
        estimate_number = f"EST-{datetime.now().year}-{str(estimate_count + 1).zfill(5)}"

        # Calculate totals
        subtotal = 0
        tax_amount = 0

        # Create estimate
        estimate_id = str(uuid4())

        # Set valid_until to 30 days from now if not provided
        if not estimate.valid_until:
            estimate.valid_until = date.today() + timedelta(days=30)

        result = db.execute(
            text("""
                INSERT INTO estimates (
                    id, estimate_number, customer_id, job_site_id,
                    title, description, status, valid_until,
                    subtotal, discount_amount, tax_rate, tax_amount, total_amount,
                    notes, terms, created_by, created_at, updated_at, is_template
                )
                VALUES (
                    :id, :estimate_number, :customer_id, :job_site_id,
                    :title, :description, :status, :valid_until,
                    :subtotal, :discount_amount, :tax_rate, :tax_amount, :total_amount,
                    :notes, :terms, :created_by, NOW(), NOW(), :is_template
                )
                RETURNING *
            """),
            {
                "id": estimate_id,
                "estimate_number": estimate_number,
                "customer_id": estimate.customer_id,
                "job_site_id": estimate.job_site_id,
                "title": estimate.title,
                "description": estimate.description,
                "status": EstimateStatus.DRAFT.value,
                "valid_until": estimate.valid_until,
                "subtotal": 0,
                "discount_amount": estimate.discount_amount or 0,
                "tax_rate": estimate.tax_rate or 0,
                "tax_amount": 0,
                "total_amount": 0,
                "notes": estimate.notes,
                "terms": estimate.terms,
                "created_by": current_user["id"],
                "is_template": estimate.is_template
            }
        )

        # Add line items
        for item in estimate.line_items:
            line_total = item.quantity * item.unit_price * (1 - (item.discount_percent or 0) / 100)
            item_tax = line_total * (item.tax_rate or estimate.tax_rate or 0) / 100
            subtotal += line_total
            tax_amount += item_tax

            db.execute(
                text("""
                    INSERT INTO estimate_line_items (
                        id, estimate_id, description, quantity, unit,
                        unit_price, discount_percent, tax_rate,
                        line_total, tax_amount, notes, created_at
                    )
                    VALUES (
                        :id, :estimate_id, :description, :quantity, :unit,
                        :unit_price, :discount_percent, :tax_rate,
                        :line_total, :tax_amount, :notes, NOW()
                    )
                """),
                {
                    "id": str(uuid4()),
                    "estimate_id": estimate_id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "discount_percent": item.discount_percent or 0,
                    "tax_rate": item.tax_rate or estimate.tax_rate or 0,
                    "line_total": line_total,
                    "tax_amount": item_tax,
                    "notes": item.notes
                }
            )

        # Update totals
        total_after_discount = subtotal - (estimate.discount_amount or 0)
        if not tax_amount and estimate.tax_rate:
            tax_amount = total_after_discount * estimate.tax_rate / 100
        total_amount = total_after_discount + tax_amount

        db.execute(
            text("""
                UPDATE estimates
                SET subtotal = :subtotal,
                    tax_amount = :tax_amount,
                    total_amount = :total_amount
                WHERE id = :id
            """),
            {
                "id": estimate_id,
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount
            }
        )

        db.commit()

        # Log activity
        background_tasks.add_task(
            log_estimate_activity,
            estimate_id,
            "created",
            current_user["id"],
            db
        )

        return EstimateResponse(
            id=estimate_id,
            estimate_number=estimate_number,
            customer_id=estimate.customer_id,
            customer_name=customer.name,
            title=estimate.title,
            description=estimate.description,
            status=EstimateStatus.DRAFT.value,
            subtotal=subtotal,
            discount_amount=estimate.discount_amount or 0,
            tax_amount=tax_amount,
            total_amount=total_amount,
            valid_until=estimate.valid_until,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            sent_at=None,
            viewed_at=None,
            approved_at=None,
            line_items_count=len(estimate.line_items)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create estimate: {str(e)}"
        )

@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def list_estimates(
    customer_id: Optional[str] = None,
    status: Optional[EstimateStatus] = None,
    is_expired: Optional[bool] = None,
    is_template: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """List estimates with filtering"""
    try:
        # Build query
        query = """
            SELECT
                e.*,
                c.name as customer_name,
                c.email as customer_email,
                u.email as created_by_email,
                COUNT(eli.id) as line_items_count
            FROM estimates e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN users u ON e.created_by = u.id
            LEFT JOIN estimate_line_items eli ON e.id = eli.estimate_id
            WHERE 1=1
        """
        params = {}

        if customer_id:
            query += " AND e.customer_id = :customer_id"
            params["customer_id"] = customer_id

        if status:
            query += " AND e.status = :status"
            params["status"] = status.value

        if is_expired is not None:
            if is_expired:
                query += " AND e.valid_until < CURRENT_DATE AND e.status NOT IN ('converted', 'expired')"
            else:
                query += " AND (e.valid_until >= CURRENT_DATE OR e.valid_until IS NULL)"

        if is_template is not None:
            query += " AND e.is_template = :is_template"
            params["is_template"] = is_template

        if search:
            query += """ AND (
                e.estimate_number ILIKE :search
                OR e.title ILIKE :search
                OR c.name ILIKE :search
            )"""
            params["search"] = f"%{search}%"

        query += " GROUP BY e.id, c.name, c.email, u.email"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()

        # Get estimates
        query += " ORDER BY e.created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params)
        estimates = []

        for row in result:
            estimates.append({
                "id": str(row.id),
                "estimate_number": row.estimate_number,
                "customer_id": str(row.customer_id),
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "title": row.title,
                "description": row.description,
                "status": row.status,
                "subtotal": float(row.subtotal),
                "discount_amount": float(row.discount_amount or 0),
                "tax_amount": float(row.tax_amount or 0),
                "total_amount": float(row.total_amount),
                "valid_until": row.valid_until.isoformat() if row.valid_until else None,
                "is_expired": row.valid_until < date.today() if row.valid_until else False,
                "is_template": row.is_template,
                "line_items_count": row.line_items_count,
                "created_at": row.created_at.isoformat(),
                "created_by_email": row.created_by_email,
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                "viewed_at": row.viewed_at.isoformat() if row.viewed_at else None,
                "approved_at": row.approved_at.isoformat() if row.approved_at else None
            })

        return {
            "success": True,
            "data": {
                "total": total,
                "estimates": estimates,
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        message = str(e)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Estimates schema unavailable; returning fallback dataset.")
            return {
                "success": True,
                "data": {
                    "total": 0,
                    "estimates": [],
                    "limit": limit,
                    "offset": offset
                },
                "degraded": True,
                "message": "Estimates schema unavailable; returning empty list."
            }
        logger.error(f"Failed to list estimates: {message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list estimates"
        )

@router.get("/{estimate_id}", response_model=Dict[str, Any])
async def get_estimate_details(
    estimate_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get detailed estimate information"""
    try:
        # Get estimate details
        result = db.execute(
            text("""
                SELECT
                    e.*,
                    c.name as customer_name,
                    c.email as customer_email,
                    c.phone as customer_phone,
                    c.address as customer_address,
                    u.email as created_by_email,
                    u.full_name as created_by_name
                FROM estimates e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN users u ON e.created_by = u.id
                WHERE e.id = :id
            """),
            {"id": estimate_id}
        )

        estimate = result.fetchone()
        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )

        # Get line items
        line_items_result = db.execute(
            text("""
                SELECT * FROM estimate_line_items
                WHERE estimate_id = :estimate_id
                ORDER BY created_at
            """),
            {"estimate_id": estimate_id}
        )

        line_items = []
        for item in line_items_result:
            line_items.append({
                "id": str(item.id),
                "description": item.description,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "unit_price": float(item.unit_price),
                "discount_percent": float(item.discount_percent or 0),
                "tax_rate": float(item.tax_rate or 0),
                "line_total": float(item.line_total),
                "tax_amount": float(item.tax_amount or 0),
                "notes": item.notes
            })

        # Get activity history
        activity_result = db.execute(
            text("""
                SELECT
                    ea.*,
                    u.email as user_email
                FROM estimate_activity ea
                LEFT JOIN users u ON ea.user_id = u.id
                WHERE ea.estimate_id = :estimate_id
                ORDER BY ea.created_at DESC
                LIMIT 20
            """),
            {"estimate_id": estimate_id}
        )

        activities = []
        for activity in activity_result:
            activities.append({
                "action": activity.action,
                "description": activity.description,
                "user_email": activity.user_email,
                "created_at": activity.created_at.isoformat()
            })

        return {
            "estimate": {
                "id": str(estimate.id),
                "estimate_number": estimate.estimate_number,
                "customer_id": str(estimate.customer_id),
                "customer_name": estimate.customer_name,
                "customer_email": estimate.customer_email,
                "customer_phone": estimate.customer_phone,
                "customer_address": estimate.customer_address,
                "title": estimate.title,
                "description": estimate.description,
                "status": estimate.status,
                "subtotal": float(estimate.subtotal),
                "discount_amount": float(estimate.discount_amount or 0),
                "tax_rate": float(estimate.tax_rate or 0),
                "tax_amount": float(estimate.tax_amount or 0),
                "total_amount": float(estimate.total_amount),
                "valid_until": estimate.valid_until.isoformat() if estimate.valid_until else None,
                "is_expired": estimate.valid_until < date.today() if estimate.valid_until else False,
                "notes": estimate.notes,
                "terms": estimate.terms,
                "created_by": str(estimate.created_by),
                "created_by_email": estimate.created_by_email,
                "created_by_name": estimate.created_by_name,
                "created_at": estimate.created_at.isoformat(),
                "updated_at": estimate.updated_at.isoformat(),
                "sent_at": estimate.sent_at.isoformat() if estimate.sent_at else None,
                "viewed_at": estimate.viewed_at.isoformat() if estimate.viewed_at else None,
                "approved_at": estimate.approved_at.isoformat() if estimate.approved_at else None
            },
            "line_items": line_items,
            "activities": activities
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get estimate details: {str(e)}"
        )

@router.put("/{estimate_id}", response_model=dict)
async def update_estimate(
    estimate_id: str,
    update: EstimateUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update estimate details"""
    try:
        # Check if estimate exists
        existing = db.execute(
            text("SELECT status FROM estimates WHERE id = :id"),
            {"id": estimate_id}
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )

        # Don't allow updates to converted estimates
        if existing.status == EstimateStatus.CONVERTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a converted estimate"
            )

        # Build update query
        update_fields = []
        params = {"id": estimate_id}

        if update.title is not None:
            update_fields.append("title = :title")
            params["title"] = update.title

        if update.description is not None:
            update_fields.append("description = :description")
            params["description"] = update.description

        if update.valid_until is not None:
            update_fields.append("valid_until = :valid_until")
            params["valid_until"] = update.valid_until

        if update.status is not None:
            update_fields.append("status = :status")
            params["status"] = update.status.value

            # Track status change timestamps
            if update.status == EstimateStatus.SENT:
                update_fields.append("sent_at = NOW()")
            elif update.status == EstimateStatus.APPROVED:
                update_fields.append("approved_at = NOW()")

        if update.discount_amount is not None:
            update_fields.append("discount_amount = :discount_amount")
            params["discount_amount"] = update.discount_amount

        if update.tax_rate is not None:
            update_fields.append("tax_rate = :tax_rate")
            params["tax_rate"] = update.tax_rate

        if update.notes is not None:
            update_fields.append("notes = :notes")
            params["notes"] = update.notes

        if update.terms is not None:
            update_fields.append("terms = :terms")
            params["terms"] = update.terms

        update_fields.append("updated_at = NOW()")

        # Execute update
        db.execute(
            text(f"""
                UPDATE estimates
                SET {', '.join(update_fields)}
                WHERE id = :id
            """),
            params
        )

        # Recalculate totals if discount or tax changed
        if update.discount_amount is not None or update.tax_rate is not None:
            recalculate_estimate_totals(estimate_id, db)

        db.commit()

        # Log activity
        log_estimate_activity(
            estimate_id,
            "updated",
            current_user["id"],
            db,
            f"Updated: {', '.join(update_fields)}"
        )

        return {"message": "Estimate updated successfully", "id": estimate_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update estimate: {str(e)}"
        )

@router.post("/{estimate_id}/send", response_model=dict)
async def send_estimate(
    estimate_id: str,
    background_tasks: BackgroundTasks,
    email_to: Optional[str] = None,
    message: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Send estimate to customer"""
    try:
        # Get estimate and customer details
        result = db.execute(
            text("""
                SELECT
                    e.*,
                    c.email as customer_email,
                    c.name as customer_name
                FROM estimates e
                JOIN customers c ON e.customer_id = c.id
                WHERE e.id = :id
            """),
            {"id": estimate_id}
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )

        # Use provided email or customer's email
        recipient_email = email_to or result.customer_email

        if not recipient_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email address available for customer"
            )

        # Update estimate status
        db.execute(
            text("""
                UPDATE estimates
                SET status = :status,
                    sent_at = NOW(),
                    updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": estimate_id,
                "status": EstimateStatus.SENT.value
            }
        )

        db.commit()

        # Queue email sending
        background_tasks.add_task(
            send_estimate_email,
            estimate_id,
            recipient_email,
            result.customer_name,
            result.estimate_number,
            message
        )

        # Log activity
        log_estimate_activity(
            estimate_id,
            "sent",
            current_user["id"],
            db,
            f"Sent to {recipient_email}"
        )

        return {
            "message": f"Estimate sent to {recipient_email}",
            "estimate_id": estimate_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send estimate: {str(e)}"
        )

@router.post("/{estimate_id}/convert-to-job", response_model=dict)
async def convert_estimate_to_job(
    estimate_id: str,
    scheduled_start: Optional[date] = None,
    scheduled_end: Optional[date] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Convert approved estimate to job"""
    try:
        # Get estimate details
        estimate = db.execute(
            text("""
                SELECT * FROM estimates
                WHERE id = :id AND status = :status
            """),
            {
                "id": estimate_id,
                "status": EstimateStatus.APPROVED.value
            }
        ).fetchone()

        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estimate not found or not approved"
            )

        # Generate job number
        job_count = db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE created_at >= DATE_TRUNC('year', CURRENT_DATE)")
        ).scalar()
        job_number = f"JOB-{datetime.now().year}-{str(job_count + 1).zfill(5)}"

        # Create job from estimate
        job_id = str(uuid4())

        db.execute(
            text("""
                INSERT INTO jobs (
                    id, job_number, customer_id, job_site_id,
                    title, description, status,
                    estimated_revenue, actual_revenue,
                    estimated_cost, actual_cost,
                    scheduled_start, scheduled_end,
                    created_from_estimate_id, created_by,
                    created_at, updated_at, notes
                )
                VALUES (
                    :id, :job_number, :customer_id, :job_site_id,
                    :title, :description, 'scheduled',
                    :estimated_revenue, 0,
                    :estimated_cost, 0,
                    :scheduled_start, :scheduled_end,
                    :estimate_id, :created_by,
                    NOW(), NOW(), :notes
                )
            """),
            {
                "id": job_id,
                "job_number": job_number,
                "customer_id": estimate.customer_id,
                "job_site_id": estimate.job_site_id,
                "title": estimate.title,
                "description": estimate.description,
                "estimated_revenue": estimate.total_amount,
                "estimated_cost": estimate.total_amount * 0.65,  # Default 35% margin
                "scheduled_start": scheduled_start or date.today() + timedelta(days=7),
                "scheduled_end": scheduled_end or (scheduled_start or date.today()) + timedelta(days=14),
                "estimate_id": estimate_id,
                "created_by": current_user["id"],
                "notes": notes
            }
        )

        # Update estimate status
        db.execute(
            text("""
                UPDATE estimates
                SET status = :status,
                    converted_to_job_id = :job_id,
                    converted_at = NOW(),
                    updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": estimate_id,
                "status": EstimateStatus.CONVERTED.value,
                "job_id": job_id
            }
        )

        db.commit()

        # Log activity
        log_estimate_activity(
            estimate_id,
            "converted",
            current_user["id"],
            db,
            f"Converted to job {job_number}"
        )

        return {
            "message": "Estimate converted to job successfully",
            "estimate_id": estimate_id,
            "job_id": job_id,
            "job_number": job_number
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert estimate: {str(e)}"
        )

@router.post("/{estimate_id}/duplicate", response_model=EstimateResponse)
async def duplicate_estimate(
    estimate_id: str,
    customer_id: Optional[str] = None,
    title_suffix: str = " (Copy)",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EstimateResponse:
    """Create a duplicate of an existing estimate"""
    try:
        # Get original estimate
        original = db.execute(
            text("""
                SELECT * FROM estimates
                WHERE id = :id
            """),
            {"id": estimate_id}
        ).fetchone()

        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )

        # Generate new estimate number
        estimate_count = db.execute(
            text("SELECT COUNT(*) FROM estimates WHERE created_at >= DATE_TRUNC('year', CURRENT_DATE)")
        ).scalar()
        estimate_number = f"EST-{datetime.now().year}-{str(estimate_count + 1).zfill(5)}"

        # Create duplicate
        new_estimate_id = str(uuid4())

        db.execute(
            text("""
                INSERT INTO estimates (
                    id, estimate_number, customer_id, job_site_id,
                    title, description, status, valid_until,
                    subtotal, discount_amount, tax_rate, tax_amount, total_amount,
                    notes, terms, created_by, created_at, updated_at
                )
                VALUES (
                    :id, :estimate_number, :customer_id, :job_site_id,
                    :title, :description, 'draft', :valid_until,
                    :subtotal, :discount_amount, :tax_rate, :tax_amount, :total_amount,
                    :notes, :terms, :created_by, NOW(), NOW()
                )
            """),
            {
                "id": new_estimate_id,
                "estimate_number": estimate_number,
                "customer_id": customer_id or original.customer_id,
                "job_site_id": original.job_site_id,
                "title": original.title + title_suffix,
                "description": original.description,
                "valid_until": date.today() + timedelta(days=30),
                "subtotal": original.subtotal,
                "discount_amount": original.discount_amount,
                "tax_rate": original.tax_rate,
                "tax_amount": original.tax_amount,
                "total_amount": original.total_amount,
                "notes": original.notes,
                "terms": original.terms,
                "created_by": current_user["id"]
            }
        )

        # Copy line items
        db.execute(
            text("""
                INSERT INTO estimate_line_items (
                    id, estimate_id, description, quantity, unit,
                    unit_price, discount_percent, tax_rate,
                    line_total, tax_amount, notes, created_at
                )
                SELECT
                    gen_random_uuid(), :new_estimate_id, description, quantity, unit,
                    unit_price, discount_percent, tax_rate,
                    line_total, tax_amount, notes, NOW()
                FROM estimate_line_items
                WHERE estimate_id = :original_estimate_id
            """),
            {
                "new_estimate_id": new_estimate_id,
                "original_estimate_id": estimate_id
            }
        )

        db.commit()

        # Get customer name
        customer = db.execute(
            text("SELECT name FROM customers WHERE id = :id"),
            {"id": customer_id or original.customer_id}
        ).fetchone()

        return EstimateResponse(
            id=new_estimate_id,
            estimate_number=estimate_number,
            customer_id=customer_id or str(original.customer_id),
            customer_name=customer.name,
            title=original.title + title_suffix,
            description=original.description,
            status=EstimateStatus.DRAFT.value,
            subtotal=float(original.subtotal),
            discount_amount=float(original.discount_amount or 0),
            tax_amount=float(original.tax_amount or 0),
            total_amount=float(original.total_amount),
            valid_until=date.today() + timedelta(days=30),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            sent_at=None,
            viewed_at=None,
            approved_at=None,
            line_items_count=0  # Will be populated from the copy
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate estimate: {str(e)}"
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def recalculate_estimate_totals(estimate_id: str, db: Session):
    """Recalculate estimate totals based on line items"""
    try:
        # Get line items totals
        result = db.execute(
            text("""
                SELECT
                    SUM(line_total) as subtotal,
                    SUM(tax_amount) as tax_amount
                FROM estimate_line_items
                WHERE estimate_id = :estimate_id
            """),
            {"estimate_id": estimate_id}
        ).fetchone()

        # Get discount amount
        estimate = db.execute(
            text("SELECT discount_amount FROM estimates WHERE id = :id"),
            {"id": estimate_id}
        ).fetchone()

        subtotal = result.subtotal or 0
        tax_amount = result.tax_amount or 0
        discount_amount = estimate.discount_amount or 0
        total_amount = subtotal - discount_amount + tax_amount

        # Update totals
        db.execute(
            text("""
                UPDATE estimates
                SET subtotal = :subtotal,
                    tax_amount = :tax_amount,
                    total_amount = :total_amount
                WHERE id = :id
            """),
            {
                "id": estimate_id,
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount
            }
        )

    except Exception as e:
        print(f"Error recalculating totals: {e}")

def log_estimate_activity(
    estimate_id: str,
    action: str,
    user_id: str,
    db: Session,
    description: Optional[str] = None
):
    """Log estimate activity"""
    try:
        db.execute(
            text("""
                INSERT INTO estimate_activity (
                    id, estimate_id, action, description,
                    user_id, created_at
                )
                VALUES (
                    gen_random_uuid(), :estimate_id, :action, :description,
                    :user_id, NOW()
                )
            """),
            {
                "estimate_id": estimate_id,
                "action": action,
                "description": description,
                "user_id": user_id
            }
        )
        db.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def send_estimate_email(
    estimate_id: str,
    recipient_email: str,
    customer_name: str,
    estimate_number: str,
    custom_message: Optional[str] = None
):
    """Send estimate email (placeholder for actual email service)"""
    # In production, this would integrate with an email service
    # like SendGrid, AWS SES, or similar
    print(f"Sending estimate {estimate_number} to {recipient_email}")
    print(f"Customer: {customer_name}")
    if custom_message:
        print(f"Message: {custom_message} RETURNING * RETURNING *")
    
