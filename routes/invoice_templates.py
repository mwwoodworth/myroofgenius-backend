"""
Invoice Templates Module
Task 32: Invoice templates implementation

Provides reusable invoice templates for quick invoice generation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import json
import uuid
import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

router = APIRouter()

# ==================== Enums ====================

class TemplateCategory(str, Enum):
    SERVICE = "service"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    INSTALLATION = "installation"
    CONSULTATION = "consultation"
    PROJECT = "project"
    RECURRING = "recurring"
    CUSTOM = "custom"

# ==================== Pydantic Models ====================

class InvoiceTemplateItem(BaseModel):
    """Invoice template line item"""
    id: Optional[str] = None
    item_type: str = Field(description="Type of item (service, material, expense, other)")
    description: str = Field(description="Item description")
    default_quantity: float = Field(default=1.0, description="Default quantity")
    default_price: Optional[float] = Field(default=None, description="Default unit price")
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Tax rate percentage")
    sort_order: int = Field(default=0, description="Display order")

class CreateInvoiceTemplate(BaseModel):
    """Create new invoice template"""
    template_name: str = Field(description="Template name", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="Template description")
    category: Optional[TemplateCategory] = Field(default=TemplateCategory.CUSTOM, description="Template category")
    payment_terms: Optional[str] = Field(default="Net 30", description="Default payment terms")
    default_notes: Optional[str] = Field(default=None, description="Default invoice notes")
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Default tax rate")
    items: List[InvoiceTemplateItem] = Field(default=[], description="Template line items")

class UpdateInvoiceTemplate(BaseModel):
    """Update invoice template"""
    template_name: Optional[str] = Field(default=None, description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    category: Optional[TemplateCategory] = Field(default=None, description="Template category")
    payment_terms: Optional[str] = Field(default=None, description="Default payment terms")
    default_notes: Optional[str] = Field(default=None, description="Default invoice notes")
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Default tax rate")
    is_active: Optional[bool] = Field(default=None, description="Template active status")

class InvoiceFromTemplate(BaseModel):
    """Generate invoice from template"""
    customer_id: str = Field(description="Customer ID")
    job_id: Optional[str] = Field(default=None, description="Associated job ID")
    issue_date: Optional[date] = Field(default=None, description="Invoice issue date")
    due_date: Optional[date] = Field(default=None, description="Payment due date")
    apply_customer_discount: bool = Field(default=True, description="Apply customer-specific discount")
    override_items: Optional[List[InvoiceTemplateItem]] = Field(default=None, description="Override template items")
    additional_notes: Optional[str] = Field(default=None, description="Additional notes to append")

class TemplateUsageStats(BaseModel):
    """Template usage statistics"""
    template_id: str
    template_name: str
    usage_count: int
    last_used: Optional[datetime]
    total_revenue: float
    average_invoice_value: float
    most_recent_customers: List[Dict[str, str]]

# ==================== Database Functions ====================

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(DATABASE_URL)

# ==================== Template Management ====================

@router.post("/templates", tags=["Invoice Templates"])
async def create_invoice_template(template: CreateInvoiceTemplate):
    """Create new invoice template"""
    try:
        conn = await get_db_connection()
        try:
            # Begin transaction
            async with conn.transaction():
                # Create template
                template_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO invoice_templates (
                        id, template_name, description, category,
                        payment_terms, default_notes, tax_rate, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, template_id, template.template_name, template.description,
                    template.category.value if template.category else 'custom',
                    template.payment_terms, template.default_notes,
                    template.tax_rate, True)
                
                # Add template items
                for idx, item in enumerate(template.items):
                    item_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO invoice_template_items (
                            id, template_id, item_type, description,
                            default_quantity, default_price, tax_rate, sort_order
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, item_id, template_id, item.item_type, item.description,
                        item.default_quantity, item.default_price,
                        item.tax_rate, idx)
                
                return {
                    "success": True,
                    "template_id": template_id,
                    "message": f"Template '{template.template_name}' created successfully"
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", tags=["Invoice Templates"])
async def list_invoice_templates(
    category: Optional[TemplateCategory] = None,
    is_active: bool = True,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List invoice templates"""
    try:
        conn = await get_db_connection()
        try:
            # Build query
            query = """
                SELECT t.*, COUNT(DISTINCT i.id) as usage_count,
                       MAX(i.created_at) as last_used
                FROM invoice_templates t
                LEFT JOIN invoices i ON i.id::text LIKE '%template%' -- Simplified join
                WHERE t.is_active = $1
            """
            params = [is_active]
            param_count = 1
            
            if category:
                param_count += 1
                query += f" AND t.category = ${param_count}"
                params.append(category.value)
            
            if search:
                param_count += 1
                query += f" AND (t.template_name ILIKE ${param_count} OR t.description ILIKE ${param_count})"
                params.append(f"%{search}%")
            
            query += """
                GROUP BY t.id
                ORDER BY t.created_at DESC
                LIMIT $%d OFFSET $%d
            """ % (param_count + 1, param_count + 2)
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            templates = []
            for row in rows:
                # Get template items
                items = await conn.fetch("""
                    SELECT * FROM invoice_template_items
                    WHERE template_id = $1
                    ORDER BY sort_order
                """, row['id'])
                
                templates.append({
                    "id": str(row['id']),
                    "template_name": row['template_name'],
                    "description": row['description'],
                    "category": row['category'],
                    "payment_terms": row['payment_terms'],
                    "default_notes": row['default_notes'],
                    "tax_rate": float(row['tax_rate']) if row['tax_rate'] else 0,
                    "is_active": row['is_active'],
                    "usage_count": row['usage_count'],
                    "last_used": row['last_used'].isoformat() if row['last_used'] else None,
                    "items": [
                        {
                            "id": str(item['id']),
                            "item_type": item['item_type'],
                            "description": item['description'],
                            "default_quantity": float(item['default_quantity']),
                            "default_price": float(item['default_price']) if item['default_price'] else None,
                            "tax_rate": float(item['tax_rate']) if item['tax_rate'] else 0
                        }
                        for item in items
                    ],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            # Get total count
            count_query = """
                SELECT COUNT(*) FROM invoice_templates
                WHERE is_active = $1
            """
            if category:
                count_query += " AND category = $2"
                total = await conn.fetchval(count_query, is_active, category.value)
            else:
                total = await conn.fetchval(count_query, is_active)
            
            return {
                "templates": templates,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}", tags=["Invoice Templates"])
async def get_invoice_template(template_id: str):
    """Get invoice template details"""
    try:
        conn = await get_db_connection()
        try:
            # Get template
            row = await conn.fetchrow("""
                SELECT * FROM invoice_templates WHERE id = $1
            """, uuid.UUID(template_id))
            
            if not row:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Get template items
            items = await conn.fetch("""
                SELECT * FROM invoice_template_items
                WHERE template_id = $1
                ORDER BY sort_order
            """, uuid.UUID(template_id))
            
            # Get usage statistics
            stats = await conn.fetchrow("""
                SELECT COUNT(*) as usage_count,
                       MAX(created_at) as last_used,
                       SUM(total_cents) / 100.0 as total_revenue
                FROM invoices
                WHERE id::text LIKE $1
            """, f"%{template_id}%")
            
            return {
                "id": str(row['id']),
                "template_name": row['template_name'],
                "description": row['description'],
                "category": row['category'],
                "payment_terms": row['payment_terms'],
                "default_notes": row['default_notes'],
                "tax_rate": float(row['tax_rate']) if row['tax_rate'] else 0,
                "is_active": row['is_active'],
                "items": [
                    {
                        "id": str(item['id']),
                        "item_type": item['item_type'],
                        "description": item['description'],
                        "default_quantity": float(item['default_quantity']),
                        "default_price": float(item['default_price']) if item['default_price'] else None,
                        "tax_rate": float(item['tax_rate']) if item['tax_rate'] else 0,
                        "sort_order": item['sort_order']
                    }
                    for item in items
                ],
                "usage_stats": {
                    "usage_count": stats['usage_count'] if stats else 0,
                    "last_used": stats['last_used'].isoformat() if stats and stats['last_used'] else None,
                    "total_revenue": float(stats['total_revenue']) if stats and stats['total_revenue'] else 0
                },
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}", tags=["Invoice Templates"])
async def update_invoice_template(
    template_id: str,
    update: UpdateInvoiceTemplate
):
    """Update invoice template"""
    try:
        conn = await get_db_connection()
        try:
            # Check if template exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM invoice_templates WHERE id = $1)",
                uuid.UUID(template_id)
            )
            
            if not exists:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Build update query
            updates = []
            params = []
            param_count = 1
            
            if update.template_name is not None:
                updates.append(f"template_name = ${param_count}")
                params.append(update.template_name)
                param_count += 1
            
            if update.description is not None:
                updates.append(f"description = ${param_count}")
                params.append(update.description)
                param_count += 1
            
            if update.category is not None:
                updates.append(f"category = ${param_count}")
                params.append(update.category.value)
                param_count += 1
            
            if update.payment_terms is not None:
                updates.append(f"payment_terms = ${param_count}")
                params.append(update.payment_terms)
                param_count += 1
            
            if update.default_notes is not None:
                updates.append(f"default_notes = ${param_count}")
                params.append(update.default_notes)
                param_count += 1
            
            if update.tax_rate is not None:
                updates.append(f"tax_rate = ${param_count}")
                params.append(update.tax_rate)
                param_count += 1
            
            if update.is_active is not None:
                updates.append(f"is_active = ${param_count}")
                params.append(update.is_active)
                param_count += 1
            
            if updates:
                updates.append("updated_at = NOW()")
                query = f"""
                    UPDATE invoice_templates
                    SET {', '.join(updates)}
                    WHERE id = ${param_count}
                    RETURNING *
                """
                params.append(uuid.UUID(template_id))
                
                row = await conn.fetchrow(query, *params)
                
                return {
                    "success": True,
                    "message": "Template updated successfully",
                    "template": {
                        "id": str(row['id']),
                        "template_name": row['template_name'],
                        "category": row['category'],
                        "is_active": row['is_active']
                    }
                }
            else:
                return {
                    "success": True,
                    "message": "No updates provided"
                }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}", tags=["Invoice Templates"])
