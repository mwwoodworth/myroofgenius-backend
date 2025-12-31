"""
Invoice Management System
Handles invoice creation, payment tracking, and financial management
SECURITY FIX: Added tenant isolation to prevent cross-tenant data access
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from enum import Enum

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/invoices")

# ============================================================================
# INVOICE MODELS
# ============================================================================

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    OTHER = "other"

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    unit: Optional[str] = "each"
    tax_rate: Optional[float] = 0
    notes: Optional[str] = None

class InvoiceCreate(BaseModel):
    customer_id: str
    job_id: Optional[str] = None
    estimate_id: Optional[str] = None
    due_date: Optional[date] = None
    line_items: List[InvoiceLineItem] = []
    discount_amount: Optional[float] = 0
    tax_rate: Optional[float] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    send_immediately: bool = False

class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    terms: Optional[str] = None

class PaymentRecord(BaseModel):
    amount: float
    payment_method: PaymentMethod
    payment_date: Optional[date] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    amount_due: float
    due_date: Optional[date]
    created_at: datetime
    sent_at: Optional[datetime]
    paid_at: Optional[datetime]

# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@router.post("/", response_model=InvoiceResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> InvoiceResponse:
    """Create a new invoice - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify customer exists and belongs to tenant
        customer = db.execute(
            text("SELECT id, name, email FROM customers WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": invoice.customer_id, "tenant_id": tenant_id}
        ).fetchone()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        # Generate invoice number - tenant scoped
        invoice_count = db.execute(
            text("SELECT COUNT(*) FROM invoices WHERE tenant_id = :tenant_id AND created_at >= DATE_TRUNC('year', CURRENT_DATE)"),
            {"tenant_id": tenant_id}
        ).scalar()
        invoice_number = f"INV-{datetime.now().year}-{str(invoice_count + 1).zfill(5)}"

        # Calculate totals
        subtotal = 0
        tax_amount = 0

        # Create invoice
        invoice_id = str(uuid4())

        # Set due date to 30 days from now if not provided
        if not invoice.due_date:
            invoice.due_date = date.today() + timedelta(days=30)

        result = db.execute(
            text("""
                INSERT INTO invoices (
                    id, invoice_number, customer_id, job_id, estimate_id,
                    status, due_date, subtotal, discount_amount, tax_rate,
                    tax_amount, total_amount, amount_paid, amount_due,
                    notes, terms, created_by, created_at, updated_at, tenant_id
                )
                VALUES (
                    :id, :invoice_number, :customer_id, :job_id, :estimate_id,
                    :status, :due_date, :subtotal, :discount_amount, :tax_rate,
                    :tax_amount, :total_amount, 0, :total_amount,
                    :notes, :terms, :created_by, NOW(), NOW(), :tenant_id
                )
                RETURNING *
            """),
            {
                "id": invoice_id,
                "invoice_number": invoice_number,
                "customer_id": invoice.customer_id,
                "job_id": invoice.job_id,
                "estimate_id": invoice.estimate_id,
                "status": InvoiceStatus.DRAFT.value,
                "due_date": invoice.due_date,
                "subtotal": 0,
                "discount_amount": invoice.discount_amount or 0,
                "tax_rate": invoice.tax_rate or 0,
                "tax_amount": 0,
                "total_amount": 0,
                "notes": invoice.notes,
                "terms": invoice.terms,
                "created_by": current_user["id"],
                "tenant_id": tenant_id
            }
        )

        # Add line items
        for item in invoice.line_items:
            line_total = item.quantity * item.unit_price
            item_tax = line_total * (item.tax_rate or invoice.tax_rate or 0) / 100
            subtotal += line_total
            tax_amount += item_tax

            db.execute(
                text("""
                    INSERT INTO invoice_line_items (
                        id, invoice_id, description, quantity, unit,
                        unit_price, tax_rate, line_total, tax_amount,
                        notes, created_at
                    )
                    VALUES (
                        :id, :invoice_id, :description, :quantity, :unit,
                        :unit_price, :tax_rate, :line_total, :tax_amount,
                        :notes, NOW()
                    )
                """),
                {
                    "id": str(uuid4()),
                    "invoice_id": invoice_id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "tax_rate": item.tax_rate or invoice.tax_rate or 0,
                    "line_total": line_total,
                    "tax_amount": item_tax,
                    "notes": item.notes
                }
            )

        # Update totals
        total_after_discount = subtotal - (invoice.discount_amount or 0)
        if not tax_amount and invoice.tax_rate:
            tax_amount = total_after_discount * invoice.tax_rate / 100
        total_amount = total_after_discount + tax_amount

        db.execute(
            text("""
                UPDATE invoices
                SET subtotal = :subtotal,
                    tax_amount = :tax_amount,
                    total_amount = :total_amount,
                    amount_due = :total_amount
                WHERE id = :id
            """),
            {
                "id": invoice_id,
                "subtotal": subtotal,
                "tax_amount": tax_amount,
                "total_amount": total_amount
            }
        )

        # Update job status if linked
        if invoice.job_id:
            db.execute(
                text("""
                    UPDATE jobs
                    SET status = 'invoiced',
                        actual_revenue = :total_amount,
                        updated_at = NOW()
                    WHERE id = :job_id
                """),
                {"job_id": invoice.job_id, "total_amount": total_amount}
            )

        db.commit()

        # Send immediately if requested
        if invoice.send_immediately:
            background_tasks.add_task(
                send_invoice_email,
                invoice_id,
                customer.email,
                customer.name,
                invoice_number
            )

            # Update status to sent
            db.execute(
                text("UPDATE invoices SET status = 'sent', sent_at = NOW() WHERE id = :id"),
                {"id": invoice_id}
            )
            db.commit()

        invoice_data = result.fetchone()

        return InvoiceResponse(
            id=invoice_id,
            invoice_number=invoice_number,
            customer_id=invoice.customer_id,
            customer_name=customer.name,
            status=InvoiceStatus.SENT.value if invoice.send_immediately else InvoiceStatus.DRAFT.value,
            subtotal=subtotal,
            discount_amount=invoice.discount_amount or 0,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=0,
            amount_due=total_amount,
            due_date=invoice.due_date,
            created_at=datetime.now(),
            sent_at=datetime.now() if invoice.send_immediately else None,
            paid_at=None
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}"
        )

