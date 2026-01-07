"""
Complete Customer CRUD API with Full History Tracking
Task #101: Full-featured customer management endpoints with search, filter, batch operations,
and comprehensive history tracking for all changes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import text, and_, or_, func
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
import csv
import io
import json
import logging
import hashlib
from uuid import UUID, uuid4
import asyncio
from enum import Enum
from psycopg2 import sql

from core.supabase_auth import get_current_user  # SUPABASE AUTH
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customers", tags=["Customers - Complete"])

# ============================================================================
# ENUMS
# ============================================================================

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"
    PROSPECT = "prospect"
    ARCHIVED = "archived"

class ContactType(str, Enum):
    PRIMARY = "primary"
    BILLING = "billing"
    TECHNICAL = "technical"
    EMERGENCY = "emergency"

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
    status: Optional[CustomerStatus] = CustomerStatus.ACTIVE
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(30, ge=0, le=365)
    tax_exempt: Optional[bool] = False
    notes: Optional[str] = None

class CustomerContact(BaseModel):
    contact_type: ContactType
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    is_primary: bool = False

class CustomerTag(BaseModel):
    tag: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class CustomerNote(BaseModel):
    note: str = Field(..., min_length=1)
    is_internal: bool = True
    reminder_date: Optional[datetime] = None

class CustomerCustomField(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=100)
    field_value: Any
    field_type: str = Field("text", pattern=r"^(text|number|date|boolean|json)$")

class CustomerCreate(CustomerBase):
    source: Optional[str] = "manual"
    lead_source: Optional[str] = None
    referred_by: Optional[UUID] = None
    contacts: Optional[List[CustomerContact]] = []
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
    status: Optional[CustomerStatus] = None
    credit_limit: Optional[float] = None
    payment_terms: Optional[int] = None
    tax_exempt: Optional[bool] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    status: CustomerStatus
    credit_limit: Optional[float]
    payment_terms: int
    tax_exempt: bool
    notes: Optional[str]
    source: Optional[str]
    lead_source: Optional[str]
    referred_by: Optional[UUID]
    total_spent: float
    job_count: int
    last_interaction: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    contacts: List[Dict]
    tags: List[str]
    custom_fields: Dict[str, Any]
    history_count: int

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class CustomerMergeRequest(BaseModel):
    primary_customer_id: UUID
    duplicate_customer_ids: List[UUID]
    merge_strategy: str = Field("keep_primary", pattern=r"^(keep_primary|keep_newest|manual)$")
    field_overrides: Optional[Dict[str, Any]] = {}

class CustomerBulkUpdateRequest(BaseModel):
    customer_ids: List[UUID]
    updates: CustomerUpdate

class CustomerExportRequest(BaseModel):
    format: str = Field("csv", pattern=r"^(csv|json|excel)$")
    fields: Optional[List[str]] = None
    include_history: bool = False
    include_jobs: bool = False

# ============================================================================
# CRUD OPERATIONS
# ============================================================================

@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a new customer with complete history tracking
    """
    try:
        cursor = db.cursor()

        # Generate customer ID
        customer_id = str(uuid4())

        # Insert customer
        query = sql.SQL("""
            INSERT INTO customers (
                id, name, email, phone, company, address, city, state, zip_code,
                status, credit_limit, payment_terms, tax_exempt, notes,
                source, lead_source, referred_by, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, NOW(), NOW()
            )
            RETURNING *
        """)
        cursor.execute(query, (
            customer_id, customer.name, customer.email, customer.phone, customer.company,
            customer.address, customer.city, customer.state, customer.zip_code,
            customer.status.value if customer.status else 'active',
            customer.credit_limit, customer.payment_terms, customer.tax_exempt, customer.notes,
            customer.source, customer.lead_source, str(customer.referred_by) if customer.referred_by else None
        ))

        new_customer = cursor.fetchone()

        # Add contacts
        for contact in customer.contacts:
            contact_query = sql.SQL("""
                INSERT INTO customer_contacts (
                    id, customer_id, contact_type, name, email, phone, title, is_primary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """)
            cursor.execute(contact_query, (
                str(uuid4()), customer_id, contact.contact_type.value,
                contact.name, contact.email, contact.phone, contact.title, contact.is_primary
            ))

        # Add tags
        for tag in customer.tags:
            tag_query = sql.SQL("""
                INSERT INTO customer_tags (id, customer_id, tag, created_at)
                VALUES (%s, %s, %s, NOW())
            """)
            cursor.execute(tag_query, (str(uuid4()), customer_id, tag))

        # Add custom fields
        for field_name, field_value in customer.custom_fields.items():
            field_query = sql.SQL("""
                INSERT INTO customer_custom_fields (
                    id, customer_id, field_name, field_value, field_type
                ) VALUES (%s, %s, %s, %s, %s)
            """)
            cursor.execute(field_query, (
                str(uuid4()), customer_id, field_name,
                json.dumps(field_value) if not isinstance(field_value, str) else field_value,
                type(field_value).__name__
            ))

        db.commit()

        # Get complete customer data
        return await get_customer(UUID(customer_id), db, current_user)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get a specific customer by ID with all related data
    """
    try:
        cursor = db.cursor()

        # Get customer
        query = sql.SQL("""
            SELECT c.*,
                   COALESCE(SUM(i.amount), 0) as total_spent,
                   COUNT(DISTINCT j.id) as job_count,
                   MAX(GREATEST(j.updated_at, i.updated_at)) as last_interaction,
                   COUNT(DISTINCT ch.version) as history_count
            FROM customers c
            LEFT JOIN jobs j ON j.customer_id = c.id
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.status = 'paid'
            LEFT JOIN customer_history ch ON ch.customer_id = c.id
            WHERE c.id = %s
            GROUP BY c.id
        """)
        cursor.execute(query, (str(customer_id),))

        customer = cursor.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get contacts
        contact_query = sql.SQL("SELECT * FROM customer_contacts WHERE customer_id = %s")
        cursor.execute(contact_query, (str(customer_id),))
        contacts = cursor.fetchall()

        # Get tags
        tag_query = sql.SQL("SELECT tag FROM customer_tags WHERE customer_id = %s")
        cursor.execute(tag_query, (str(customer_id),))
        tags = [row['tag'] for row in cursor.fetchall()]

        # Get custom fields
        field_query = sql.SQL("""
            SELECT field_name, field_value, field_type FROM customer_custom_fields
            WHERE customer_id = %s
        """)
        cursor.execute(field_query, (str(customer_id),))
        custom_fields = {}
        for row in cursor.fetchall():
            value = row['field_value']
            if row['field_type'] == 'json':
                value = json.loads(value)
            custom_fields[row['field_name']] = value

        return CustomerResponse(
            **customer,
            contacts=contacts,
            tags=tags,
            custom_fields=custom_fields
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    updates: CustomerUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update a customer with history tracking
    """
    try:
        cursor = db.cursor()

        # SECURITY: Whitelist allowed update fields (defense-in-depth)
        ALLOWED_UPDATE_FIELDS = {
            "name", "email", "phone", "company", "address", "city", "state",
            "zip_code", "status", "credit_limit", "payment_terms", "tax_exempt", "notes"
        }

        # Build update query
        update_fields = []
        update_values = []
        for field, value in updates.dict(exclude_unset=True).items():
            # Skip fields not in whitelist
            if field not in ALLOWED_UPDATE_FIELDS:
                continue
            update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            if field == "status" and value:
                update_values.append(value.value)
            else:
                update_values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append(sql.SQL("updated_at = NOW()"))
        update_values.append(str(customer_id))

        update_query = sql.SQL("""
            UPDATE customers
            SET {fields}
            WHERE id = %s
            RETURNING *
        """).format(fields=sql.SQL(", ").join(update_fields))
        cursor.execute(update_query, update_values)

        updated_customer = cursor.fetchone()
        if not updated_customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        db.commit()

        return await get_customer(customer_id, db, current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Soft delete a customer (mark as archived)
    """
    try:
        cursor = db.cursor()

        # Check if customer exists
        cursor.execute("SELECT id FROM customers WHERE id = %s", (str(customer_id),))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")

        # Soft delete by setting status to archived
        cursor.execute("""
            UPDATE customers
            SET status = 'archived', updated_at = NOW()
            WHERE id = %s
        """, (str(customer_id),))

        db.commit()

        return {"message": "Customer archived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    status: Optional[CustomerStatus] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    min_spent: Optional[float] = None,
    max_spent: Optional[float] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: str = Query("created_at", pattern=r"^(name|email|created_at|updated_at|total_spent|job_count)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    List customers with advanced filtering and pagination
    """
    try:
        cursor = db.cursor()

        # Build WHERE clause
        where_conditions = [sql.SQL("1=1")]
        params = []

        if search:
            where_conditions.append(sql.SQL("""
                (LOWER(c.name) LIKE LOWER(%s) OR
                 LOWER(c.email) LIKE LOWER(%s) OR
                 LOWER(c.company) LIKE LOWER(%s) OR
                 c.phone LIKE %s)
            """))
            search_pattern = f"%{search}%"
            params.extend([search_pattern] * 4)

        if status:
            where_conditions.append(sql.SQL("c.status = %s"))
            params.append(status.value)

        if city:
            where_conditions.append(sql.SQL("LOWER(c.city) = LOWER(%s)"))
            params.append(city)

        if state:
            where_conditions.append(sql.SQL("UPPER(c.state) = UPPER(%s)"))
            params.append(state)

        where_clause = sql.SQL(" AND ").join(where_conditions)

        # Build HAVING clause for aggregates
        having_conditions = []
        if min_spent is not None:
            having_conditions.append(sql.SQL("COALESCE(SUM(i.amount), 0) >= %s"))
            params.append(min_spent)
        if max_spent is not None:
            having_conditions.append(sql.SQL("COALESCE(SUM(i.amount), 0) <= %s"))
            params.append(max_spent)

        having_clause = sql.SQL(" AND ").join(having_conditions) if having_conditions else sql.SQL("1=1")

        # Get total count
        count_query = sql.SQL("""
            SELECT COUNT(DISTINCT c.id) as total
            FROM customers c
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.status = 'paid'
            WHERE {where_clause}
            GROUP BY c.id
            HAVING {having_clause}
        """).format(
            where_clause=where_clause,
            having_clause=having_clause,
        )
        cursor.execute(count_query, params)
        total = len(cursor.fetchall())

        # Get paginated results
        offset = (page - 1) * per_page

        # Sort mapping
        sort_mapping = {
            "name": "c.name",
            "email": "c.email",
            "created_at": "c.created_at",
            "updated_at": "c.updated_at",
            "total_spent": "total_spent",
            "job_count": "job_count"
        }

        # Ensure safe sort column and order to prevent SQL injection
        safe_sort_column = sort_mapping.get(sort_by, 'c.created_at')
        safe_sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"

        if "." in safe_sort_column:
            alias, column = safe_sort_column.split(".", 1)
            sort_sql = sql.SQL("{}.{}").format(sql.Identifier(alias), sql.Identifier(column))
        else:
            sort_sql = sql.Identifier(safe_sort_column)

        list_query = sql.SQL("""
            SELECT c.*,
                   COALESCE(SUM(i.amount), 0) as total_spent,
                   COUNT(DISTINCT j.id) as job_count,
                   MAX(GREATEST(j.updated_at, i.updated_at)) as last_interaction,
                   COUNT(DISTINCT ch.version) as history_count
            FROM customers c
            LEFT JOIN jobs j ON j.customer_id = c.id
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.status = 'paid'
            LEFT JOIN customer_history ch ON ch.customer_id = c.id
            WHERE {where_clause}
            GROUP BY c.id
            HAVING {having_clause}
            ORDER BY {sort_column} {sort_order}
            LIMIT %s OFFSET %s
        """).format(
            where_clause=where_clause,
            having_clause=having_clause,
            sort_column=sort_sql,
            sort_order=sql.SQL(safe_sort_order),
        )
        params.extend([per_page, offset])

        cursor.execute(list_query, params)
        customers = cursor.fetchall()

        # Enrich with tags for each customer
        customer_responses = []
        for customer in customers:
            cursor.execute("SELECT tag FROM customer_tags WHERE customer_id = %s", (customer['id'],))
            customer_tags = [row['tag'] for row in cursor.fetchall()]

            # Filter by tags if specified
            if tags and not any(tag in customer_tags for tag in tags):
                continue

            customer_responses.append(CustomerResponse(
                **customer,
                contacts=[],
                tags=customer_tags,
                custom_fields={}
            ))

        total_pages = (total + per_page - 1) // per_page

        return CustomerListResponse(
            customers=customer_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/advanced")
async def search_customers(
    query: str,
    threshold: float = Query(0.3, ge=0, le=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Advanced customer search using the custom search_customers function
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT * FROM search_customers(%s, %s, %s)
        """, (query, threshold, limit))

        results = cursor.fetchall()

        return results

    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge", response_model=CustomerResponse)
async def merge_customers(
    merge_request: CustomerMergeRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Merge duplicate customers into one
    """
    try:
        cursor = db.cursor()

        # Execute merge function
        cursor.execute("""
            SELECT merge_duplicate_customers(%s, %s)
        """, (
            str(merge_request.primary_customer_id),
            [str(id) for id in merge_request.duplicate_customer_ids]
        ))

        result = cursor.fetchone()
        db.commit()

        if not result or not result.get('merge_duplicate_customers'):
            raise HTTPException(status_code=500, detail="Merge failed")

        # Get the merged customer
        return await get_customer(merge_request.primary_customer_id, db, current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error merging customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}/history")
async def get_customer_history(
    customer_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get the change history for a customer
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT * FROM customer_history
            WHERE customer_id = %s
            ORDER BY changed_at DESC
            LIMIT %s
        """, (str(customer_id), limit))

        history = cursor.fetchall()

        return history

    except Exception as e:
        logger.error(f"Error getting customer history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/contacts", response_model=Dict)
async def add_customer_contact(
    customer_id: UUID,
    contact: CustomerContact,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Add a contact to a customer
    """
    try:
        cursor = db.cursor()

        contact_id = str(uuid4())

        cursor.execute("""
            INSERT INTO customer_contacts (
                id, customer_id, contact_type, name, email, phone, title, is_primary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            contact_id, str(customer_id), contact.contact_type.value,
            contact.name, contact.email, contact.phone, contact.title, contact.is_primary
        ))

        new_contact = cursor.fetchone()
        db.commit()

        return new_contact

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/tags")
async def add_customer_tags(
    customer_id: UUID,
    tags: List[str],
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Add tags to a customer
    """
    try:
        cursor = db.cursor()

        for tag in tags:
            cursor.execute("""
                INSERT INTO customer_tags (id, customer_id, tag, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (customer_id, tag) DO NOTHING
            """, (str(uuid4()), str(customer_id), tag))

        db.commit()

        return {"message": f"Added {len(tags)} tags to customer"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/notes")
async def add_customer_note(
    customer_id: UUID,
    note: CustomerNote,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Add a note to a customer
    """
    try:
        cursor = db.cursor()

        note_id = str(uuid4())

        cursor.execute("""
            INSERT INTO customer_notes (
                id, customer_id, note, is_internal, reminder_date, created_by, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING *
        """, (
            note_id, str(customer_id), note.note,
            note.is_internal, note.reminder_date, current_user['email']
        ))

        new_note = cursor.fetchone()
        db.commit()

        return new_note

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bulk-update")
async def bulk_update_customers(
    bulk_update: CustomerBulkUpdateRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update multiple customers at once
    """
    try:
        cursor = db.cursor()

        # SECURITY: Whitelist allowed update fields (defense-in-depth)
        ALLOWED_UPDATE_FIELDS = {
            "name", "email", "phone", "company", "address", "city", "state",
            "zip_code", "status", "credit_limit", "payment_terms", "tax_exempt", "notes"
        }

        update_fields = []
        update_values = []
        for field, value in bulk_update.updates.dict(exclude_unset=True).items():
            # Skip fields not in whitelist
            if field not in ALLOWED_UPDATE_FIELDS:
                continue
            update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            if field == "status" and value:
                update_values.append(value.value)
            else:
                update_values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append(sql.SQL("updated_at = NOW()"))

        # Update each customer
        updated_count = 0
        for customer_id in bulk_update.customer_ids:
            bulk_query = sql.SQL("""
                UPDATE customers
                SET {fields}
                WHERE id = %s
            """).format(fields=sql.SQL(", ").join(update_fields))
            cursor.execute(bulk_query, update_values + [str(customer_id)])
            updated_count += cursor.rowcount

        db.commit()

        return {"message": f"Updated {updated_count} customers"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk updating customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_customers(
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Import customers from CSV file
    """
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(text_content))

        cursor = db.cursor()
        imported_count = 0
        errors = []

        for row in csv_reader:
            try:
                customer_id = str(uuid4())

                cursor.execute("""
                    INSERT INTO customers (
                        id, name, email, phone, company, address, city, state, zip_code,
                        status, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, NOW(), NOW()
                    )
                """, (
                    customer_id,
                    row.get('name', ''),
                    row.get('email', ''),
                    row.get('phone'),
                    row.get('company'),
                    row.get('address'),
                    row.get('city'),
                    row.get('state'),
                    row.get('zip_code'),
                    row.get('status', 'active')
                ))

                imported_count += 1

            except Exception as e:
                errors.append({
                    "row": row,
                    "error": str(e)
                })

        db.commit()

        return {
            "imported": imported_count,
            "errors": len(errors),
            "error_details": errors[:10]  # Return first 10 errors
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error importing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_customers(
    export_request: CustomerExportRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Export customers to specified format
    """
    try:
        cursor = db.cursor()

        # Get customers
        cursor.execute("""
            SELECT c.*,
                   COALESCE(SUM(i.amount), 0) as total_spent,
                   COUNT(DISTINCT j.id) as job_count
            FROM customers c
            LEFT JOIN jobs j ON j.customer_id = c.id
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.status = 'paid'
            WHERE c.status != 'archived'
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)

        customers = cursor.fetchall()

        if export_request.format == "json":
            return customers

        elif export_request.format == "csv":
            output = io.StringIO()

            # Define fields to export
            fields = export_request.fields or [
                'id', 'name', 'email', 'phone', 'company',
                'city', 'state', 'total_spent', 'job_count'
            ]

            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()

            for customer in customers:
                writer.writerow({
                    field: customer.get(field, '') for field in fields
                })

            return output.getvalue()

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {export_request.format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
async def get_customer_stats(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get customer statistics overview
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active_customers,
                COUNT(*) FILTER (WHERE status = 'lead') as leads,
                COUNT(*) FILTER (WHERE status = 'prospect') as prospects,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_this_month,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week,
                COALESCE(AVG((SELECT SUM(amount) FROM invoices WHERE customer_id = c.id AND status = 'paid')), 0) as avg_revenue_per_customer,
                COALESCE(AVG((SELECT COUNT(*) FROM jobs WHERE customer_id = c.id)), 0) as avg_jobs_per_customer
            FROM customers c
            WHERE status != 'archived'
        """)

        stats = cursor.fetchone()

        return stats

    except Exception as e:
        logger.error(f"Error getting customer stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Register all endpoints
__all__ = ['router']