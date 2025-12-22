"""
Complete Customer CRUD API
Full-featured customer management endpoints with search, filter, and batch operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import csv
import io
import json
import logging
from uuid import UUID, uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH - CORRECT!
from services.audit_service import log_data_access, log_data_modification
from services.encryption_service import encrypt_field, decrypt_field, mask_sensitive_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

# ============================================================================
# MODELS
# ============================================================================

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")

class CustomerCreate(CustomerBase):
    source: Optional[str] = "manual"
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    status: str
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_jobs: int = 0
    total_revenue: float = 0
    last_contact: Optional[datetime]

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    per_page: int
    pages: int

class CustomerFilter(BaseModel):
    status: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    min_revenue: Optional[float] = None
    max_revenue: Optional[float] = None

class BatchOperation(BaseModel):
    operation: str  # update, delete, tag, untag
    customer_ids: List[str]
    data: Optional[Dict[str, Any]] = {}

# ============================================================================
# CRUD OPERATIONS
# ============================================================================

@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    status: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(name|email|created_at|total_revenue)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customers with pagination, search, and filters"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build base query
        query = "SELECT c.*, COUNT(j.id) as job_count, COALESCE(SUM(j.total_amount), 0) as total_revenue "
        count_query = "SELECT COUNT(DISTINCT c.id) "

        base_from = "FROM customers c LEFT JOIN jobs j ON c.id = j.customer_id "

        # Build WHERE conditions
        conditions = ["c.tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id}

        if search:
            conditions.append("""
                (c.name ILIKE :search OR
                 c.email ILIKE :search OR
                 c.phone ILIKE :search OR
                 c.company ILIKE :search)
            """)
            params["search"] = f"%{search}%"

        if status:
            conditions.append("c.status = :status")
            params["status"] = status

        if state:
            conditions.append("c.state = :state")
            params["state"] = state

        if city:
            conditions.append("c.city = :city")
            params["city"] = city

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Get total count
        count_result = db.execute(text(count_query + base_from + where_clause), params)
        total = count_result.scalar() or 0

        # Build final query with grouping and pagination
        query += base_from + where_clause
        query += " GROUP BY c.id "
        query += f" ORDER BY {sort_by} {sort_order.upper()} "
        query += f" LIMIT :limit OFFSET :offset"

        params["limit"] = per_page
        params["offset"] = (page - 1) * per_page

        # Execute query
        result = db.execute(text(query), params)

        # Format results
        customers = []
        for row in result:
            customer = dict(row._mapping)
            customer["id"] = str(customer["id"])
            customer["tags"] = customer.get("tags", []) or []
            customer["total_jobs"] = customer.get("job_count", 0)
            customer["total_revenue"] = float(customer.get("total_revenue", 0))
            customers.append(customer)

        # Log access
        log_data_access(db, current_user["id"], "customers", "list", len(customers))

        return CustomerListResponse(
            customers=customers,
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page if per_page > 0 else 0
        )

    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customers")

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single customer with full details"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = db.execute(
            text("""
                SELECT c.*,
                    COUNT(DISTINCT j.id) as job_count,
                    COALESCE(SUM(j.total_amount), 0) as total_revenue,
                    MAX(j.created_at) as last_job_date
                FROM customers c
                LEFT JOIN jobs j ON c.id = j.customer_id
                WHERE c.id = :id AND c.tenant_id = :tenant_id
                GROUP BY c.id
            """),
            {"id": customer_id, "tenant_id": tenant_id}
        )

        customer = result.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer_dict = dict(customer._mapping)
        customer_dict["id"] = str(customer_dict["id"])
        customer_dict["total_jobs"] = customer_dict.get("job_count", 0)
        customer_dict["total_revenue"] = float(customer_dict.get("total_revenue", 0))
        customer_dict["last_contact"] = customer_dict.get("last_job_date")

        # Log access
        log_data_access(db, current_user["id"], "customers", "read", 1)

        return customer_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer")

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new customer"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        customer_id = str(uuid4())

        # Check for duplicate email within tenant
        existing = db.execute(
            text("SELECT id FROM customers WHERE email = :email AND tenant_id = :tenant_id"),
            {"email": customer.email, "tenant_id": tenant_id}
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists"
            )

        # Insert customer
        db.execute(
            text("""
                INSERT INTO customers (
                    id, name, email, phone, company,
                    address, city, state, zip_code,
                    status, tags, source, custom_fields,
                    created_at, created_by, tenant_id
                ) VALUES (
                    :id, :name, :email, :phone, :company,
                    :address, :city, :state, :zip_code,
                    'active', :tags::jsonb, :source, :custom_fields::jsonb,
                    NOW(), :created_by, :tenant_id
                )
            """),
            {
                "id": customer_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "company": customer.company,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "tags": json.dumps(customer.tags or []),
                "source": customer.source,
                "custom_fields": json.dumps(customer.custom_fields or {}),
                "created_by": current_user["id"],
                "tenant_id": tenant_id
            }
        )

        db.commit()

        # Log creation
        log_data_modification(
            db, current_user["id"], "customers", "create",
            customer_id, new_values=customer.dict()
        )

        # Fetch and return created customer
        return await get_customer(customer_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer details"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Check customer exists
        existing = db.execute(
            text("SELECT * FROM customers WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": customer_id, "tenant_id": tenant_id}
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Build update query
        update_fields = []
        params = {"id": customer_id, "tenant_id": tenant_id}

        for field, value in customer.dict(exclude_unset=True).items():
            if field in ["tags", "custom_fields"]:
                update_fields.append(f"{field} = :{field}::jsonb")
                params[field] = json.dumps(value)
            else:
                update_fields.append(f"{field} = :{field}")
                params[field] = value

        if update_fields:
            update_fields.append("updated_at = NOW()")
            query = f"""
                UPDATE customers
                SET {', '.join(update_fields)}
                WHERE id = :id AND tenant_id = :tenant_id
            """

            db.execute(text(query), params)
            db.commit()

            # Log modification
            log_data_modification(
                db, current_user["id"], "customers", "update",
                customer_id, old_values=dict(existing._mapping),
                new_values=customer.dict(exclude_unset=True)
            )

        # Return updated customer
        return await get_customer(customer_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update customer")

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete customer (soft delete by default)"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Check if customer has jobs
        job_count = db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE customer_id = :id AND tenant_id = :tenant_id"),
            {"id": customer_id, "tenant_id": tenant_id}
        ).scalar()

        if job_count > 0:
            # Soft delete - just mark as inactive
            db.execute(
                text("""
                    UPDATE customers
                    SET status = 'deleted',
                        deleted_at = NOW(),
                        deleted_by = :user_id
                    WHERE id = :id AND tenant_id = :tenant_id
                """),
                {"id": customer_id, "user_id": current_user["id"], "tenant_id": tenant_id}
            )
        else:
            # Hard delete if no associated data
            db.execute(
                text("DELETE FROM customers WHERE id = :id AND tenant_id = :tenant_id"),
                {"id": customer_id, "tenant_id": tenant_id}
            )

        db.commit()

        # Log deletion
        log_data_modification(
            db, current_user["id"], "customers", "delete",
            customer_id
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete customer")

# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@router.post("/batch", response_model=Dict[str, Any])
async def batch_operation(
    operation: BatchOperation,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform batch operations on multiple customers"""
    try:
        results = {"success": 0, "failed": 0, "errors": []}

        for customer_id in operation.customer_ids:
            try:
                if operation.operation == "delete":
                    await delete_customer(customer_id, current_user, db)
                    results["success"] += 1

                elif operation.operation == "update":
                    update_data = CustomerUpdate(**operation.data)
                    await update_customer(customer_id, update_data, current_user, db)
                    results["success"] += 1

                elif operation.operation == "tag":
                    tags = operation.data.get("tags", [])
                    db.execute(
                        text("""
                            UPDATE customers
                            SET tags = tags || :new_tags::jsonb
                            WHERE id = :id AND tenant_id = :tenant_id
                        """),
                        {"id": customer_id, "new_tags": json.dumps(tags), "tenant_id": current_user["tenant_id"]}
                    )
                    results["success"] += 1

                else:
                    results["failed"] += 1
                    results["errors"].append(f"Unknown operation: {operation.operation}")

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Customer {customer_id}: {str(e)}")

        if results["success"] > 0:
            db.commit()

        return results

    except Exception as e:
        db.rollback()
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(status_code=500, detail="Batch operation failed")

