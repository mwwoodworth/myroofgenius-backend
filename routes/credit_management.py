"""
Credit Management Module
Task 36: Credit management implementation

Comprehensive credit management system including credit limits,
credit checks, aging reports, and credit risk assessment.
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
from decimal import Decimal

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

router = APIRouter()

# ==================== Enums ====================

class CreditStatus(str, Enum):
    EXCELLENT = "excellent"  # 750+
    GOOD = "good"           # 700-749
    FAIR = "fair"           # 650-699
    POOR = "poor"           # 600-649
    VERY_POOR = "very_poor" # Below 600
    NO_CREDIT = "no_credit"  # No credit history

class PaymentBehavior(str, Enum):
    ON_TIME = "on_time"
    OCCASIONALLY_LATE = "occasionally_late"
    FREQUENTLY_LATE = "frequently_late"
    DELINQUENT = "delinquent"
    DEFAULT = "default"

class CreditAction(str, Enum):
    INCREASE_LIMIT = "increase_limit"
    DECREASE_LIMIT = "decrease_limit"
    SUSPEND = "suspend"
    REINSTATE = "reinstate"
    WRITE_OFF = "write_off"
    SEND_TO_COLLECTIONS = "send_to_collections"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNACCEPTABLE = "unacceptable"

# ==================== Pydantic Models ====================

class CustomerCredit(BaseModel):
    """Customer credit information"""
    customer_id: str
    credit_limit: float = Field(ge=0, description="Credit limit amount")
    current_balance: float = Field(description="Current outstanding balance")
    available_credit: float = Field(description="Available credit amount")
    credit_status: CreditStatus
    payment_behavior: PaymentBehavior
    risk_level: RiskLevel
    days_sales_outstanding: int = Field(ge=0, description="Average DSO")
    last_payment_date: Optional[date]
    last_credit_review: Optional[date]
    notes: Optional[str]

class SetCreditLimit(BaseModel):
    """Set or update credit limit"""
    customer_id: str
    credit_limit: float = Field(ge=0, description="New credit limit")
    effective_date: Optional[date] = Field(default=None, description="Effective date")
    reason: str = Field(description="Reason for change")
    approved_by: Optional[str] = Field(default=None, description="Approver name/ID")
    notes: Optional[str] = None

class CreditApplication(BaseModel):
    """Credit application for new or existing customers"""
    customer_id: Optional[str] = None
    company_name: str
    tax_id: Optional[str] = None
    annual_revenue: Optional[float] = None
    years_in_business: Optional[int] = None
    requested_credit_limit: float = Field(gt=0)
    trade_references: List[Dict[str, Any]] = Field(default=[])
    bank_references: List[Dict[str, Any]] = Field(default=[])
    financial_statements: Optional[Dict[str, Any]] = None
    authorized_signature: bool = Field(default=False)

class CreditCheck(BaseModel):
    """Credit check request"""
    customer_id: str
    check_type: str = Field(description="internal, bureau, comprehensive")
    include_trade_references: bool = Field(default=False)
    include_bank_verification: bool = Field(default=False)
    include_financial_analysis: bool = Field(default=False)
    bureau_report_type: Optional[str] = Field(default=None, description="Equifax, Experian, D&B")

class AgingReport(BaseModel):
    """Accounts receivable aging report"""
    as_of_date: date = Field(default_factory=date.today)
    customer_id: Optional[str] = None
    include_zero_balance: bool = Field(default=False)
    group_by: str = Field(default="customer", description="customer, invoice, age_bucket")

class CreditAdjustment(BaseModel):
    """Credit adjustment request"""
    customer_id: str
    adjustment_type: str = Field(description="credit_memo, debit_memo, write_off")
    amount: float = Field(description="Adjustment amount")
    invoice_id: Optional[str] = None
    reason: str
    approved_by: Optional[str] = None
    notes: Optional[str] = None

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Credit Limits ====================

@router.post("/set-limit", tags=["Credit Management"])
async def set_credit_limit(
    request: SetCreditLimit,
    background_tasks: BackgroundTasks
):
    """Set or update customer credit limit"""
    try:
        conn = await get_db_connection()
        try:
            # Check if customer exists
            customer = await conn.fetchrow("""
                SELECT * FROM customers WHERE id = $1
            """, uuid.UUID(request.customer_id))
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Create or update credit profile
            credit_id = str(uuid.uuid4())
            effective_date = request.effective_date or date.today()
            
            # Check for existing credit profile
            existing = await conn.fetchrow("""
                SELECT * FROM customer_credit_profiles
                WHERE customer_id = $1
            """, uuid.UUID(request.customer_id))
            
            if existing:
                # Update existing profile
                old_limit = existing['credit_limit']
                
                await conn.execute("""
                    UPDATE customer_credit_profiles
                    SET credit_limit = $2,
                        available_credit = available_credit + ($2 - credit_limit),
                        last_review_date = $3,
                        updated_at = NOW()
                    WHERE customer_id = $1
                """, uuid.UUID(request.customer_id), request.credit_limit, effective_date)
                
                # Log the change
                await conn.execute("""
                    INSERT INTO credit_limit_history (
                        customer_id, old_limit, new_limit,
                        effective_date, reason, approved_by, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, uuid.UUID(request.customer_id), old_limit, request.credit_limit,
                    effective_date, request.reason, request.approved_by, request.notes)
                
                action = "updated"
            else:
                # Create new profile
                await conn.execute("""
                    INSERT INTO customer_credit_profiles (
                        id, customer_id, credit_limit, current_balance,
                        available_credit, credit_status, payment_behavior,
                        risk_level, last_review_date
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, uuid.UUID(credit_id), uuid.UUID(request.customer_id),
                    request.credit_limit, 0, request.credit_limit,
                    CreditStatus.NO_CREDIT.value, PaymentBehavior.ON_TIME.value,
                    RiskLevel.MEDIUM.value, effective_date)
                
                action = "created"
            
            # Send notification
            background_tasks.add_task(
                notify_credit_limit_change,
                request.customer_id,
                request.credit_limit,
                action
            )
            
            return {
                "success": True,
                "customer_id": request.customer_id,
                "credit_limit": request.credit_limit,
                "effective_date": effective_date.isoformat(),
                "message": f"Credit limit {action} successfully"
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting credit limit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{customer_id}", tags=["Credit Management"])
async def get_credit_profile(customer_id: str):
    """Get customer credit profile"""
    try:
        conn = await get_db_connection()
        try:
            # Get credit profile
            profile = await conn.fetchrow("""
                SELECT cp.*, c.customer_name, c.email
                FROM customer_credit_profiles cp
                JOIN customers c ON cp.customer_id = c.id
                WHERE cp.customer_id = $1
            """, uuid.UUID(customer_id))
            
            if not profile:
                # Return default profile for customer without credit
                customer = await conn.fetchrow("""
                    SELECT customer_name, email FROM customers WHERE id = $1
                """, uuid.UUID(customer_id))
                
                if not customer:
                    raise HTTPException(status_code=404, detail="Customer not found")
                
                return {
                    "customer_id": customer_id,
                    "customer_name": customer['customer_name'],
                    "credit_limit": 0,
                    "current_balance": 0,
                    "available_credit": 0,
                    "credit_status": "no_credit",
                    "payment_behavior": "no_history",
                    "risk_level": "unknown"
                }
            
            # Calculate current balance from outstanding invoices
            balance = await conn.fetchval("""
                SELECT COALESCE(SUM(balance_cents), 0) / 100.0
                FROM invoices
                WHERE customer_id = $1 AND status NOT IN ('paid', 'cancelled')
            """, uuid.UUID(customer_id))
            
            # Get payment statistics
            payment_stats = await conn.fetchrow("""
                SELECT 
                    AVG(CASE 
                        WHEN paid_date IS NOT NULL 
                        THEN paid_date - due_date 
                        ELSE CURRENT_DATE - due_date 
                    END) as avg_days_to_pay,
                    COUNT(CASE WHEN paid_date > due_date THEN 1 END) as late_payments,
                    COUNT(CASE WHEN status = 'paid' THEN 1 END) as total_paid,
                    MAX(paid_date) as last_payment_date
                FROM invoices
                WHERE customer_id = $1
            """, uuid.UUID(customer_id))
            
            # Get credit history
            history = await conn.fetch("""
                SELECT * FROM credit_limit_history
                WHERE customer_id = $1
                ORDER BY effective_date DESC
                LIMIT 5
            """, uuid.UUID(customer_id))
            
            return {
                "customer_id": customer_id,
                "customer_name": profile['customer_name'],
                "email": profile['email'],
                "credit_limit": float(profile['credit_limit']) if profile['credit_limit'] else 0,
                "current_balance": float(balance),
                "available_credit": float(profile['credit_limit'] or 0) - float(balance),
                "credit_status": profile['credit_status'],
                "payment_behavior": profile['payment_behavior'],
                "risk_level": profile['risk_level'],
                "days_sales_outstanding": int(payment_stats['avg_days_to_pay']) if payment_stats['avg_days_to_pay'] else 0,
                "late_payment_count": payment_stats['late_payments'] or 0,
                "total_invoices_paid": payment_stats['total_paid'] or 0,
                "last_payment_date": payment_stats['last_payment_date'].isoformat() if payment_stats['last_payment_date'] else None,
                "last_review_date": profile['last_review_date'].isoformat() if profile['last_review_date'] else None,
                "credit_history": [
                    {
                        "date": h['effective_date'].isoformat(),
                        "old_limit": float(h['old_limit']) if h['old_limit'] else 0,
                        "new_limit": float(h['new_limit']) if h['new_limit'] else 0,
                        "reason": h['reason']
                    }
                    for h in history
                ]
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credit profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Credit Checks ====================

@router.post("/check", tags=["Credit Management"])
async def perform_credit_check(
    request: CreditCheck,
    background_tasks: BackgroundTasks
):
    """Perform credit check on customer"""
    try:
        conn = await get_db_connection()
        try:
            check_id = str(uuid.uuid4())
            
            # Get customer information
            customer = await conn.fetchrow("""
                SELECT * FROM customers WHERE id = $1
            """, uuid.UUID(request.customer_id))
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Internal credit check
            internal_score = await calculate_internal_credit_score(
                conn, uuid.UUID(request.customer_id)
            )
            
            results = {
                "check_id": check_id,
                "customer_id": request.customer_id,
                "check_date": datetime.now().isoformat(),
                "internal_score": internal_score
            }
            
            # Bureau check (placeholder)
            if request.check_type in ['bureau', 'comprehensive']:
                bureau_score = 700  # Placeholder
                results['bureau_score'] = bureau_score
                results['bureau_report'] = {
                    "provider": request.bureau_report_type or "Equifax",
                    "report_date": date.today().isoformat(),
                    "score": bureau_score,
                    "risk_level": get_risk_level_from_score(bureau_score)
                }
            
            # Trade references check
            if request.include_trade_references:
                trade_refs = await conn.fetch("""
                    SELECT * FROM customer_trade_references
                    WHERE customer_id = $1
                """, uuid.UUID(request.customer_id))
                
                results['trade_references'] = [
                    {
                        "company": ref['company_name'],
                        "contact": ref['contact_person'],
                        "payment_history": ref['payment_history'],
                        "credit_limit": float(ref['credit_limit']) if ref['credit_limit'] else None
                    }
                    for ref in trade_refs
                ]
            
            # Calculate recommendation
            avg_score = internal_score
            if 'bureau_score' in results:
                avg_score = (internal_score + results['bureau_score']) / 2
            
            risk_level = get_risk_level_from_score(avg_score)
            recommended_limit = calculate_recommended_credit_limit(
                avg_score,
                customer.get('annual_revenue', 0)
            )
            
            results['recommendation'] = {
                "overall_score": avg_score,
                "risk_level": risk_level,
                "recommended_credit_limit": recommended_limit,
                "decision": "approve" if avg_score >= 650 else "review" if avg_score >= 600 else "decline"
            }
            
            # Save credit check record
            await conn.execute("""
                INSERT INTO credit_checks (
                    id, customer_id, check_type, check_date,
                    internal_score, bureau_score, risk_level,
                    recommended_limit, decision, report_data
                ) VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7, $8, $9)
            """, uuid.UUID(check_id), uuid.UUID(request.customer_id),
                request.check_type, internal_score,
                results.get('bureau_score'), risk_level,
                recommended_limit, results['recommendation']['decision'],
                json.dumps(results))
            
            return results
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing credit check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Aging Reports ====================

@router.post("/aging-report", tags=["Credit Management"])
async def generate_aging_report(request: AgingReport):
    """Generate accounts receivable aging report"""
    try:
        conn = await get_db_connection()
        try:
            # Build query
            query = """
                SELECT 
                    i.id as invoice_id,
                    i.invoice_number,
                    i.customer_id,
                    c.customer_name,
                    i.invoice_date,
                    i.due_date,
                    i.total_cents / 100.0 as total_amount,
                    i.balance_cents / 100.0 as balance_due,
                    CURRENT_DATE - i.due_date as days_overdue,
                    CASE 
                        WHEN CURRENT_DATE - i.due_date <= 0 THEN 'current'
                        WHEN CURRENT_DATE - i.due_date <= 30 THEN '1-30'
                        WHEN CURRENT_DATE - i.due_date <= 60 THEN '31-60'
                        WHEN CURRENT_DATE - i.due_date <= 90 THEN '61-90'
                        ELSE 'over_90'
                    END as age_bucket
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.due_date <= $1
                    AND i.status NOT IN ('paid', 'cancelled')
            """
            params = [request.as_of_date]
            
            if request.customer_id:
                query += " AND i.customer_id = $2"
                params.append(uuid.UUID(request.customer_id))
            
            if not request.include_zero_balance:
                query += f" AND i.balance_cents > 0"
            
            query += " ORDER BY c.customer_name, i.due_date"
            
            invoices = await conn.fetch(query, *params)
            
            # Process results based on grouping
            if request.group_by == "age_bucket":
                buckets = {'current': [], '1-30': [], '31-60': [], '61-90': [], 'over_90': []}
                bucket_totals = {'current': 0, '1-30': 0, '31-60': 0, '61-90': 0, 'over_90': 0}
                
                for inv in invoices:
                    bucket = inv['age_bucket']
                    buckets[bucket].append({
                        "invoice_number": inv['invoice_number'],
                        "customer_name": inv['customer_name'],
                        "due_date": inv['due_date'].isoformat(),
                        "balance_due": float(inv['balance_due'])
                    })
                    bucket_totals[bucket] += float(inv['balance_due'])
                
                return {
                    "report_date": request.as_of_date.isoformat(),
                    "grouping": "age_bucket",
                    "summary": {
                        "total_outstanding": sum(bucket_totals.values()),
                        "current": bucket_totals['current'],
                        "1_30_days": bucket_totals['1-30'],
                        "31_60_days": bucket_totals['31-60'],
                        "61_90_days": bucket_totals['61-90'],
                        "over_90_days": bucket_totals['over_90']
                    },
                    "details": buckets
                }
            
            elif request.group_by == "customer":
                customers = {}
                
                for inv in invoices:
                    cust_id = str(inv['customer_id'])
                    if cust_id not in customers:
                        customers[cust_id] = {
                            "customer_name": inv['customer_name'],
                            "invoices": [],
                            "total_due": 0,
                            "current": 0,
                            "overdue_1_30": 0,
                            "overdue_31_60": 0,
                            "overdue_61_90": 0,
                            "overdue_90_plus": 0
                        }
                    
                    customers[cust_id]['invoices'].append({
                        "invoice_number": inv['invoice_number'],
                        "due_date": inv['due_date'].isoformat(),
                        "days_overdue": inv['days_overdue'],
                        "balance_due": float(inv['balance_due'])
                    })
                    
                    customers[cust_id]['total_due'] += float(inv['balance_due'])
                    
                    if inv['age_bucket'] == 'current':
                        customers[cust_id]['current'] += float(inv['balance_due'])
                    elif inv['age_bucket'] == '1-30':
                        customers[cust_id]['overdue_1_30'] += float(inv['balance_due'])
                    elif inv['age_bucket'] == '31-60':
                        customers[cust_id]['overdue_31_60'] += float(inv['balance_due'])
                    elif inv['age_bucket'] == '61-90':
                        customers[cust_id]['overdue_61_90'] += float(inv['balance_due'])
                    else:
                        customers[cust_id]['overdue_90_plus'] += float(inv['balance_due'])
                
                return {
                    "report_date": request.as_of_date.isoformat(),
                    "grouping": "customer",
                    "customers": list(customers.values()),
                    "summary": {
                        "total_customers": len(customers),
                        "total_outstanding": sum(c['total_due'] for c in customers.values())
                    }
                }
            
            else:  # Default invoice-level detail
                return {
                    "report_date": request.as_of_date.isoformat(),
                    "grouping": "invoice",
                    "invoices": [
                        {
                            "invoice_number": inv['invoice_number'],
                            "customer_name": inv['customer_name'],
                            "invoice_date": inv['invoice_date'].isoformat(),
                            "due_date": inv['due_date'].isoformat(),
                            "days_overdue": inv['days_overdue'],
                            "age_bucket": inv['age_bucket'],
                            "total_amount": float(inv['total_amount']),
                            "balance_due": float(inv['balance_due'])
                        }
                        for inv in invoices
                    ],
                    "summary": {
                        "total_invoices": len(invoices),
                        "total_outstanding": sum(float(inv['balance_due']) for inv in invoices)
                    }
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error generating aging report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Credit Actions ====================

@router.post("/action", tags=["Credit Management"])
async def perform_credit_action(
    customer_id: str,
    action: CreditAction,
    amount: Optional[float] = None,
    reason: str = Query(...),
    approved_by: Optional[str] = None
):
    """Perform credit management action"""
    try:
        conn = await get_db_connection()
        try:
            # Verify customer
            customer = await conn.fetchrow("""
                SELECT * FROM customers WHERE id = $1
            """, uuid.UUID(customer_id))
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            action_id = str(uuid.uuid4())
            
            if action == CreditAction.SUSPEND:
                # Suspend credit
                await conn.execute("""
                    UPDATE customer_credit_profiles
                    SET credit_status = 'suspended',
                        available_credit = 0,
                        updated_at = NOW()
                    WHERE customer_id = $1
                """, uuid.UUID(customer_id))
                
                message = "Customer credit suspended"
            
            elif action == CreditAction.REINSTATE:
                # Reinstate credit
                await conn.execute("""
                    UPDATE customer_credit_profiles
                    SET credit_status = 'good',
                        available_credit = credit_limit - current_balance,
                        updated_at = NOW()
                    WHERE customer_id = $1
                """, uuid.UUID(customer_id))
                
                message = "Customer credit reinstated"
            
            elif action == CreditAction.WRITE_OFF:
                # Write off bad debt
                if not amount:
                    raise HTTPException(status_code=400, detail="Amount required for write-off")
                
                await conn.execute("""
                    INSERT INTO credit_write_offs (
                        id, customer_id, amount, reason,
                        write_off_date, approved_by
                    ) VALUES ($1, $2, $3, $4, NOW(), $5)
                """, uuid.UUID(action_id), uuid.UUID(customer_id),
                    amount, reason, approved_by)
                
                message = f"Written off ${amount:.2f}"
            
            elif action == CreditAction.SEND_TO_COLLECTIONS:
                # Send to collections
                await conn.execute("""
                    UPDATE customers
                    SET status = 'collections',
                        updated_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(customer_id))
                
                # Create collections record
                await conn.execute("""
                    INSERT INTO collections_accounts (
                        customer_id, sent_date, total_amount,
                        reason, status
                    ) VALUES ($1, NOW(), $2, $3, 'active')
                """, uuid.UUID(customer_id),
                    amount or 0, reason)
                
                message = "Account sent to collections"
            
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
            
            # Log action
            await conn.execute("""
                INSERT INTO credit_actions_log (
                    id, customer_id, action_type, amount,
                    reason, approved_by, action_date
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """, uuid.UUID(action_id), uuid.UUID(customer_id),
                action.value, amount, reason, approved_by)
            
            return {
                "success": True,
                "action_id": action_id,
                "customer_id": customer_id,
                "action": action.value,
                "message": message
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing credit action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Risk Assessment ====================

@router.get("/risk-assessment", tags=["Credit Management"])
async def get_risk_assessment(
    min_balance: Optional[float] = None,
    risk_level: Optional[RiskLevel] = None
):
    """Get credit risk assessment for all customers"""
    try:
        conn = await get_db_connection()
        try:
            query = """
                SELECT 
                    c.id,
                    c.customer_name,
                    cp.credit_limit,
                    cp.current_balance,
                    cp.credit_status,
                    cp.risk_level,
                    COUNT(DISTINCT i.id) as total_invoices,
                    SUM(CASE WHEN i.status = 'overdue' THEN 1 ELSE 0 END) as overdue_invoices,
                    SUM(i.balance_cents) / 100.0 as total_outstanding,
                    MAX(CURRENT_DATE - i.due_date) as max_days_overdue
                FROM customers c
                LEFT JOIN customer_credit_profiles cp ON c.id = cp.customer_id
                LEFT JOIN invoices i ON c.id = i.customer_id AND i.status NOT IN ('paid', 'cancelled')
                WHERE 1=1
            """
            params = []
            
            if min_balance:
                query += " AND (i.balance_cents / 100.0) >= $1"
                params.append(min_balance)
            
            if risk_level:
                param_num = len(params) + 1
                query += f" AND cp.risk_level = ${param_num}"
                params.append(risk_level.value)
            
            query += " GROUP BY c.id, c.customer_name, cp.credit_limit, cp.current_balance, cp.credit_status, cp.risk_level"
            query += " HAVING SUM(i.balance_cents) > 0 OR cp.credit_limit > 0"
            query += " ORDER BY total_outstanding DESC"
            
            customers = await conn.fetch(query, *params)
            
            high_risk = []
            medium_risk = []
            low_risk = []
            
            for customer in customers:
                risk_score = calculate_risk_score(
                    customer['total_outstanding'],
                    customer['credit_limit'],
                    customer['max_days_overdue'],
                    customer['overdue_invoices']
                )
                
                customer_risk = {
                    "customer_id": str(customer['id']),
                    "customer_name": customer['customer_name'],
                    "credit_limit": float(customer['credit_limit']) if customer['credit_limit'] else 0,
                    "total_outstanding": float(customer['total_outstanding']) if customer['total_outstanding'] else 0,
                    "overdue_invoices": customer['overdue_invoices'] or 0,
                    "max_days_overdue": customer['max_days_overdue'] or 0,
                    "risk_score": risk_score,
                    "risk_level": customer['risk_level'] or get_risk_level_from_score(risk_score)
                }
                
                if risk_score >= 70:
                    high_risk.append(customer_risk)
                elif risk_score >= 40:
                    medium_risk.append(customer_risk)
                else:
                    low_risk.append(customer_risk)
            
            return {
                "assessment_date": datetime.now().isoformat(),
                "summary": {
                    "total_customers": len(customers),
                    "high_risk_count": len(high_risk),
                    "medium_risk_count": len(medium_risk),
                    "low_risk_count": len(low_risk),
                    "total_exposure": sum(float(c['total_outstanding'] or 0) for c in customers)
                },
                "high_risk_customers": high_risk[:10],  # Top 10
                "medium_risk_customers": medium_risk[:10],
                "low_risk_customers": low_risk[:10]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting risk assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Helper Functions ====================

async def calculate_internal_credit_score(
    conn: asyncpg.Connection,
    customer_id: uuid.UUID
) -> int:
    """Calculate internal credit score based on payment history"""
    # Get payment history
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_invoices,
            COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_invoices,
            COUNT(CASE WHEN paid_date > due_date THEN 1 END) as late_payments,
            AVG(CASE WHEN paid_date IS NOT NULL THEN paid_date - due_date ELSE 0 END) as avg_days_to_pay,
            MAX(total_cents) / 100.0 as max_invoice_amount,
            SUM(CASE WHEN status = 'overdue' THEN balance_cents ELSE 0 END) / 100.0 as overdue_amount
        FROM invoices
        WHERE customer_id = $1
    """, customer_id)
    
    # Base score
    score = 700
    
    # Adjust based on payment history
    if stats['total_invoices'] > 0:
        # Payment rate
        payment_rate = (stats['paid_invoices'] / stats['total_invoices']) * 100
        if payment_rate >= 95:
            score += 50
        elif payment_rate >= 85:
            score += 25
        elif payment_rate < 70:
            score -= 50
        
        # Late payment penalty
        if stats['late_payments']:
            late_rate = (stats['late_payments'] / stats['paid_invoices']) * 100 if stats['paid_invoices'] else 0
            score -= int(late_rate * 2)  # -2 points per percentage
        
        # Average days to pay
        if stats['avg_days_to_pay']:
            if stats['avg_days_to_pay'] <= 0:
                score += 25  # Early payer
            elif stats['avg_days_to_pay'] > 30:
                score -= int(stats['avg_days_to_pay'] - 30)  # Penalty for late
        
        # Overdue amount penalty
        if stats['overdue_amount'] and stats['overdue_amount'] > 0:
            score -= min(100, int(stats['overdue_amount'] / 100))  # Max -100 points
    
    return max(300, min(850, score))  # Clamp between 300-850

def get_risk_level_from_score(score: int) -> str:
    """Get risk level from credit score"""
    if score >= 750:
        return RiskLevel.LOW.value
    elif score >= 650:
        return RiskLevel.MEDIUM.value
    elif score >= 550:
        return RiskLevel.HIGH.value
    else:
        return RiskLevel.VERY_HIGH.value

def calculate_recommended_credit_limit(
    credit_score: int,
    annual_revenue: float
) -> float:
    """Calculate recommended credit limit based on score and revenue"""
    if credit_score >= 750:
        multiplier = 0.15  # 15% of annual revenue
    elif credit_score >= 700:
        multiplier = 0.10
    elif credit_score >= 650:
        multiplier = 0.05
    elif credit_score >= 600:
        multiplier = 0.02
    else:
        return 0  # No credit
    
    base_limit = annual_revenue * multiplier if annual_revenue else 5000
    
    # Round to nearest $1000
    return round(base_limit / 1000) * 1000

def calculate_risk_score(
    outstanding: float,
    credit_limit: float,
    max_days_overdue: int,
    overdue_count: int
) -> int:
    """Calculate risk score (0-100, higher is riskier)"""
    score = 0
    
    # Credit utilization (0-40 points)
    if credit_limit and credit_limit > 0:
        utilization = outstanding / credit_limit
        score += min(40, int(utilization * 40))
    elif outstanding > 0:
        score += 40  # Max risk if no credit limit but has balance
    
    # Days overdue (0-40 points)
    if max_days_overdue:
        if max_days_overdue > 90:
            score += 40
        elif max_days_overdue > 60:
            score += 30
        elif max_days_overdue > 30:
            score += 20
        elif max_days_overdue > 0:
            score += 10
    
    # Overdue invoice count (0-20 points)
    if overdue_count:
        score += min(20, overdue_count * 5)
    
    return min(100, score)

async def notify_credit_limit_change(
    customer_id: str,
    new_limit: float,
    action: str
):
    """Send notification about credit limit change (placeholder)"""
    logger.info(f"Credit limit {action} for customer {customer_id}: ${new_limit} RETURNING * RETURNING * RETURNING *")
    # Email notification implementation would go here