@router.get("/", response_model=Dict[str, Any])
async def list_invoices(
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None,
    is_overdue: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """List invoices with filtering - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build query with tenant filter
        query = """
            SELECT
                i.*,
                c.name as customer_name,
                c.email as customer_email,
                j.job_number,
                COUNT(ili.id) as line_items_count
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN jobs j ON i.job_id = j.id
            LEFT JOIN invoice_line_items ili ON i.id = ili.invoice_id
            WHERE i.tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id}

        if customer_id:
            query += " AND i.customer_id = :customer_id"
            params["customer_id"] = customer_id

        if status:
            query += " AND i.status = :status"
            params["status"] = status.value

        if is_overdue:
            query += " AND i.due_date < CURRENT_DATE AND i.status NOT IN ('paid', 'cancelled')"

        if search:
            query += """ AND (
                i.invoice_number ILIKE :search
                OR c.name ILIKE :search
            )"""
            params["search"] = f"%{search}%"

        query += " GROUP BY i.id, c.name, c.email, j.job_number"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()

        # Get invoices
        query += " ORDER BY i.created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params)
        invoices = []

        for row in result:
            # Check if overdue
            is_overdue = row.due_date < date.today() if row.due_date and row.status not in ['paid', 'cancelled'] else False

            invoices.append({
                "id": str(row.id),
                "invoice_number": row.invoice_number,
                "customer_id": str(row.customer_id),
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "job_number": row.job_number,
                "status": row.status,
                "is_overdue": is_overdue,
                "subtotal": float(row.subtotal),
                "discount_amount": float(row.discount_amount or 0),
                "tax_amount": float(row.tax_amount or 0),
                "total_amount": float(row.total_amount),
                "amount_paid": float(row.amount_paid or 0),
                "amount_due": float(row.amount_due or 0),
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "line_items_count": row.line_items_count,
                "created_at": row.created_at.isoformat(),
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                "paid_at": row.paid_at.isoformat() if row.paid_at else None
            })

        return {
            "total": total,
            "invoices": invoices,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invoices: {str(e)}"
        )