# ============================================================================
# IMPORT/EXPORT
# ============================================================================

@router.post("/import", response_model=Dict[str, Any])
async def import_customers(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import customers from CSV file"""
    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))

        imported = 0
        errors = []

        for row in csv_reader:
            try:
                customer = CustomerCreate(
                    name=row.get('name'),
                    email=row.get('email'),
                    phone=row.get('phone'),
                    company=row.get('company'),
                    address=row.get('address'),
                    city=row.get('city'),
                    state=row.get('state'),
                    zip_code=row.get('zip_code')
                )

                await create_customer(customer, current_user, db)
                imported += 1

            except Exception as e:
                errors.append(f"Row {imported + len(errors) + 1}: {str(e)}")

        return {
            "imported": imported,
            "failed": len(errors),
            "errors": errors[:10]  # Limit error messages
        }

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail="Import failed")

@router.get("/export", response_model=None)
async def export_customers(
    format: str = Query("csv", pattern="^(csv|json)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export customers to CSV or JSON"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = db.execute(
            text("SELECT * FROM customers WHERE status != 'deleted' AND tenant_id = :tenant_id ORDER BY created_at DESC"),
            {"tenant_id": tenant_id}
        )

        customers = [dict(row._mapping) for row in result]

        if format == "json":
            return customers
        else:
            # Create CSV
            output = io.StringIO()
            if customers:
                writer = csv.DictWriter(output, fieldnames=customers[0].keys())
                writer.writeheader()
                writer.writerows(customers)

            return output.getvalue()

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed RETURNING *")