async def delete_invoice_template(template_id: str):
    """Delete invoice template (soft delete by deactivating)"""
    try:
        conn = await get_db_connection()
        try:
            # Soft delete by deactivating
            result = await conn.execute("""
                UPDATE invoice_templates
                SET is_active = false, updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(template_id))
            
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Template not found")
            
            return {
                "success": True,
                "message": "Template deactivated successfully"
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Template Items Management ====================

@router.post("/templates/{template_id}/items", tags=["Invoice Templates"])
async def add_template_item(
    template_id: str,
    item: InvoiceTemplateItem
):
    """Add item to template"""
    try:
        conn = await get_db_connection()
        try:
            # Check if template exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM invoice_templates WHERE id = $1)",
                uuid.UUID(template_id)
            )
            
            if not exists:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Get max sort order
            max_order = await conn.fetchval("""
                SELECT COALESCE(MAX(sort_order), -1) + 1
                FROM invoice_template_items
                WHERE template_id = $1
            """, uuid.UUID(template_id))
            
            # Add item
            item_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO invoice_template_items (
                    id, template_id, item_type, description,
                    default_quantity, default_price, tax_rate, sort_order
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, uuid.UUID(item_id), uuid.UUID(template_id),
                item.item_type, item.description,
                item.default_quantity, item.default_price,
                item.tax_rate, max_order)
            
            # Update template timestamp
            await conn.execute("""
                UPDATE invoice_templates
                SET updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(template_id))
            
            return {
                "success": True,
                "item_id": item_id,
                "message": "Item added to template"
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding template item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}/items/{item_id}", tags=["Invoice Templates"])
async def remove_template_item(template_id: str, item_id: str):
    """Remove item from template"""
    try:
        conn = await get_db_connection()
        try:
            # Delete item
            result = await conn.execute("""
                DELETE FROM invoice_template_items
                WHERE id = $1 AND template_id = $2
            """, uuid.UUID(item_id), uuid.UUID(template_id))
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Item not found")
            
            # Update template timestamp
            await conn.execute("""
                UPDATE invoice_templates
                SET updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(template_id))
            
            return {
                "success": True,
                "message": "Item removed from template"
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing template item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Invoice Generation from Template ====================

@router.post("/templates/{template_id}/generate-invoice", tags=["Invoice Templates"])
async def generate_invoice_from_template(
    template_id: str,
    request: InvoiceFromTemplate,
    background_tasks: BackgroundTasks
):
    """Generate invoice from template"""
    try:
        conn = await get_db_connection()
        try:
            # Get template
            template = await conn.fetchrow("""
                SELECT * FROM invoice_templates
                WHERE id = $1 AND is_active = true
            """, uuid.UUID(template_id))
            
            if not template:
                raise HTTPException(status_code=404, detail="Template not found or inactive")
            
            # Get template items or use overrides
            if request.override_items:
                items = request.override_items
            else:
                item_rows = await conn.fetch("""
                    SELECT * FROM invoice_template_items
                    WHERE template_id = $1
                    ORDER BY sort_order
                """, uuid.UUID(template_id))
                
                items = [
                    {
                        "item_type": item['item_type'],
                        "description": item['description'],
                        "quantity": float(item['default_quantity']),
                        "unit_price": float(item['default_price']) if item['default_price'] else 0,
                        "tax_rate": float(item['tax_rate']) if item['tax_rate'] else 0
                    }
                    for item in item_rows
                ]
            
            # Calculate totals
            subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in items)
            tax_amount = subtotal * (template['tax_rate'] / 100 if template['tax_rate'] else 0)
            total = subtotal + tax_amount
            
            # Generate invoice number
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Set dates
            issue_date = request.issue_date or date.today()
            if request.due_date:
                due_date = request.due_date
            elif template['payment_terms'] == 'Net 30':
                due_date = issue_date + timedelta(days=30)
            elif template['payment_terms'] == 'Net 15':
                due_date = issue_date + timedelta(days=15)
            elif template['payment_terms'] == 'Due on Receipt':
                due_date = issue_date
            else:
                due_date = issue_date + timedelta(days=30)
            
            # Combine notes
            notes = template['default_notes'] or ""
            if request.additional_notes:
                notes = f"{notes}\n\n{request.additional_notes}" if notes else request.additional_notes
            
            # Create invoice
            invoice_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO invoices (
                    id, invoice_number, customer_id, job_id,
                    title, description, invoice_date, due_date,
                    subtotal_cents, tax_cents, total_cents, balance_cents,
                    line_items, notes, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW())
            """, uuid.UUID(invoice_id), invoice_number,
                uuid.UUID(request.customer_id),
                uuid.UUID(request.job_id) if request.job_id else None,
                template['template_name'],
                template['description'],
                issue_date, due_date,
                int(subtotal * 100), int(tax_amount * 100),
                int(total * 100), int(total * 100),
                json.dumps(items), notes, 'draft')
            
            # Log activity
            await conn.execute("""
                INSERT INTO invoice_activities (
                    invoice_id, activity_type, description, metadata
                ) VALUES ($1, $2, $3, $4)
            """, uuid.UUID(invoice_id), 'created_from_template',
                f"Invoice created from template: {template['template_name']}",
                json.dumps({"template_id": template_id, "template_name": template['template_name']}))
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "total_amount": total,
                "due_date": due_date.isoformat(),
                "message": f"Invoice {invoice_number} generated from template"
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invoice from template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Template Categories & Statistics ====================