@router.get("/{invoice_id}", response_model=Dict[str, Any])
async def get_invoice_details(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get detailed invoice information - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Get invoice with tenant filter
        result = db.execute(
            text("""
                SELECT
                    i.*,
                    c.name as customer_name,
                    c.email as customer_email,
                    c.phone as customer_phone,
                    c.address as customer_address,
                    j.job_number,
                    j.title as job_title,
                    u.email as created_by_email
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN jobs j ON i.job_id = j.id
                LEFT JOIN users u ON i.created_by = u.id
                WHERE i.id = :id AND i.tenant_id = :tenant_id
            """),
            {"id": invoice_id, "tenant_id": tenant_id}
        )

        invoice = result.fetchone()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        # Get line items
        line_items_result = db.execute(
            text("""
                SELECT * FROM invoice_line_items
                WHERE invoice_id = :invoice_id
                ORDER BY created_at
            """),
            {"invoice_id": invoice_id}
        )

        line_items = []
        for item in line_items_result:
            line_items.append({
                "id": str(item.id),
                "description": item.description,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "unit_price": float(item.unit_price),
                "tax_rate": float(item.tax_rate or 0),
                "line_total": float(item.line_total),
                "tax_amount": float(item.tax_amount or 0),
                "notes": item.notes
            })

        # Get payment history
        payments_result = db.execute(
            text("""
                SELECT
                    p.*,
                    u.email as processed_by_email
                FROM invoice_payments p
                LEFT JOIN users u ON p.processed_by = u.id
                WHERE p.invoice_id = :invoice_id
                ORDER BY p.payment_date DESC
            """),
            {"invoice_id": invoice_id}
        )

        payments = []
        for payment in payments_result:
            payments.append({
                "id": str(payment.id),
                "amount": float(payment.amount),
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "reference_number": payment.reference_number,
                "notes": payment.notes,
                "processed_by_email": payment.processed_by_email,
                "created_at": payment.created_at.isoformat()
            })

        # Check if overdue
        is_overdue = invoice.due_date < date.today() if invoice.due_date and invoice.status not in ['paid', 'cancelled'] else False

        return {
            "invoice": {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "customer_id": str(invoice.customer_id),
                "customer_name": invoice.customer_name,
                "customer_email": invoice.customer_email,
                "customer_phone": invoice.customer_phone,
                "customer_address": invoice.customer_address,
                "job_id": str(invoice.job_id) if invoice.job_id else None,
                "job_number": invoice.job_number,
                "job_title": invoice.job_title,
                "status": invoice.status,
                "is_overdue": is_overdue,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "subtotal": float(invoice.subtotal),
                "discount_amount": float(invoice.discount_amount or 0),
                "tax_rate": float(invoice.tax_rate or 0),
                "tax_amount": float(invoice.tax_amount or 0),
                "total_amount": float(invoice.total_amount),
                "amount_paid": float(invoice.amount_paid or 0),
                "amount_due": float(invoice.amount_due or 0),
                "notes": invoice.notes,
                "terms": invoice.terms,
                "created_by": str(invoice.created_by),
                "created_by_email": invoice.created_by_email,
                "created_at": invoice.created_at.isoformat(),
                "sent_at": invoice.sent_at.isoformat() if invoice.sent_at else None,
                "viewed_at": invoice.viewed_at.isoformat() if invoice.viewed_at else None,
                "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None
            },
            "line_items": line_items,
            "payments": payments,
            "payment_summary": {
                "total_paid": float(invoice.amount_paid or 0),
                "total_due": float(invoice.amount_due or 0),
                "payment_count": len(payments)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice details: {str(e)}"
        )

@router.post("/{invoice_id}/payment", response_model=dict)
async def record_payment(
    invoice_id: str,
    payment: PaymentRecord,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Record a payment for an invoice - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Get invoice with tenant filter
        invoice = db.execute(
            text("SELECT * FROM invoices WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": invoice_id, "tenant_id": tenant_id}
        ).fetchone()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already paid"
            )

        # Record payment
        payment_id = str(uuid4())
        payment_date = payment.payment_date or date.today()

        db.execute(
            text("""
                INSERT INTO invoice_payments (
                    id, invoice_id, amount, payment_method,
                    payment_date, reference_number, notes,
                    processed_by, created_at
                )
                VALUES (
                    :id, :invoice_id, :amount, :payment_method,
                    :payment_date, :reference_number, :notes,
                    :processed_by, NOW()
                )
            """),
            {
                "id": payment_id,
                "invoice_id": invoice_id,
                "amount": payment.amount,
                "payment_method": payment.payment_method.value,
                "payment_date": payment_date,
                "reference_number": payment.reference_number,
                "notes": payment.notes,
                "processed_by": current_user["id"]
            }
        )

        # Update invoice totals
        new_amount_paid = float(invoice.amount_paid or 0) + payment.amount
        new_amount_due = float(invoice.total_amount) - new_amount_paid

        # Determine new status
        if new_amount_due <= 0:
            new_status = InvoiceStatus.PAID.value
            paid_at = "NOW()"
        elif new_amount_paid > 0:
            new_status = InvoiceStatus.PARTIAL.value
            paid_at = "NULL"
        else:
            new_status = invoice.status
            paid_at = "NULL"

        # Update invoice
        db.execute(
            text(f"""
                UPDATE invoices
                SET amount_paid = :amount_paid,
                    amount_due = :amount_due,
                    status = :status,
                    paid_at = {paid_at},
                    updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": invoice_id,
                "amount_paid": new_amount_paid,
                "amount_due": max(0, new_amount_due),
                "status": new_status
            }
        )

        db.commit()

        return {
            "message": "Payment recorded successfully",
            "payment_id": payment_id,
            "amount_paid": payment.amount,
            "total_paid": new_amount_paid,
            "amount_due": max(0, new_amount_due),
            "invoice_status": new_status
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record payment: {str(e)}"
        )

@router.post("/{invoice_id}/send", response_model=dict)
async def send_invoice(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    email_to: Optional[str] = None,
    message: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Send invoice to customer - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Get invoice and customer with tenant filter
        result = db.execute(
            text("""
                SELECT
                    i.*,
                    c.email as customer_email,
                    c.name as customer_name
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.id = :id AND i.tenant_id = :tenant_id
            """),
            {"id": invoice_id, "tenant_id": tenant_id}
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        recipient_email = email_to or result.customer_email

        if not recipient_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email address available"
            )

        # Update status
        db.execute(
            text("""
                UPDATE invoices
                SET status = CASE
                        WHEN status = 'draft' THEN 'sent'
                        ELSE status
                    END,
                    sent_at = COALESCE(sent_at, NOW()),
                    updated_at = NOW()
                WHERE id = :id
            """),
            {"id": invoice_id}
        )

        db.commit()

        # Queue email sending
        background_tasks.add_task(
            send_invoice_email,
            invoice_id,
            recipient_email,
            result.customer_name,
            result.invoice_number,
            message
        )

        return {
            "message": f"Invoice sent to {recipient_email}",
            "invoice_id": invoice_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invoice: {str(e)}"
        )

@router.get("/overdue/list", response_model=Dict[str, Any])
async def get_overdue_invoices(
    days_overdue: Optional[int] = Query(None, ge=1),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get list of overdue invoices - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        query = """
            SELECT
                i.*,
                c.name as customer_name,
                c.email as customer_email,
                c.phone as customer_phone,
                DATE_PART('day', CURRENT_DATE - i.due_date) as days_overdue
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.tenant_id = :tenant_id
                AND i.due_date < CURRENT_DATE
                AND i.status NOT IN ('paid', 'cancelled')
        """
        params = {"tenant_id": tenant_id}

        if days_overdue:
            query += " AND i.due_date <= CURRENT_DATE - INTERVAL ':days days'"
            params["days"] = days_overdue

        query += " ORDER BY i.due_date"

        result = db.execute(text(query), params)

        overdue_invoices = []
        total_overdue = 0

        for row in result:
            amount_due = float(row.amount_due or 0)
            total_overdue += amount_due

            overdue_invoices.append({
                "id": str(row.id),
                "invoice_number": row.invoice_number,
                "customer_id": str(row.customer_id),
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "customer_phone": row.customer_phone,
                "total_amount": float(row.total_amount),
                "amount_due": amount_due,
                "due_date": row.due_date.isoformat(),
                "days_overdue": int(row.days_overdue),
                "status": row.status
            })

        return {
            "total_count": len(overdue_invoices),
            "total_amount_overdue": total_overdue,
            "invoices": overdue_invoices
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overdue invoices: {str(e)}"
        )

@router.get("/summary/stats", response_model=Dict[str, Any])
async def get_invoice_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get invoice summary statistics - tenant isolated"""
    try:
        # Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Default to current month
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = date.today().replace(day=1)

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "tenant_id": tenant_id
        }

        # Get summary stats with tenant filter
        result = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_invoices,
                    COUNT(*) FILTER (WHERE status = 'draft') as draft_count,
                    COUNT(*) FILTER (WHERE status = 'sent') as sent_count,
                    COUNT(*) FILTER (WHERE status = 'paid') as paid_count,
                    COUNT(*) FILTER (WHERE status = 'partial') as partial_count,
                    COUNT(*) FILTER (WHERE due_date < CURRENT_DATE AND status NOT IN ('paid', 'cancelled')) as overdue_count,
                    COALESCE(SUM(total_amount), 0) as total_billed,
                    COALESCE(SUM(amount_paid), 0) as total_collected,
                    COALESCE(SUM(amount_due), 0) as total_outstanding,
                    COALESCE(AVG(total_amount), 0) as avg_invoice_amount,
                    COALESCE(AVG(
                        CASE
                            WHEN paid_at IS NOT NULL
                            THEN DATE_PART('day', paid_at - created_at)
                            ELSE NULL
                        END
                    ), 0) as avg_days_to_payment
                FROM invoices
                WHERE tenant_id = :tenant_id AND created_at BETWEEN :start_date AND :end_date
            """),
            params
        ).fetchone()

        # Get top customers by invoice value with tenant filter
        top_customers = db.execute(
            text("""
                SELECT
                    c.id,
                    c.name,
                    COUNT(i.id) as invoice_count,
                    SUM(i.total_amount) as total_amount,
                    SUM(i.amount_paid) as amount_paid
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.tenant_id = :tenant_id AND i.created_at BETWEEN :start_date AND :end_date
                GROUP BY c.id, c.name
                ORDER BY total_amount DESC
                LIMIT 5
            """),
            params
        )

        top_customers_list = []
        for customer in top_customers:
            top_customers_list.append({
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "invoice_count": customer.invoice_count,
                "total_amount": float(customer.total_amount or 0),
                "amount_paid": float(customer.amount_paid or 0)
            })

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_invoices": result.total_invoices,
                "draft_count": result.draft_count,
                "sent_count": result.sent_count,
                "paid_count": result.paid_count,
                "partial_count": result.partial_count,
                "overdue_count": result.overdue_count,
                "total_billed": float(result.total_billed),
                "total_collected": float(result.total_collected),
                "total_outstanding": float(result.total_outstanding),
                "avg_invoice_amount": float(result.avg_invoice_amount),
                "avg_days_to_payment": round(result.avg_days_to_payment or 0, 1),
                "collection_rate": round((float(result.total_collected) / float(result.total_billed) * 100), 2) if result.total_billed > 0 else 0
            },
            "top_customers": top_customers_list
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice summary: {str(e)}"
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_invoice_email(
    invoice_id: str,
    recipient_email: str,
    customer_name: str,
    invoice_number: str,
    custom_message: Optional[str] = None
):
    """Send invoice email (placeholder for actual email service)"""
    # In production, this would integrate with an email service
    print(f"Sending invoice {invoice_number} to {recipient_email}")
    print(f"Customer: {customer_name}")
    if custom_message:
        print(f"Message: {custom_message} RETURNING *")
    