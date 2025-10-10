"""
Relationship-Aware API Routes
Creates entities with automatic relationship linking
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from core.relationship_awareness import RelationshipAwareness
import asyncpg

router = APIRouter(prefix="/api/v1/aware", tags=["Relationship Awareness"])

# Pydantic models for request validation
class CustomerCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    tenant_id: str

class JobCreateRequest(BaseModel):
    customer_id: str
    estimate_id: Optional[str] = None
    job_number: str
    title: str
    description: Optional[str] = None
    property_address: Optional[str] = None
    scheduled_start: Optional[str] = None
    tenant_id: str
    employee_ids: Optional[List[str]] = None  # Auto-assign crew
    equipment_ids: Optional[List[str]] = None  # Auto-reserve equipment
    materials: Optional[List[Dict[str, Any]]] = None  # Auto-allocate materials

class EmployeeCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[str] = None
    employment_status: Optional[str] = "active"
    employee_type: Optional[str] = "full_time"
    tenant_id: str

# Dependency to get RelationshipAwareness instance
async def get_relationship_awareness() -> RelationshipAwareness:
    """Get RelationshipAwareness instance from app state"""
    from main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    return RelationshipAwareness(app.state.db_pool)


@router.post("/customers")
async def create_customer_with_awareness(
    request: CustomerCreateRequest,
    ra: RelationshipAwareness = Depends(get_relationship_awareness)
):
    """
    Create customer with full relationship awareness

    Automatically:
    - Creates customer record
    - Initializes relationship tracking
    - Sets up computed field materialization
    - Returns complete view with all relationships
    """
    try:
        customer_data = request.dict()
        result = await ra.create_customer_with_awareness(customer_data)

        return {
            "success": True,
            "customer": result,
            "message": "Customer created with relationship awareness"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")


@router.post("/jobs")
async def create_job_with_awareness(
    request: JobCreateRequest,
    ra: RelationshipAwareness = Depends(get_relationship_awareness)
):
    """
    Create job with automatic relationship linking

    Automatically links:
    - Customer (parent)
    - Estimate (if provided)
    - Assigns employees (if provided)
    - Reserves equipment (if provided)
    - Allocates materials (if provided)

    Example request with auto-linking:
    {
        "customer_id": "...",
        "job_number": "JOB-001",
        "title": "Roof Replacement",
        "employee_ids": ["emp-1", "emp-2"],  # Auto-assigned to job
        "equipment_ids": ["equip-1"],  # Auto-reserved
        "materials": [
            {"inventory_item_id": "mat-1", "quantity": 100, "unit_cost": 5.50}
        ]  # Auto-allocated
    }
    """
    try:
        job_data = request.dict()
        result = await ra.create_job_with_awareness(job_data)

        return {
            "success": True,
            "job": result,
            "message": "Job created with automatic relationship linking",
            "relationships_created": {
                "employees_assigned": len(request.employee_ids or []),
                "equipment_reserved": len(request.equipment_ids or []),
                "materials_allocated": len(request.materials or [])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@router.get("/customers/{customer_id}/complete")
async def get_complete_customer_view(
    customer_id: str,
    ra: RelationshipAwareness = Depends(get_relationship_awareness)
):
    """
    Get complete 360° view of customer with ALL relationships

    Returns:
    - Base customer data
    - All jobs (with status, dates, amounts)
    - All estimates (with totals, status)
    - All invoices (with payment status)
    - All communications (history)
    - All payments (transaction history)
    - Computed fields (lifetime_value, total_jobs, etc.)
    - Complete relationship graph
    """
    try:
        result = await ra.get_complete_entity_view(
            entity_type="customers",
            entity_id=customer_id
        )

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "success": True,
            "customer_complete_view": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customer view: {str(e)}")


@router.get("/jobs/{job_id}/complete")
async def get_complete_job_view(
    job_id: str,
    ra: RelationshipAwareness = Depends(get_relationship_awareness)
):
    """
    Get complete view of job with ALL relationships

    Returns:
    - Base job data
    - Customer information
    - Assigned employees (crew)
    - Reserved equipment
    - Allocated materials
    - Timesheets (labor tracking)
    - Field inspections
    - Change orders
    - Computed fields (total_labor_hours, crew_size, etc.)
    """
    try:
        result = await ra.get_complete_entity_view(
            entity_type="jobs",
            entity_id=job_id
        )

        if not result:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "success": True,
            "job_complete_view": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job view: {str(e)}")


@router.get("/employees/{employee_id}/complete")
async def get_complete_employee_view(
    employee_id: str,
    ra: RelationshipAwareness = Depends(get_relationship_awareness)
):
    """
    Get complete view of employee with ALL relationships

    Returns:
    - Base employee data
    - HR record (status, type, hire date)
    - Job assignments (current and historical)
    - Timesheets (hours worked)
    - Certifications
    - Training records
    - Performance reviews
    - Computed fields (total_hours_worked, total_jobs_completed)
    """
    try:
        result = await ra.get_complete_entity_view(
            entity_type="employees",
            entity_id=employee_id
        )

        if not result:
            raise HTTPException(status_code=404, detail="Employee not found")

        return {
            "success": True,
            "employee_complete_view": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee view: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if relationship awareness system is operational"""
    return {
        "status": "operational",
        "system": "Relationship Awareness API",
        "version": "1.0.0",
        "features": [
            "Auto-linking on entity creation",
            "Complete 360° entity views",
            "Relationship graph tracking",
            "Computed field materialization"
        ]
    }