@router.get("/templates/categories", tags=["Invoice Templates"])
async def get_template_categories():
    """Get available template categories with counts"""
    try:
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT category, COUNT(*) as count,
                       COUNT(CASE WHEN is_active THEN 1 END) as active_count
                FROM invoice_templates
                GROUP BY category
                ORDER BY count DESC
            """)
            
            return {
                "categories": [
                    {
                        "category": row['category'],
                        "total_count": row['count'],
                        "active_count": row['active_count']
                    }
                    for row in rows
                ],
                "available_categories": [cat.value for cat in TemplateCategory]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/statistics", tags=["Invoice Templates"])
async def get_template_statistics():
    """Get template usage statistics"""
    try:
        conn = await get_db_connection()
        try:
            # Get overall statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT t.id) as total_templates,
                    COUNT(DISTINCT CASE WHEN t.is_active THEN t.id END) as active_templates,
                    COUNT(DISTINCT i.id) as invoices_from_templates,
                    SUM(i.total_cents) / 100.0 as total_revenue
                FROM invoice_templates t
                LEFT JOIN invoices i ON i.id::text LIKE '%template%'
            """)
            
            # Get most used templates
            most_used = await conn.fetch("""
                SELECT t.id, t.template_name, t.category,
                       COUNT(i.id) as usage_count,
                       SUM(i.total_cents) / 100.0 as revenue_generated
                FROM invoice_templates t
                LEFT JOIN invoices i ON i.id::text LIKE '%' || t.id::text || '%'
                WHERE t.is_active = true
                GROUP BY t.id, t.template_name, t.category
                HAVING COUNT(i.id) > 0
                ORDER BY usage_count DESC
                LIMIT 5
            """)
            
            # Get category distribution
            categories = await conn.fetch("""
                SELECT category, COUNT(*) as count
                FROM invoice_templates
                WHERE is_active = true
                GROUP BY category
                ORDER BY count DESC
            """)
            
            return {
                "summary": {
                    "total_templates": stats['total_templates'],
                    "active_templates": stats['active_templates'],
                    "invoices_generated": stats['invoices_from_templates'] or 0,
                    "total_revenue": float(stats['total_revenue']) if stats['total_revenue'] else 0
                },
                "most_used_templates": [
                    {
                        "id": str(row['id']),
                        "name": row['template_name'],
                        "category": row['category'],
                        "usage_count": row['usage_count'],
                        "revenue_generated": float(row['revenue_generated']) if row['revenue_generated'] else 0
                    }
                    for row in most_used
                ],
                "category_distribution": [
                    {
                        "category": row['category'],
                        "count": row['count']
                    }
                    for row in categories
                ]
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/duplicate/{template_id}", tags=["Invoice Templates"])
async def duplicate_template(template_id: str, new_name: str):
    """Duplicate an existing template"""
    try:
        conn = await get_db_connection()
        try:
            # Get original template
            original = await conn.fetchrow("""
                SELECT * FROM invoice_templates WHERE id = $1
            """, uuid.UUID(template_id))
            
            if not original:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Get original items
            original_items = await conn.fetch("""
                SELECT * FROM invoice_template_items
                WHERE template_id = $1
                ORDER BY sort_order
            """, uuid.UUID(template_id))
            
            # Create new template
            new_id = str(uuid.uuid4())
            
            async with conn.transaction():
                # Insert new template
                await conn.execute("""
                    INSERT INTO invoice_templates (
                        id, template_name, description, category,
                        payment_terms, default_notes, tax_rate, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, uuid.UUID(new_id), new_name,
                    f"Copy of {original['description']}" if original['description'] else None,
                    original['category'], original['payment_terms'],
                    original['default_notes'], original['tax_rate'], True)
                
                # Copy items
                for item in original_items:
                    item_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO invoice_template_items (
                            id, template_id, item_type, description,
                            default_quantity, default_price, tax_rate, sort_order
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, uuid.UUID(item_id), uuid.UUID(new_id),
                        item['item_type'], item['description'],
                        item['default_quantity'], item['default_price'],
                        item['tax_rate'], item['sort_order'])
            
            return {
                "success": True,
                "template_id": new_id,
                "message": f"Template duplicated as '{new_name}'"
            }
        finally:
            await conn.close()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating template: {str(e)} RETURNING * RETURNING * RETURNING * RETURNING *")
        raise HTTPException(status_code=500, detail=str(e))