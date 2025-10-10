"""
Recurring Invoices Module
Task 35: Recurring invoices implementation

Automated recurring invoice generation for subscriptions,
retainers, and regular services with flexible scheduling.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import json
import uuid
import asyncpg
import os
import logging
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

router = APIRouter()

# ==================== Enums ====================

class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"
    CUSTOM = "custom"

class RecurrenceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class BillingDay(str, Enum):
    FIRST = "first"  # First day of month
    LAST = "last"    # Last day of month
    SPECIFIC = "specific"  # Specific day number
    WEEKDAY = "weekday"  # Specific weekday

# ==================== Pydantic Models ====================

class RecurringInvoiceSchedule(BaseModel):
    """Recurring invoice schedule configuration"""
    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1, description="Interval between occurrences")
    billing_day: Optional[BillingDay] = None
    specific_day: Optional[int] = Field(default=None, ge=1, le=31)
    weekday: Optional[int] = Field(default=None, ge=0, le=6, description="0=Monday, 6=Sunday")
    time_of_day: str = Field(default="09:00", description="Time to generate invoice (HH:MM)")
    timezone: str = Field(default="America/New_York")

class CreateRecurringInvoice(BaseModel):
    """Create recurring invoice request"""
    customer_id: str = Field(description="Customer ID")
    template_id: Optional[str] = Field(default=None, description="Invoice template ID")
    schedule: RecurringInvoiceSchedule
    start_date: date = Field(description="Start date for recurring invoices")
    end_date: Optional[date] = Field(default=None, description="End date (None for ongoing)")
    max_occurrences: Optional[int] = Field(default=None, ge=1, description="Maximum number of invoices")
    line_items: List[Dict[str, Any]] = Field(description="Invoice line items")
    tax_rate: float = Field(default=0.0, ge=0, le=100)
    payment_terms: str = Field(default="Net 30")
    notes: Optional[str] = None
    auto_send: bool = Field(default=False, description="Automatically send invoices")
    auto_charge: bool = Field(default=False, description="Automatically charge saved payment method")
    metadata: Optional[Dict[str, Any]] = None

class UpdateRecurringInvoice(BaseModel):
    """Update recurring invoice request"""
    schedule: Optional[RecurringInvoiceSchedule] = None
    end_date: Optional[date] = None
    max_occurrences: Optional[int] = None
    line_items: Optional[List[Dict[str, Any]]] = None
    tax_rate: Optional[float] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    auto_send: Optional[bool] = None
    auto_charge: Optional[bool] = None
    status: Optional[RecurrenceStatus] = None

class RecurringInvoiceInstance(BaseModel):
    """Individual instance of a recurring invoice"""
    recurring_invoice_id: str
    invoice_id: Optional[str]
    occurrence_number: int
    scheduled_date: date
    generated_at: Optional[datetime]
    status: str  # scheduled, generated, sent, paid, failed
    error_message: Optional[str]

class RecurrencePreview(BaseModel):
    """Preview of upcoming recurring invoices"""
    count: int = Field(default=10, ge=1, le=50, description="Number of occurrences to preview")
    include_amounts: bool = Field(default=True, description="Calculate amounts for each occurrence")

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Recurring Invoice Management ====================

@router.post("/create", tags=["Recurring Invoices"])
async def create_recurring_invoice(
    invoice: CreateRecurringInvoice,
    background_tasks: BackgroundTasks
):
    """Create a new recurring invoice schedule"""
    try:
        conn = await get_db_connection()
        try:
            # Verify customer exists
            customer = await conn.fetchrow("""
                SELECT * FROM customers WHERE id = $1
            """, uuid.UUID(invoice.customer_id))
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Create recurring invoice record
            recurring_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO recurring_invoices (
                    id, customer_id, template_id, frequency, interval_value,
                    billing_day, specific_day, weekday, start_date, end_date,
                    max_occurrences, line_items, tax_rate, payment_terms,
                    notes, auto_send, auto_charge, status, metadata,
                    next_occurrence_date, occurrences_generated
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
            """, uuid.UUID(recurring_id),
                uuid.UUID(invoice.customer_id),
                uuid.UUID(invoice.template_id) if invoice.template_id else None,
                invoice.schedule.frequency.value,
                invoice.schedule.interval,
                invoice.schedule.billing_day.value if invoice.schedule.billing_day else None,
                invoice.schedule.specific_day,
                invoice.schedule.weekday,
                invoice.start_date,
                invoice.end_date,
                invoice.max_occurrences,
                json.dumps(invoice.line_items),
                invoice.tax_rate,
                invoice.payment_terms,
                invoice.notes,
                invoice.auto_send,
                invoice.auto_charge,
                RecurrenceStatus.ACTIVE.value,
                json.dumps(invoice.metadata) if invoice.metadata else None,
                invoice.start_date,  # next_occurrence_date
                0  # occurrences_generated
            )
            
            # Generate preview of upcoming invoices
            preview = await generate_recurrence_preview(
                recurring_id,
                invoice.schedule,
                invoice.start_date,
                invoice.end_date,
                invoice.max_occurrences,
                5
            )
            
            # Schedule first invoice if start date is today
            if invoice.start_date <= date.today():
                background_tasks.add_task(
                    generate_recurring_invoice_instance,
                    recurring_id
                )
            
            return {
                "success": True,
                "recurring_invoice_id": recurring_id,
                "message": f"Recurring invoice created for customer {customer['customer_name']}",
                "next_occurrences": preview
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", tags=["Recurring Invoices"])
async def list_recurring_invoices(
    customer_id: Optional[str] = None,
    status: Optional[RecurrenceStatus] = None,
    frequency: Optional[RecurrenceFrequency] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List recurring invoices with filters"""
    try:
        conn = await get_db_connection()
        try:
            # Build query
            query = """
                SELECT r.*, c.customer_name, c.email,
                       COUNT(ri.id) as total_generated,
                       SUM(CASE WHEN i.status = 'paid' THEN 1 ELSE 0 END) as total_paid
                FROM recurring_invoices r
                JOIN customers c ON r.customer_id = c.id
                LEFT JOIN recurring_invoice_instances ri ON r.id = ri.recurring_invoice_id
                LEFT JOIN invoices i ON ri.invoice_id = i.id
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if customer_id:
                param_count += 1
                query += f" AND r.customer_id = ${param_count}"
                params.append(uuid.UUID(customer_id))
            
            if status:
                param_count += 1
                query += f" AND r.status = ${param_count}"
                params.append(status.value)
            
            if frequency:
                param_count += 1
                query += f" AND r.frequency = ${param_count}"
                params.append(frequency.value)
            
            query += f"""
                GROUP BY r.id, c.customer_name, c.email
                ORDER BY r.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            invoices = []
            for row in rows:
                invoices.append({
                    "id": str(row['id']),
                    "customer_id": str(row['customer_id']),
                    "customer_name": row['customer_name'],
                    "customer_email": row['email'],
                    "frequency": row['frequency'],
                    "interval": row['interval_value'],
                    "start_date": row['start_date'].isoformat() if row['start_date'] else None,
                    "end_date": row['end_date'].isoformat() if row['end_date'] else None,
                    "next_occurrence": row['next_occurrence_date'].isoformat() if row['next_occurrence_date'] else None,
                    "occurrences_generated": row['occurrences_generated'],
                    "total_generated": row['total_generated'],
                    "total_paid": row['total_paid'] or 0,
                    "status": row['status'],
                    "auto_send": row['auto_send'],
                    "auto_charge": row['auto_charge'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM recurring_invoices WHERE 1=1"
            if customer_id:
                count_query += " AND customer_id = $1"
                total = await conn.fetchval(count_query, uuid.UUID(customer_id))
            else:
                total = await conn.fetchval(count_query)
            
            return {
                "recurring_invoices": invoices,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error listing recurring invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{recurring_id}", tags=["Recurring Invoices"])
async def get_recurring_invoice(recurring_id: str):
    """Get recurring invoice details"""
    try:
        conn = await get_db_connection()
        try:
            # Get recurring invoice
            invoice = await conn.fetchrow("""
                SELECT r.*, c.customer_name, c.email
                FROM recurring_invoices r
                JOIN customers c ON r.customer_id = c.id
                WHERE r.id = $1
            """, uuid.UUID(recurring_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Recurring invoice not found")
            
            # Get instances
            instances = await conn.fetch("""
                SELECT ri.*, i.invoice_number, i.total_cents, i.status as invoice_status
                FROM recurring_invoice_instances ri
                LEFT JOIN invoices i ON ri.invoice_id = i.id
                WHERE ri.recurring_invoice_id = $1
                ORDER BY ri.occurrence_number DESC
                LIMIT 10
            """, uuid.UUID(recurring_id))
            
            # Calculate statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_instances,
                    SUM(CASE WHEN i.status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                    SUM(i.total_cents) / 100.0 as total_revenue,
                    AVG(i.total_cents) / 100.0 as average_amount
                FROM recurring_invoice_instances ri
                JOIN invoices i ON ri.invoice_id = i.id
                WHERE ri.recurring_invoice_id = $1
            """, uuid.UUID(recurring_id))
            
            return {
                "id": str(invoice['id']),
                "customer_id": str(invoice['customer_id']),
                "customer_name": invoice['customer_name'],
                "customer_email": invoice['email'],
                "schedule": {
                    "frequency": invoice['frequency'],
                    "interval": invoice['interval_value'],
                    "billing_day": invoice['billing_day'],
                    "specific_day": invoice['specific_day'],
                    "weekday": invoice['weekday']
                },
                "start_date": invoice['start_date'].isoformat() if invoice['start_date'] else None,
                "end_date": invoice['end_date'].isoformat() if invoice['end_date'] else None,
                "next_occurrence": invoice['next_occurrence_date'].isoformat() if invoice['next_occurrence_date'] else None,
                "line_items": json.loads(invoice['line_items']) if invoice['line_items'] else [],
                "tax_rate": float(invoice['tax_rate']) if invoice['tax_rate'] else 0,
                "payment_terms": invoice['payment_terms'],
                "notes": invoice['notes'],
                "status": invoice['status'],
                "auto_send": invoice['auto_send'],
                "auto_charge": invoice['auto_charge'],
                "statistics": {
                    "total_generated": stats['total_instances'] or 0,
                    "paid_count": stats['paid_count'] or 0,
                    "total_revenue": float(stats['total_revenue']) if stats['total_revenue'] else 0,
                    "average_amount": float(stats['average_amount']) if stats['average_amount'] else 0
                },
                "recent_instances": [
                    {
                        "occurrence_number": inst['occurrence_number'],
                        "scheduled_date": inst['scheduled_date'].isoformat() if inst['scheduled_date'] else None,
                        "invoice_number": inst['invoice_number'],
                        "amount": inst['total_cents'] / 100 if inst['total_cents'] else 0,
                        "status": inst['invoice_status'] or inst['status']
                    }
                    for inst in instances
                ],
                "created_at": invoice['created_at'].isoformat() if invoice['created_at'] else None
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{recurring_id}", tags=["Recurring Invoices"])
async def update_recurring_invoice(
    recurring_id: str,
    update: UpdateRecurringInvoice
):
    """Update recurring invoice configuration"""
    try:
        conn = await get_db_connection()
        try:
            # Check if exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM recurring_invoices WHERE id = $1)",
                uuid.UUID(recurring_id)
            )
            
            if not exists:
                raise HTTPException(status_code=404, detail="Recurring invoice not found")
            
            # Build update query
            updates = []
            params = []
            param_count = 1
            
            if update.schedule:
                updates.append(f"frequency = ${param_count}")
                params.append(update.schedule.frequency.value)
                param_count += 1
                
                updates.append(f"interval_value = ${param_count}")
                params.append(update.schedule.interval)
                param_count += 1
            
            if update.end_date is not None:
                updates.append(f"end_date = ${param_count}")
                params.append(update.end_date)
                param_count += 1
            
            if update.line_items is not None:
                updates.append(f"line_items = ${param_count}")
                params.append(json.dumps(update.line_items))
                param_count += 1
            
            if update.tax_rate is not None:
                updates.append(f"tax_rate = ${param_count}")
                params.append(update.tax_rate)
                param_count += 1
            
            if update.auto_send is not None:
                updates.append(f"auto_send = ${param_count}")
                params.append(update.auto_send)
                param_count += 1
            
            if update.auto_charge is not None:
                updates.append(f"auto_charge = ${param_count}")
                params.append(update.auto_charge)
                param_count += 1
            
            if update.status is not None:
                updates.append(f"status = ${param_count}")
                params.append(update.status.value)
                param_count += 1
            
            if updates:
                updates.append("updated_at = NOW()")
                query = f"""
                    UPDATE recurring_invoices
                    SET {', '.join(updates)}
                    WHERE id = ${param_count}
                    RETURNING *
                """
                params.append(uuid.UUID(recurring_id))
                
                row = await conn.fetchrow(query, *params)
                
                return {
                    "success": True,
                    "message": "Recurring invoice updated successfully",
                    "recurring_invoice": {
                        "id": str(row['id']),
                        "status": row['status'],
                        "next_occurrence": row['next_occurrence_date'].isoformat() if row['next_occurrence_date'] else None
                    }
                }
            else:
                return {
                    "success": True,
                    "message": "No updates provided"
                }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Actions ====================

@router.post("/{recurring_id}/pause", tags=["Recurring Invoices"])
async def pause_recurring_invoice(recurring_id: str):
    """Pause a recurring invoice"""
    try:
        conn = await get_db_connection()
        try:
            result = await conn.execute("""
                UPDATE recurring_invoices
                SET status = 'paused',
                    updated_at = NOW()
                WHERE id = $1 AND status = 'active'
            """, uuid.UUID(recurring_id))
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Recurring invoice not found or not active")
            
            return {
                "success": True,
                "message": "Recurring invoice paused successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{recurring_id}/resume", tags=["Recurring Invoices"])
async def resume_recurring_invoice(recurring_id: str):
    """Resume a paused recurring invoice"""
    try:
        conn = await get_db_connection()
        try:
            # Resume and calculate next occurrence
            invoice = await conn.fetchrow("""
                UPDATE recurring_invoices
                SET status = 'active',
                    next_occurrence_date = CASE
                        WHEN next_occurrence_date < CURRENT_DATE THEN CURRENT_DATE
                        ELSE next_occurrence_date
                    END,
                    updated_at = NOW()
                WHERE id = $1 AND status = 'paused'
                RETURNING *
            """, uuid.UUID(recurring_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Recurring invoice not found or not paused")
            
            return {
                "success": True,
                "message": "Recurring invoice resumed successfully",
                "next_occurrence": invoice['next_occurrence_date'].isoformat() if invoice['next_occurrence_date'] else None
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{recurring_id}/cancel", tags=["Recurring Invoices"])
async def cancel_recurring_invoice(
    recurring_id: str,
    cancel_pending: bool = Query(default=False, description="Cancel pending instances")
):
    """Cancel a recurring invoice"""
    try:
        conn = await get_db_connection()
        try:
            async with conn.transaction():
                # Cancel recurring invoice
                result = await conn.execute("""
                    UPDATE recurring_invoices
                    SET status = 'cancelled',
                        updated_at = NOW()
                    WHERE id = $1 AND status IN ('active', 'paused')
                """, uuid.UUID(recurring_id))
                
                if result == "UPDATE 0":
                    raise HTTPException(status_code=404, detail="Recurring invoice not found or already cancelled")
                
                # Cancel pending instances if requested
                if cancel_pending:
                    await conn.execute("""
                        UPDATE recurring_invoice_instances
                        SET status = 'cancelled'
                        WHERE recurring_invoice_id = $1 AND status = 'scheduled'
                    """, uuid.UUID(recurring_id))
            
            return {
                "success": True,
                "message": "Recurring invoice cancelled successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling recurring invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Preview & Generation ====================

@router.post("/{recurring_id}/preview", tags=["Recurring Invoices"])
async def preview_recurring_invoices(
    recurring_id: str,
    preview: RecurrencePreview
):
    """Preview upcoming recurring invoice occurrences"""
    try:
        conn = await get_db_connection()
        try:
            # Get recurring invoice
            invoice = await conn.fetchrow("""
                SELECT * FROM recurring_invoices WHERE id = $1
            """, uuid.UUID(recurring_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Recurring invoice not found")
            
            # Generate preview
            schedule = RecurringInvoiceSchedule(
                frequency=RecurrenceFrequency(invoice['frequency']),
                interval=invoice['interval_value'],
                billing_day=BillingDay(invoice['billing_day']) if invoice['billing_day'] else None,
                specific_day=invoice['specific_day'],
                weekday=invoice['weekday']
            )
            
            occurrences = await generate_recurrence_preview(
                recurring_id,
                schedule,
                invoice['next_occurrence_date'] or invoice['start_date'],
                invoice['end_date'],
                invoice['max_occurrences'] - invoice['occurrences_generated'] if invoice['max_occurrences'] else None,
                preview.count
            )
            
            # Calculate amounts if requested
            if preview.include_amounts:
                line_items = json.loads(invoice['line_items']) if invoice['line_items'] else []
                subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in line_items)
                tax = subtotal * (invoice['tax_rate'] / 100 if invoice['tax_rate'] else 0)
                total = subtotal + tax
                
                for occ in occurrences:
                    occ['amount'] = total
            
            return {
                "recurring_invoice_id": recurring_id,
                "upcoming_occurrences": occurrences
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing recurring invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{recurring_id}/generate-next", tags=["Recurring Invoices"])
async def generate_next_invoice(
    recurring_id: str,
    background_tasks: BackgroundTasks
):
    """Manually generate the next invoice in the series"""
    try:
        conn = await get_db_connection()
        try:
            # Get recurring invoice
            invoice = await conn.fetchrow("""
                SELECT * FROM recurring_invoices
                WHERE id = $1 AND status = 'active'
            """, uuid.UUID(recurring_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Recurring invoice not found or not active")
            
            # Generate invoice
            invoice_id = await generate_invoice_from_recurring(
                conn,
                invoice,
                invoice['occurrences_generated'] + 1
            )
            
            # Update next occurrence
            next_date = calculate_next_occurrence(
                invoice['next_occurrence_date'] or invoice['start_date'],
                invoice['frequency'],
                invoice['interval_value']
            )
            
            await conn.execute("""
                UPDATE recurring_invoices
                SET occurrences_generated = occurrences_generated + 1,
                    next_occurrence_date = $2,
                    updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(recurring_id), next_date)
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "message": "Invoice generated successfully",
                "next_occurrence": next_date.isoformat()
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating next invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Instances & History ====================

@router.get("/{recurring_id}/instances", tags=["Recurring Invoices"])
async def get_recurring_invoice_instances(
    recurring_id: str,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100)
):
    """Get instances of a recurring invoice"""
    try:
        conn = await get_db_connection()
        try:
            query = """
                SELECT ri.*, i.invoice_number, i.total_cents, i.status as invoice_status,
                       i.paid_date, i.due_date
                FROM recurring_invoice_instances ri
                LEFT JOIN invoices i ON ri.invoice_id = i.id
                WHERE ri.recurring_invoice_id = $1
            """
            params = [uuid.UUID(recurring_id)]
            
            if status:
                query += " AND ri.status = $2"
                params.append(status)
            
            query += " ORDER BY ri.occurrence_number DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            instances = await conn.fetch(query, *params)
            
            return {
                "recurring_invoice_id": recurring_id,
                "instances": [
                    {
                        "id": str(inst['id']),
                        "occurrence_number": inst['occurrence_number'],
                        "scheduled_date": inst['scheduled_date'].isoformat() if inst['scheduled_date'] else None,
                        "generated_at": inst['generated_at'].isoformat() if inst['generated_at'] else None,
                        "invoice_id": str(inst['invoice_id']) if inst['invoice_id'] else None,
                        "invoice_number": inst['invoice_number'],
                        "amount": inst['total_cents'] / 100 if inst['total_cents'] else None,
                        "status": inst['invoice_status'] or inst['status'],
                        "due_date": inst['due_date'].isoformat() if inst['due_date'] else None,
                        "paid_date": inst['paid_date'].isoformat() if inst['paid_date'] else None,
                        "error_message": inst['error_message']
                    }
                    for inst in instances
                ],
                "total": len(instances)
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting instances: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Helper Functions ====================

async def generate_recurrence_preview(
    recurring_id: str,
    schedule: RecurringInvoiceSchedule,
    start_date: date,
    end_date: Optional[date],
    max_occurrences: Optional[int],
    count: int
) -> List[Dict[str, Any]]:
    """Generate preview of recurring dates"""
    occurrences = []
    current_date = start_date
    occurrence_num = 1
    
    while len(occurrences) < count:
        # Check limits
        if end_date and current_date > end_date:
            break
        if max_occurrences and occurrence_num > max_occurrences:
            break
        
        occurrences.append({
            "occurrence_number": occurrence_num,
            "date": current_date.isoformat()
        })
        
        # Calculate next date
        current_date = calculate_next_occurrence(
            current_date,
            schedule.frequency.value,
            schedule.interval
        )
        occurrence_num += 1
    
    return occurrences

def calculate_next_occurrence(
    current_date: date,
    frequency: str,
    interval: int = 1
) -> date:
    """Calculate next occurrence date based on frequency"""
    if frequency == 'daily':
        return current_date + timedelta(days=interval)
    elif frequency == 'weekly':
        return current_date + timedelta(weeks=interval)
    elif frequency == 'biweekly':
        return current_date + timedelta(weeks=2 * interval)
    elif frequency == 'monthly':
        return current_date + relativedelta(months=interval)
    elif frequency == 'quarterly':
        return current_date + relativedelta(months=3 * interval)
    elif frequency == 'semi_annually':
        return current_date + relativedelta(months=6 * interval)
    elif frequency == 'annually':
        return current_date + relativedelta(years=interval)
    else:
        return current_date + timedelta(days=interval)

async def generate_invoice_from_recurring(
    conn: asyncpg.Connection,
    recurring: asyncpg.Record,
    occurrence_number: int
) -> str:
    """Generate an invoice from recurring configuration"""
    # Calculate amounts
    line_items = json.loads(recurring['line_items']) if recurring['line_items'] else []
    subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in line_items)
    tax = subtotal * (recurring['tax_rate'] / 100 if recurring['tax_rate'] else 0)
    total = subtotal + tax
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Create invoice
    invoice_id = str(uuid.uuid4())
    due_date = date.today() + timedelta(days=30)  # Default Net 30
    
    await conn.execute("""
        INSERT INTO invoices (
            id, invoice_number, customer_id,
            title, invoice_date, due_date,
            subtotal_cents, tax_cents, total_cents, balance_cents,
            line_items, notes, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """, uuid.UUID(invoice_id), invoice_number, recurring['customer_id'],
        f"Recurring Invoice #{occurrence_number}",
        date.today(), due_date,
        int(subtotal * 100), int(tax * 100),
        int(total * 100), int(total * 100),
        json.dumps(line_items), recurring['notes'], 'draft')
    
    # Create instance record
    await conn.execute("""
        INSERT INTO recurring_invoice_instances (
            recurring_invoice_id, invoice_id, occurrence_number,
            scheduled_date, generated_at, status
        ) VALUES ($1, $2, $3, $4, NOW(), 'generated')
    """, recurring['id'], uuid.UUID(invoice_id), occurrence_number,
        date.today())
    
    return invoice_id

async def generate_recurring_invoice_instance(recurring_id: str):
    """Background task to generate recurring invoice instance"""
    try:
        conn = await get_db_connection()
        try:
            invoice = await conn.fetchrow("""
                SELECT * FROM recurring_invoices WHERE id = $1
            """, uuid.UUID(recurring_id))
            
            if invoice and invoice['status'] == 'active':
                await generate_invoice_from_recurring(
                    conn,
                    invoice,
                    invoice['occurrences_generated'] + 1
                )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error generating recurring invoice instance: {str(e)} RETURNING *")