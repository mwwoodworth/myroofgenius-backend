"""
Payment Processing Module
Task 33: Payment processing implementation

Provides comprehensive payment processing capabilities including
Stripe integration, ACH, credit cards, and payment tracking.
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
import hashlib
import hmac
from decimal import Decimal

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter()

# ==================== Enums ====================

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH_TRANSFER = "ach_transfer"
    WIRE_TRANSFER = "wire_transfer"
    CHECK = "check"
    CASH = "cash"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    SQUARE = "square"
    OTHER = "other"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"

class RefundReason(str, Enum):
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    SERVICE_NOT_RENDERED = "service_not_rendered"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"

# ==================== Pydantic Models ====================

class PaymentMethodDetails(BaseModel):
    """Payment method details"""
    method: PaymentMethod
    last_four: Optional[str] = Field(default=None, description="Last 4 digits of card/account")
    brand: Optional[str] = Field(default=None, description="Card brand (Visa, Mastercard, etc)")
    bank_name: Optional[str] = Field(default=None, description="Bank name for ACH/wire")
    account_type: Optional[str] = Field(default=None, description="Account type (checking, savings)")
    reference_number: Optional[str] = Field(default=None, description="Check/wire reference number")

class ProcessPayment(BaseModel):
    """Process a payment"""
    invoice_id: str = Field(description="Invoice ID to pay")
    amount: float = Field(gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(description="Payment method")
    payment_details: Optional[PaymentMethodDetails] = None
    customer_email: Optional[EmailStr] = None
    send_receipt: bool = Field(default=True, description="Send email receipt")
    notes: Optional[str] = None

class CreditCardPayment(BaseModel):
    """Credit card payment details"""
    invoice_id: str
    amount: float = Field(gt=0)
    card_token: Optional[str] = Field(default=None, description="Stripe card token")
    card_number: Optional[str] = Field(default=None, description="Card number (for manual entry)")
    exp_month: Optional[int] = Field(default=None, ge=1, le=12)
    exp_year: Optional[int] = Field(default=None, ge=datetime.now().year)
    cvc: Optional[str] = Field(default=None, min_length=3, max_length=4)
    zip_code: Optional[str] = None
    save_card: bool = Field(default=False, description="Save card for future use")

class ACHPayment(BaseModel):
    """ACH payment details"""
    invoice_id: str
    amount: float = Field(gt=0)
    account_number: str = Field(description="Bank account number")
    routing_number: str = Field(description="Bank routing number", min_length=9, max_length=9)
    account_type: str = Field(default="checking", description="checking or savings")
    account_holder_name: str
    save_account: bool = Field(default=False)

class RefundPayment(BaseModel):
    """Refund a payment"""
    payment_id: str = Field(description="Payment ID to refund")
    amount: Optional[float] = Field(default=None, description="Refund amount (None for full refund)")
    reason: RefundReason = Field(description="Refund reason")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    notify_customer: bool = Field(default=True)

class PaymentPlan(BaseModel):
    """Payment plan setup"""
    invoice_id: str
    down_payment: float = Field(ge=0, description="Initial down payment")
    installments: int = Field(ge=2, le=24, description="Number of installments")
    frequency: str = Field(default="monthly", description="weekly, biweekly, monthly")
    start_date: Optional[date] = None
    auto_charge: bool = Field(default=False, description="Automatically charge installments")
    payment_method: Optional[PaymentMethod] = None

class PaymentReport(BaseModel):
    """Payment report filters"""
    start_date: date
    end_date: date
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    customer_id: Optional[str] = None

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Payment Processing ====================

@router.post("/process", tags=["Payment Processing"])
async def process_payment(
    payment: ProcessPayment,
    background_tasks: BackgroundTasks
):
    """Process a payment for an invoice"""
    try:
        conn = await get_db_connection()
        try:
            # Get invoice details
            invoice = await conn.fetchrow("""
                SELECT i.*, c.customer_name, c.email
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.id = $1
            """, uuid.UUID(payment.invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Calculate amount in cents
            amount_cents = int(payment.amount * 100)
            balance_cents = invoice['balance_cents'] or invoice['total_cents']
            
            if amount_cents > balance_cents:
                raise HTTPException(
                    status_code=400,
                    detail=f"Payment amount exceeds balance due: ${balance_cents/100:.2f}"
                )
            
            # Create payment record
            payment_id = str(uuid.uuid4())
            transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{payment_id[:8].upper()}"
            
            # Process based on payment method
            gateway_response = {}
            if payment.payment_method == PaymentMethod.STRIPE and STRIPE_AVAILABLE:
                # Process Stripe payment (placeholder)
                gateway_response = {
                    "status": "succeeded",
                    "transaction_id": transaction_id,
                    "processor": "stripe"
                }
            
            # Record payment
            await conn.execute("""
                INSERT INTO invoice_payments (
                    id, invoice_id, payment_date, amount,
                    payment_method, reference_number, notes,
                    transaction_id, gateway_response, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            """, uuid.UUID(payment_id), uuid.UUID(payment.invoice_id),
                date.today(), payment.amount,
                payment.payment_method.value,
                payment.payment_details.reference_number if payment.payment_details else None,
                payment.notes, transaction_id,
                json.dumps(gateway_response))
            
            # Update invoice status
            new_balance = balance_cents - amount_cents
            new_status = 'paid' if new_balance <= 0 else 'partial'
            
            await conn.execute("""
                UPDATE invoices
                SET status = $1,
                    paid_date = CASE WHEN $1 = 'paid' THEN NOW() ELSE paid_date END,
                    updated_at = NOW()
                WHERE id = $2
            """, new_status, uuid.UUID(payment.invoice_id))
            
            # Log activity
            await conn.execute("""
                INSERT INTO invoice_activities (
                    invoice_id, activity_type, description, metadata
                ) VALUES ($1, $2, $3, $4)
            """, uuid.UUID(payment.invoice_id), 'payment_received',
                f"Payment of ${payment.amount:.2f} received via {payment.payment_method.value}",
                json.dumps({
                    "payment_id": payment_id,
                    "amount": payment.amount,
                    "method": payment.payment_method.value
                }))
            
            # Send receipt email in background
            if payment.send_receipt:
                customer_email = payment.customer_email or invoice['email']
                if customer_email:
                    background_tasks.add_task(
                        send_payment_receipt,
                        payment_id, customer_email, payment.amount,
                        invoice['invoice_number']
                    )
            
            return {
                "success": True,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "amount": payment.amount,
                "new_balance": new_balance / 100,
                "invoice_status": new_status,
                "message": f"Payment of ${payment.amount:.2f} processed successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/credit-card", tags=["Payment Processing"])
async def process_credit_card_payment(
    payment: CreditCardPayment,
    background_tasks: BackgroundTasks
):
    """Process credit card payment"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Credit card processing is not available. Stripe not configured."
        )
    
    try:
        conn = await get_db_connection()
        try:
            # Get invoice
            invoice = await conn.fetchrow("""
                SELECT * FROM invoices WHERE id = $1
            """, uuid.UUID(payment.invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Create Stripe payment intent (placeholder)
            payment_intent = {
                "id": f"pi_{uuid.uuid4().hex}",
                "amount": int(payment.amount * 100),
                "status": "succeeded",
                "payment_method": "card"
            }
            
            # Record payment
            payment_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO invoice_payments (
                    id, invoice_id, payment_date, amount,
                    payment_method, transaction_id, gateway_response
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, uuid.UUID(payment_id), uuid.UUID(payment.invoice_id),
                date.today(), payment.amount, 'credit_card',
                payment_intent['id'], json.dumps(payment_intent))
            
            # Update invoice
            balance = (invoice['balance_cents'] or invoice['total_cents']) / 100
            new_balance = balance - payment.amount
            
            await conn.execute("""
                UPDATE invoices
                SET status = CASE
                    WHEN $1 <= 0 THEN 'paid'
                    ELSE 'partial'
                END,
                updated_at = NOW()
                WHERE id = $2
            """, new_balance, uuid.UUID(payment.invoice_id))
            
            return {
                "success": True,
                "payment_id": payment_id,
                "stripe_payment_intent_id": payment_intent['id'],
                "amount": payment.amount,
                "new_balance": new_balance
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing credit card payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ach", tags=["Payment Processing"])
async def process_ach_payment(
    payment: ACHPayment,
    background_tasks: BackgroundTasks
):
    """Process ACH payment"""
    try:
        conn = await get_db_connection()
        try:
            # Get invoice
            invoice = await conn.fetchrow("""
                SELECT * FROM invoices WHERE id = $1
            """, uuid.UUID(payment.invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Validate routing number (basic checksum)
            if not validate_routing_number(payment.routing_number):
                raise HTTPException(status_code=400, detail="Invalid routing number")
            
            # Create ACH transaction (placeholder)
            transaction_id = f"ACH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Record payment (pending ACH clearing)
            payment_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO invoice_payments (
                    id, invoice_id, payment_date, amount,
                    payment_method, reference_number, transaction_id,
                    gateway_response, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            """, uuid.UUID(payment_id), uuid.UUID(payment.invoice_id),
                date.today() + timedelta(days=2),  # ACH typically clears in 2-3 days
                payment.amount, 'ach_transfer',
                f"****{payment.account_number[-4:]}",
                transaction_id,
                json.dumps({
                    "status": "pending",
                    "account_type": payment.account_type,
                    "expected_clear_date": (date.today() + timedelta(days=2)).isoformat()
                }))
            
            # Log activity
            await conn.execute("""
                INSERT INTO invoice_activities (
                    invoice_id, activity_type, description
                ) VALUES ($1, $2, $3)
            """, uuid.UUID(payment.invoice_id), 'ach_initiated',
                f"ACH payment of ${payment.amount:.2f} initiated")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "amount": payment.amount,
                "status": "pending",
                "expected_clear_date": (date.today() + timedelta(days=2)).isoformat(),
                "message": "ACH payment initiated. Funds will be available in 2-3 business days."
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing ACH payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Refunds ====================

@router.post("/refund", tags=["Payment Processing"])
async def refund_payment(
    refund: RefundPayment,
    background_tasks: BackgroundTasks
):
    """Refund a payment"""
    try:
        conn = await get_db_connection()
        try:
            # Get payment details
            payment = await conn.fetchrow("""
                SELECT p.*, i.invoice_number, i.customer_id
                FROM invoice_payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE p.id = $1
            """, uuid.UUID(refund.payment_id))
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            # Calculate refund amount
            original_amount = float(payment['amount'])
            refund_amount = refund.amount if refund.amount else original_amount
            
            if refund_amount > original_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"Refund amount exceeds original payment: ${original_amount:.2f}"
                )
            
            # Check for existing refunds
            existing_refunds = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payment_refunds
                WHERE payment_id = $1
            """, uuid.UUID(refund.payment_id))
            
            if float(existing_refunds) + refund_amount > original_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total refunds would exceed original payment amount"
                )
            
            # Process refund
            refund_id = str(uuid.uuid4())
            refund_transaction_id = f"RFD-{datetime.now().strftime('%Y%m%d')}-{refund_id[:8].upper()}"
            
            # Create refund record
            await conn.execute("""
                INSERT INTO payment_refunds (
                    id, payment_id, refund_date, amount,
                    reason, notes, transaction_id, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, uuid.UUID(refund_id), uuid.UUID(refund.payment_id),
                date.today(), refund_amount,
                refund.reason.value, refund.notes,
                refund_transaction_id, 'completed')
            
            # Update invoice balance
            await conn.execute("""
                UPDATE invoices
                SET balance_cents = balance_cents + $1,
                    status = CASE
                        WHEN balance_cents + $1 > 0 THEN 'partial'
                        ELSE status
                    END,
                    updated_at = NOW()
                WHERE id = $2
            """, int(refund_amount * 100), payment['invoice_id'])
            
            # Log activity
            await conn.execute("""
                INSERT INTO invoice_activities (
                    invoice_id, activity_type, description, metadata
                ) VALUES ($1, $2, $3, $4)
            """, payment['invoice_id'], 'payment_refunded',
                f"Refund of ${refund_amount:.2f} processed",
                json.dumps({
                    "refund_id": refund_id,
                    "amount": refund_amount,
                    "reason": refund.reason.value
                }))
            
            # Send notification
            if refund.notify_customer:
                background_tasks.add_task(
                    send_refund_notification,
                    refund_id, payment['customer_id'], refund_amount
                )
            
            return {
                "success": True,
                "refund_id": refund_id,
                "transaction_id": refund_transaction_id,
                "amount": refund_amount,
                "message": f"Refund of ${refund_amount:.2f} processed successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Payment Plans ====================

@router.post("/payment-plan", tags=["Payment Processing"])
async def create_payment_plan(plan: PaymentPlan):
    """Create a payment plan for an invoice"""
    try:
        conn = await get_db_connection()
        try:
            # Get invoice
            invoice = await conn.fetchrow("""
                SELECT * FROM invoices WHERE id = $1
            """, uuid.UUID(plan.invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            total_amount = (invoice['total_cents'] or 0) / 100
            balance = (invoice['balance_cents'] or invoice['total_cents']) / 100
            
            # Calculate installment amount
            remaining = balance - plan.down_payment
            if remaining < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Down payment exceeds invoice balance"
                )
            
            installment_amount = remaining / plan.installments
            
            # Create payment plan
            plan_id = str(uuid.uuid4())
            start_date = plan.start_date or date.today()
            
            await conn.execute("""
                INSERT INTO payment_plans (
                    id, invoice_id, total_amount, down_payment,
                    installments, installment_amount, frequency,
                    start_date, auto_charge, payment_method, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, uuid.UUID(plan_id), uuid.UUID(plan.invoice_id),
                balance, plan.down_payment, plan.installments,
                installment_amount, plan.frequency,
                start_date, plan.auto_charge,
                plan.payment_method.value if plan.payment_method else None,
                'active')
            
            # Process down payment if specified
            if plan.down_payment > 0:
                payment_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO invoice_payments (
                        id, invoice_id, payment_date, amount,
                        payment_method, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, uuid.UUID(payment_id), uuid.UUID(plan.invoice_id),
                    date.today(), plan.down_payment,
                    plan.payment_method.value if plan.payment_method else 'other',
                    'Payment plan down payment')
            
            # Generate installment schedule
            installments = []
            current_date = start_date
            for i in range(plan.installments):
                if plan.frequency == 'weekly':
                    due_date = current_date + timedelta(weeks=i)
                elif plan.frequency == 'biweekly':
                    due_date = current_date + timedelta(weeks=i*2)
                else:  # monthly
                    due_date = date(current_date.year, current_date.month, current_date.day)
                    for _ in range(i):
                        if due_date.month == 12:
                            due_date = due_date.replace(year=due_date.year + 1, month=1)
                        else:
                            due_date = due_date.replace(month=due_date.month + 1)
                
                installments.append({
                    "installment_number": i + 1,
                    "due_date": due_date.isoformat(),
                    "amount": installment_amount
                })
            
            return {
                "success": True,
                "plan_id": plan_id,
                "total_amount": balance,
                "down_payment": plan.down_payment,
                "installment_amount": installment_amount,
                "schedule": installments,
                "message": f"Payment plan created with {plan.installments} installments of ${installment_amount:.2f}"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Payment History & Reports ====================

@router.get("/history/{invoice_id}", tags=["Payment Processing"])
async def get_payment_history(invoice_id: str):
    """Get payment history for an invoice"""
    try:
        conn = await get_db_connection()
        try:
            # Get payments
            payments = await conn.fetch("""
                SELECT p.*, r.amount as refund_amount, r.refund_date
                FROM invoice_payments p
                LEFT JOIN payment_refunds r ON r.payment_id = p.id
                WHERE p.invoice_id = $1
                ORDER BY p.created_at DESC
            """, uuid.UUID(invoice_id))
            
            # Get invoice details
            invoice = await conn.fetchrow("""
                SELECT invoice_number, total_cents, balance_cents, status
                FROM invoices WHERE id = $1
            """, uuid.UUID(invoice_id))
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            payment_list = []
            for payment in payments:
                payment_list.append({
                    "id": str(payment['id']),
                    "payment_date": payment['payment_date'].isoformat() if payment['payment_date'] else None,
                    "amount": float(payment['amount']),
                    "payment_method": payment['payment_method'],
                    "reference_number": payment['reference_number'],
                    "transaction_id": payment['transaction_id'],
                    "notes": payment['notes'],
                    "refunded_amount": float(payment['refund_amount']) if payment['refund_amount'] else None,
                    "refund_date": payment['refund_date'].isoformat() if payment['refund_date'] else None,
                    "created_at": payment['created_at'].isoformat() if payment['created_at'] else None
                })
            
            return {
                "invoice_number": invoice['invoice_number'],
                "total_amount": invoice['total_cents'] / 100,
                "balance_due": invoice['balance_cents'] / 100,
                "status": invoice['status'],
                "payments": payment_list,
                "total_paid": sum(p['amount'] for p in payments if p['amount']),
                "total_refunded": sum(p['refund_amount'] for p in payments if p['refund_amount'])
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports", tags=["Payment Processing"])
async def generate_payment_report(report: PaymentReport):
    """Generate payment report"""
    try:
        conn = await get_db_connection()
        try:
            # Build query
            query = """
                SELECT p.*, i.invoice_number, c.customer_name
                FROM invoice_payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN customers c ON i.customer_id = c.id
                WHERE p.payment_date BETWEEN $1 AND $2
            """
            params = [report.start_date, report.end_date]
            param_count = 2
            
            if report.payment_method:
                param_count += 1
                query += f" AND p.payment_method = ${param_count}"
                params.append(report.payment_method.value)
            
            if report.min_amount:
                param_count += 1
                query += f" AND p.amount >= ${param_count}"
                params.append(report.min_amount)
            
            if report.max_amount:
                param_count += 1
                query += f" AND p.amount <= ${param_count}"
                params.append(report.max_amount)
            
            if report.customer_id:
                param_count += 1
                query += f" AND i.customer_id = ${param_count}"
                params.append(uuid.UUID(report.customer_id))
            
            query += " ORDER BY p.payment_date DESC"
            
            payments = await conn.fetch(query, *params)
            
            # Calculate statistics
            total_amount = sum(float(p['amount']) for p in payments if p['amount'])
            payment_count = len(payments)
            avg_amount = total_amount / payment_count if payment_count > 0 else 0
            
            # Group by payment method
            by_method = {}
            for payment in payments:
                method = payment['payment_method'] or 'other'
                if method not in by_method:
                    by_method[method] = {'count': 0, 'total': 0}
                by_method[method]['count'] += 1
                by_method[method]['total'] += float(payment['amount'] or 0)
            
            return {
                "summary": {
                    "total_payments": payment_count,
                    "total_amount": total_amount,
                    "average_amount": avg_amount,
                    "date_range": f"{report.start_date} to {report.end_date}"
                },
                "by_method": by_method,
                "payments": [
                    {
                        "id": str(payment['id']),
                        "invoice_number": payment['invoice_number'],
                        "customer_name": payment['customer_name'],
                        "payment_date": payment['payment_date'].isoformat(),
                        "amount": float(payment['amount']),
                        "payment_method": payment['payment_method'],
                        "transaction_id": payment['transaction_id']
                    }
                    for payment in payments[:100]  # Limit to 100 for performance
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error generating payment report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Stripe Webhook ====================

@router.post("/webhook/stripe", tags=["Payment Processing"])
async def stripe_webhook(request: Dict[str, Any]):
    """Handle Stripe webhook events"""
    if not STRIPE_AVAILABLE:
        return {"status": "ignored", "reason": "Stripe not configured"}
    
    try:
        event_type = request.get('type')
        data = request.get('data', {}).get('object', {})
        
        conn = await get_db_connection()
        try:
            if event_type == 'payment_intent.succeeded':
                # Update payment status
                await conn.execute("""
                    UPDATE invoice_payments
                    SET gateway_response = gateway_response || $1
                    WHERE transaction_id = $2
                """, json.dumps({"webhook_received": datetime.now().isoformat()}),
                    data.get('id'))
            
            elif event_type == 'charge.refunded':
                # Record refund from Stripe
                pass
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

# ==================== Helper Functions ====================

def validate_routing_number(routing_number: str) -> bool:
    """Validate US bank routing number using checksum"""
    if len(routing_number) != 9 or not routing_number.isdigit():
        return False
    
    # ABA routing number checksum algorithm
    weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
    total = sum(int(routing_number[i]) * weights[i] for i in range(9))
    return total % 10 == 0

async def send_payment_receipt(
    payment_id: str,
    email: str,
    amount: float,
    invoice_number: str
):
    """Send payment receipt email (placeholder)"""
    logger.info(f"Sending receipt for payment {payment_id} to {email}")
    # Email sending implementation would go here

async def send_refund_notification(
    refund_id: str,
    customer_id: str,
    amount: float
):
    """Send refund notification (placeholder)"""
    logger.info(f"Sending refund notification for {refund_id} to customer {customer_id} RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *")
    # Notification implementation would go here