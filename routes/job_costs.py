"""
Job Cost Tracking
Track job costs, expenses, materials, and profitability
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import json
from decimal import Decimal
from uuid import uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from services.audit_service import log_data_modification, log_data_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["Job Costs"])

# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class CostCategory(str, Enum):
    LABOR = "labor"
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    PERMITS = "permits"
    DISPOSAL = "disposal"
    TRAVEL = "travel"
    OTHER = "other"

class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"

class ExpenseCreate(BaseModel):
    category: CostCategory
    description: str
    amount: float = Field(..., gt=0)
    quantity: float = Field(1, gt=0)
    unit_cost: Optional[float] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    expense_date: date
    employee_id: Optional[str] = None
    is_billable: bool = True
    markup_percentage: float = Field(0, ge=0, le=100)
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

class ExpenseUpdate(BaseModel):
    category: Optional[CostCategory] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    expense_date: Optional[date] = None
    is_billable: Optional[bool] = None
    markup_percentage: Optional[float] = None
    notes: Optional[str] = None

class MaterialUsage(BaseModel):
    material_id: str
    quantity: float = Field(..., gt=0)
    unit_cost: Optional[float] = None
    notes: Optional[str] = None

class LaborEntry(BaseModel):
    employee_id: str
    hours_worked: float = Field(..., gt=0)
    hourly_rate: Optional[float] = None
    work_date: date
    task_id: Optional[str] = None
    notes: Optional[str] = None

class CostSummary(BaseModel):
    total_costs: float
    labor_costs: float
    material_costs: float
    equipment_costs: float
    other_costs: float
    estimated_costs: float
    actual_costs: float
    variance: float
    variance_percentage: float
    profit_margin: float
    markup_amount: float

# ============================================================================
# COST TRACKING ENDPOINTS
# ============================================================================

@router.post("/{job_id}/expenses", status_code=status.HTTP_201_CREATED)
async def add_job_expense(
    job_id: str,
    expense: ExpenseCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an expense to a job"""
    try:
        # Verify job exists
        job = db.execute(
            text("SELECT id, status FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        expense_id = str(uuid4())
        
        # Calculate total amount
        if expense.unit_cost:
            total_amount = expense.quantity * expense.unit_cost
        else:
            total_amount = expense.amount
        
        # Calculate billable amount with markup
        billable_amount = total_amount * (1 + expense.markup_percentage / 100) if expense.is_billable else 0
        
        # Create expense
        db.execute(
            text("""
                INSERT INTO job_expenses (
                    id, job_id, category, description,
                    amount, quantity, unit_cost,
                    total_amount, billable_amount,
                    vendor, invoice_number, expense_date,
                    employee_id, is_billable, markup_percentage,
                    status, receipt_url, notes, tags,
                    created_at, created_by, updated_at
                )
                VALUES (
                    :id, :job_id, :category, :description,
                    :amount, :quantity, :unit_cost,
                    :total_amount, :billable_amount,
                    :vendor, :invoice_number, :expense_date,
                    :employee_id, :is_billable, :markup_percentage,
                    :status, :receipt_url, :notes, :tags::jsonb,
                    NOW(), :created_by, NOW()
                )
            """),
            {
                "id": expense_id,
                "job_id": job_id,
                "category": expense.category,
                "description": expense.description,
                "amount": expense.amount,
                "quantity": expense.quantity,
                "unit_cost": expense.unit_cost,
                "total_amount": total_amount,
                "billable_amount": billable_amount,
                "vendor": expense.vendor,
                "invoice_number": expense.invoice_number,
                "expense_date": expense.expense_date,
                "employee_id": expense.employee_id,
                "is_billable": expense.is_billable,
                "markup_percentage": expense.markup_percentage,
                "status": ExpenseStatus.PENDING,
                "receipt_url": expense.receipt_url,
                "notes": expense.notes,
                "tags": json.dumps(expense.tags or []),
                "created_by": current_user["id"]
            }
        )
        
        # Update job actual cost
        db.execute(
            text("""
                UPDATE jobs
                SET actual_cost = COALESCE(actual_cost, 0) + :amount,
                    updated_at = NOW()
                WHERE id = :job_id
            """),
            {"job_id": job_id, "amount": total_amount}
        )
        
        db.commit()
        
        log_data_modification(
            db, current_user["id"], "job_expenses", "create",
            expense_id, new_values=expense.dict()
        )
        
        return {
            "id": expense_id,
            "message": "Expense added successfully",
            "total_amount": total_amount,
            "billable_amount": billable_amount
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to add expense")

@router.get("/{job_id}/expenses")
async def get_job_expenses(
    job_id: str,
    category: Optional[CostCategory] = None,
    status: Optional[ExpenseStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all expenses for a job"""
    try:
        query = """
            SELECT e.*, emp.first_name || ' ' || emp.last_name as employee_name
            FROM job_expenses e
            LEFT JOIN employees emp ON e.employee_id = emp.id
            WHERE e.job_id = :job_id
        """
        
        params = {"job_id": job_id}
        
        if category:
            query += " AND e.category = :category"
            params["category"] = category
        
        if status:
            query += " AND e.status = :status"
            params["status"] = status
        
        if start_date:
            query += " AND e.expense_date >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            query += " AND e.expense_date <= :end_date"
            params["end_date"] = end_date
        
        query += " ORDER BY e.expense_date DESC, e.created_at DESC"
        
        result = db.execute(text(query), params)
        
        expenses = []
        total_amount = 0
        total_billable = 0
        
        for row in result:
            expense = dict(row._mapping)
            expense["id"] = str(expense["id"])
            expense["job_id"] = str(expense["job_id"])
            if expense["employee_id"]:
                expense["employee_id"] = str(expense["employee_id"])
            
            total_amount += expense.get("total_amount", 0)
            total_billable += expense.get("billable_amount", 0)
            expenses.append(expense)
        
        log_data_access(db, current_user["id"], "job_expenses", "list", len(expenses))
        
        return {
            "job_id": job_id,
            "expenses": expenses,
            "total_expenses": total_amount,
            "total_billable": total_billable,
            "count": len(expenses)
        }
    
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch expenses")

@router.post("/{job_id}/materials")
async def record_material_usage(
    job_id: str,
    material: MaterialUsage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record material usage for a job"""
    try:
        # Get material details
        material_info = db.execute(
            text("""
                SELECT id, name, unit_cost, unit_of_measure
                FROM materials
                WHERE id = :material_id
            """),
            {"material_id": material.material_id}
        ).fetchone()
        
        if not material_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found"
            )
        
        usage_id = str(uuid4())
        unit_cost = material.unit_cost or material_info.unit_cost
        total_cost = material.quantity * unit_cost
        
        # Record usage
        db.execute(
            text("""
                INSERT INTO job_material_usage (
                    id, job_id, material_id, quantity,
                    unit_cost, total_cost, notes,
                    created_at, created_by
                )
                VALUES (
                    :id, :job_id, :material_id, :quantity,
                    :unit_cost, :total_cost, :notes,
                    NOW(), :created_by
                )
            """),
            {
                "id": usage_id,
                "job_id": job_id,
                "material_id": material.material_id,
                "quantity": material.quantity,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "notes": material.notes,
                "created_by": current_user["id"]
            }
        )
        
        # Update material inventory
        db.execute(
            text("""
                UPDATE materials
                SET quantity_on_hand = quantity_on_hand - :quantity,
                    last_used = NOW()
                WHERE id = :material_id
            """),
            {"material_id": material.material_id, "quantity": material.quantity}
        )
        
        # Add as job expense
        db.execute(
            text("""
                INSERT INTO job_expenses (
                    id, job_id, category, description,
                    amount, quantity, unit_cost, total_amount,
                    is_billable, created_at, created_by
                )
                VALUES (
                    :id, :job_id, 'materials', :description,
                    :total_cost, :quantity, :unit_cost, :total_cost,
                    TRUE, NOW(), :created_by
                )
            """),
            {
                "id": str(uuid4()),
                "job_id": job_id,
                "description": f"Material: {material_info.name}",
                "total_cost": total_cost,
                "quantity": material.quantity,
                "unit_cost": unit_cost,
                "created_by": current_user["id"]
            }
        )
        
        db.commit()
        
        return {
            "id": usage_id,
            "message": "Material usage recorded",
            "material": material_info.name,
            "quantity": material.quantity,
            "total_cost": total_cost
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording material usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to record material usage")

@router.post("/{job_id}/labor")
async def record_labor_entry(
    job_id: str,
    labor: LaborEntry,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record labor hours for a job"""
    try:
        # Get employee details
        employee = db.execute(
            text("""
                SELECT id, first_name, last_name, hourly_rate
                FROM employees
                WHERE id = :employee_id
            """),
            {"employee_id": labor.employee_id}
        ).fetchone()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        entry_id = str(uuid4())
        hourly_rate = labor.hourly_rate or employee.hourly_rate or 0
        total_cost = labor.hours_worked * hourly_rate
        
        # Record labor entry
        db.execute(
            text("""
                INSERT INTO job_labor_entries (
                    id, job_id, employee_id, hours_worked,
                    hourly_rate, total_cost, work_date,
                    task_id, notes, created_at, created_by
                )
                VALUES (
                    :id, :job_id, :employee_id, :hours,
                    :rate, :cost, :work_date,
                    :task_id, :notes, NOW(), :created_by
                )
            """),
            {
                "id": entry_id,
                "job_id": job_id,
                "employee_id": labor.employee_id,
                "hours": labor.hours_worked,
                "rate": hourly_rate,
                "cost": total_cost,
                "work_date": labor.work_date,
                "task_id": labor.task_id,
                "notes": labor.notes,
                "created_by": current_user["id"]
            }
        )
        
        # Add as job expense
        db.execute(
            text("""
                INSERT INTO job_expenses (
                    id, job_id, category, description,
                    amount, expense_date, employee_id,
                    is_billable, created_at, created_by
                )
                VALUES (
                    :id, :job_id, 'labor', :description,
                    :amount, :work_date, :employee_id,
                    TRUE, NOW(), :created_by
                )
            """),
            {
                "id": str(uuid4()),
                "job_id": job_id,
                "description": f"Labor: {employee.first_name} {employee.last_name} - {labor.hours_worked} hours",
                "amount": total_cost,
                "work_date": labor.work_date,
                "employee_id": labor.employee_id,
                "created_by": current_user["id"]
            }
        )
        
        # Update job actual hours
        db.execute(
            text("""
                UPDATE jobs
                SET actual_hours = COALESCE(actual_hours, 0) + :hours,
                    updated_at = NOW()
                WHERE id = :job_id
            """),
            {"job_id": job_id, "hours": labor.hours_worked}
        )
        
        db.commit()
        
        return {
            "id": entry_id,
            "message": "Labor entry recorded",
            "employee": f"{employee.first_name} {employee.last_name}",
            "hours": labor.hours_worked,
            "total_cost": total_cost
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording labor: {e}")
        raise HTTPException(status_code=500, detail="Failed to record labor")

@router.get("/{job_id}/cost-summary")
async def get_job_cost_summary(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive cost summary for a job"""
    try:
        # Get job details
        job = db.execute(
            text("""
                SELECT 
                    estimated_cost,
                    actual_cost,
                    total_amount as revenue
                FROM jobs
                WHERE id = :job_id
            """),
            {"job_id": job_id}
        ).fetchone()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get expense breakdown
        expenses = db.execute(
            text("""
                SELECT 
                    category,
                    SUM(total_amount) as total,
                    SUM(billable_amount) as billable
                FROM job_expenses
                WHERE job_id = :job_id
                GROUP BY category
            """),
            {"job_id": job_id}
        ).fetchall()
        
        # Calculate totals
        cost_breakdown = {}
        total_costs = 0
        total_billable = 0
        
        for expense in expenses:
            cost_breakdown[expense.category] = {
                "total": float(expense.total or 0),
                "billable": float(expense.billable or 0)
            }
            total_costs += expense.total or 0
            total_billable += expense.billable or 0
        
        # Calculate metrics
        estimated = float(job.estimated_cost or 0)
        actual = float(total_costs)
        revenue = float(job.revenue or 0)
        
        variance = actual - estimated
        variance_pct = (variance / estimated * 100) if estimated > 0 else 0
        profit = revenue - actual
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        
        summary = {
            "job_id": job_id,
            "estimated_cost": estimated,
            "actual_cost": actual,
            "revenue": revenue,
            "profit": profit,
            "profit_margin": profit_margin,
            "cost_variance": variance,
            "cost_variance_percentage": variance_pct,
            "total_billable": float(total_billable),
            "cost_breakdown": cost_breakdown,
            "cost_categories": {
                "labor": cost_breakdown.get("labor", {}).get("total", 0),
                "materials": cost_breakdown.get("materials", {}).get("total", 0),
                "equipment": cost_breakdown.get("equipment", {}).get("total", 0),
                "subcontractor": cost_breakdown.get("subcontractor", {}).get("total", 0),
                "other": sum(
                    v.get("total", 0) for k, v in cost_breakdown.items()
                    if k not in ["labor", "materials", "equipment", "subcontractor"]
                )
            }
        }
        
        log_data_access(db, current_user["id"], "jobs", "cost_summary", 1)
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cost summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cost summary")

@router.put("/expenses/{expense_id}/approve")
async def approve_expense(
    expense_id: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a job expense"""
    try:
        # Update expense status
        db.execute(
            text("""
                UPDATE job_expenses
                SET status = 'approved',
                    approved_by = :user_id,
                    approved_at = NOW(),
                    approval_notes = :notes,
                    updated_at = NOW()
                WHERE id = :expense_id
                AND status = 'pending'
            """),
            {
                "expense_id": expense_id,
                "user_id": current_user["id"],
                "notes": notes
            }
        )
        
        db.commit()
        
        return {"message": "Expense approved successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve expense RETURNING * RETURNING * RETURNING *")
