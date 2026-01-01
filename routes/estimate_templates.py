"""
Estimate Templates System
Manages reusable estimate templates for quick quote generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/templates")

# ============================================================================
# TEMPLATE MODELS
# ============================================================================

class TemplateItem(BaseModel):
    description: str
    default_quantity: float = 1.0
    unit: str = "each"
    default_price: Optional[float] = None
    category: Optional[str] = None
    is_optional: bool = False
    sort_order: Optional[int] = 0

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    items: List[TemplateItem] = []
    base_estimate_id: Optional[str] = None
    copy_from_estimate: bool = False

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateItemUpdate(BaseModel):
    description: Optional[str] = None
    default_quantity: Optional[float] = None
    unit: Optional[str] = None
    default_price: Optional[float] = None
    category: Optional[str] = None
    is_optional: Optional[bool] = None
    sort_order: Optional[int] = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    is_active: bool
    use_count: int
    items_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime

# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TemplateResponse:
    """Create a new estimate template"""
    try:
        template_id = str(uuid4())

        # If copying from an existing estimate
        if template.copy_from_estimate and template.base_estimate_id:
            # Verify estimate exists
            estimate = db.execute(
                text("SELECT id FROM estimates WHERE id = :id"),
                {"id": template.base_estimate_id}
            ).fetchone()

            if not estimate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Base estimate not found"
                )

        # Create template
        result = db.execute(
            text("""
                INSERT INTO estimate_templates (
                    id, name, description, category,
                    base_estimate_id, is_active, use_count,
                    created_by, created_at, updated_at
                )
                VALUES (
                    :id, :name, :description, :category,
                    :base_estimate_id, true, 0,
                    :created_by, NOW(), NOW()
                )
                RETURNING *
            """),
            {
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "base_estimate_id": template.base_estimate_id,
                "created_by": current_user["id"]
            }
        )

        # Add template items
        if template.copy_from_estimate and template.base_estimate_id:
            # Copy items from estimate
            db.execute(
                text("""
                    INSERT INTO estimate_template_items (
                        id, template_id, description, default_quantity,
                        unit, default_price, category, is_optional, sort_order
                    )
                    SELECT
                        gen_random_uuid(), :template_id, description, quantity,
                        unit, unit_price, NULL, false, 0
                    FROM estimate_line_items
                    WHERE estimate_id = :estimate_id
                    ORDER BY created_at
                """),
                {
                    "template_id": template_id,
                    "estimate_id": template.base_estimate_id
                }
            )
        else:
            # Add new items
            for idx, item in enumerate(template.items):
                db.execute(
                    text("""
                        INSERT INTO estimate_template_items (
                            id, template_id, description, default_quantity,
                            unit, default_price, category, is_optional,
                            sort_order, created_at
                        )
                        VALUES (
                            gen_random_uuid(), :template_id, :description, :quantity,
                            :unit, :price, :category, :is_optional,
                            :sort_order, NOW()
                        )
                    """),
                    {
                        "template_id": template_id,
                        "description": item.description,
                        "quantity": item.default_quantity,
                        "unit": item.unit,
                        "price": item.default_price,
                        "category": item.category,
                        "is_optional": item.is_optional,
                        "sort_order": item.sort_order or idx
                    }
                )

        db.commit()

        # Get item count
        items_count = db.execute(
            text("SELECT COUNT(*) FROM estimate_template_items WHERE template_id = :id"),
            {"id": template_id}
        ).scalar()

        template_data = result.fetchone()

        return TemplateResponse(
            id=template_id,
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            is_active=template_data.is_active,
            use_count=0,
            items_count=items_count,
            created_by=str(template_data.created_by),
            created_at=template_data.created_at,
            updated_at=template_data.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )

@router.get("/", response_model=Dict[str, Any])
async def list_templates(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """List available estimate templates"""
    try:
        # TENANT ISOLATION: Get tenant_id from authenticated user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant context required")

        # Build query with tenant isolation
        query = """
            SELECT
                t.*,
                u.email as created_by_email,
                u.full_name as created_by_name,
                COUNT(ti.id) as items_count,
                COALESCE(SUM(ti.default_price * ti.default_quantity), 0) as estimated_value
            FROM estimate_templates t
            LEFT JOIN users u ON t.created_by = u.id
            LEFT JOIN estimate_template_items ti ON t.id = ti.template_id
            WHERE t.tenant_id = :tenant_id
        """
        params = {"tenant_id": tenant_id}

        if category:
            query += " AND t.category = :category"
            params["category"] = category

        if is_active is not None:
            query += " AND t.is_active = :is_active"
            params["is_active"] = is_active

        if search:
            query += " AND (t.name ILIKE :search OR t.description ILIKE :search)"
            params["search"] = f"%{search}%"

        query += " GROUP BY t.id, u.email, u.full_name"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()

        # Get templates
        query += " ORDER BY t.use_count DESC, t.created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params)
        templates = []

        for row in result:
            templates.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "is_active": row.is_active,
                "use_count": row.use_count,
                "items_count": row.items_count,
                "estimated_value": float(row.estimated_value),
                "created_by": str(row.created_by),
                "created_by_email": row.created_by_email,
                "created_by_name": row.created_by_name,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat()
            })

        # Get categories
        categories_result = db.execute(
            text("""
                SELECT DISTINCT category, COUNT(*) as count
                FROM estimate_templates
                WHERE category IS NOT NULL AND is_active = true
                GROUP BY category
                ORDER BY count DESC
            """)
        )

        categories = []
        for cat in categories_result:
            categories.append({
                "name": cat.category,
                "count": cat.count
            })

        return {
            "total": total,
            "templates": templates,
            "categories": categories,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )

@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_template_details(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get detailed template information"""
    try:
        # Get template
        result = db.execute(
            text("""
                SELECT
                    t.*,
                    u.email as created_by_email,
                    u.full_name as created_by_name
                FROM estimate_templates t
                LEFT JOIN users u ON t.created_by = u.id
                WHERE t.id = :id
            """),
            {"id": template_id}
        )

        template = result.fetchone()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Get template items
        items_result = db.execute(
            text("""
                SELECT * FROM estimate_template_items
                WHERE template_id = :template_id
                ORDER BY sort_order, created_at
            """),
            {"template_id": template_id}
        )

        items = []
        total_value = 0

        for item in items_result:
            item_value = (item.default_price or 0) * item.default_quantity
            total_value += item_value

            items.append({
                "id": str(item.id),
                "description": item.description,
                "default_quantity": float(item.default_quantity),
                "unit": item.unit,
                "default_price": float(item.default_price) if item.default_price else None,
                "category": item.category,
                "is_optional": item.is_optional,
                "sort_order": item.sort_order,
                "estimated_value": item_value
            })

        # Get usage history
        usage_result = db.execute(
            text("""
                SELECT
                    e.id,
                    e.estimate_number,
                    e.title,
                    e.total_amount,
                    e.created_at,
                    c.name as customer_name
                FROM estimates e
                JOIN customers c ON e.customer_id = c.id
                WHERE e.id IN (
                    SELECT base_estimate_id
                    FROM estimate_templates
                    WHERE id = :template_id
                )
                OR e.created_from_template_id = :template_id
                ORDER BY e.created_at DESC
                LIMIT 10
            """),
            {"template_id": template_id}
        )

        usage_history = []
        for usage in usage_result:
            usage_history.append({
                "estimate_id": str(usage.id),
                "estimate_number": usage.estimate_number,
                "title": usage.title,
                "customer_name": usage.customer_name,
                "total_amount": float(usage.total_amount),
                "created_at": usage.created_at.isoformat()
            })

        return {
            "template": {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "is_active": template.is_active,
                "use_count": template.use_count,
                "base_estimate_id": str(template.base_estimate_id) if template.base_estimate_id else None,
                "created_by": str(template.created_by),
                "created_by_email": template.created_by_email,
                "created_by_name": template.created_by_name,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            },
            "items": items,
            "total_estimated_value": total_value,
            "usage_history": usage_history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template details: {str(e)}"
        )

@router.put("/{template_id}", response_model=dict)
async def update_template(
    template_id: str,
    update: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update template details"""
    try:
        # Check if template exists
        existing = db.execute(
            text("SELECT id FROM estimate_templates WHERE id = :id"),
            {"id": template_id}
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Build update query
        update_fields = []
        params = {"id": template_id}

        if update.name is not None:
            update_fields.append("name = :name")
            params["name"] = update.name

        if update.description is not None:
            update_fields.append("description = :description")
            params["description"] = update.description

        if update.category is not None:
            update_fields.append("category = :category")
            params["category"] = update.category

        if update.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = update.is_active

        update_fields.append("updated_at = NOW()")

        # Execute update
        db.execute(
            text(f"""
                UPDATE estimate_templates
                SET {', '.join(update_fields)}
                WHERE id = :id
            """),
            params
        )

        db.commit()

        return {"message": "Template updated successfully", "id": template_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )

@router.post("/{template_id}/items", response_model=dict)
async def add_template_item(
    template_id: str,
    item: TemplateItem,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Add item to template"""
    try:
        # Verify template exists
        template = db.execute(
            text("SELECT id FROM estimate_templates WHERE id = :id"),
            {"id": template_id}
        ).fetchone()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Add item
        item_id = str(uuid4())

        db.execute(
            text("""
                INSERT INTO estimate_template_items (
                    id, template_id, description, default_quantity,
                    unit, default_price, category, is_optional,
                    sort_order, created_at
                )
                VALUES (
                    :id, :template_id, :description, :quantity,
                    :unit, :price, :category, :is_optional,
                    :sort_order, NOW()
                )
            """),
            {
                "id": item_id,
                "template_id": template_id,
                "description": item.description,
                "quantity": item.default_quantity,
                "unit": item.unit,
                "price": item.default_price,
                "category": item.category,
                "is_optional": item.is_optional,
                "sort_order": item.sort_order
            }
        )

        # Update template timestamp
        db.execute(
            text("UPDATE estimate_templates SET updated_at = NOW() WHERE id = :id"),
            {"id": template_id}
        )

        db.commit()

        return {"message": "Item added successfully", "item_id": item_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add item: {str(e)}"
        )

@router.put("/{template_id}/items/{item_id}", response_model=dict)
async def update_template_item(
    template_id: str,
    item_id: str,
    update: TemplateItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Update template item"""
    try:
        # Verify item exists
        existing = db.execute(
            text("""
                SELECT id FROM estimate_template_items
                WHERE id = :id AND template_id = :template_id
            """),
            {"id": item_id, "template_id": template_id}
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template item not found"
            )

        # Build update query
        update_fields = []
        params = {"id": item_id}

        if update.description is not None:
            update_fields.append("description = :description")
            params["description"] = update.description

        if update.default_quantity is not None:
            update_fields.append("default_quantity = :quantity")
            params["quantity"] = update.default_quantity

        if update.unit is not None:
            update_fields.append("unit = :unit")
            params["unit"] = update.unit

        if update.default_price is not None:
            update_fields.append("default_price = :price")
            params["price"] = update.default_price

        if update.category is not None:
            update_fields.append("category = :category")
            params["category"] = update.category

        if update.is_optional is not None:
            update_fields.append("is_optional = :is_optional")
            params["is_optional"] = update.is_optional

        if update.sort_order is not None:
            update_fields.append("sort_order = :sort_order")
            params["sort_order"] = update.sort_order

        # Execute update
        db.execute(
            text(f"""
                UPDATE estimate_template_items
                SET {', '.join(update_fields)}
                WHERE id = :id
            """),
            params
        )

        # Update template timestamp
        db.execute(
            text("UPDATE estimate_templates SET updated_at = NOW() WHERE id = :id"),
            {"id": template_id}
        )

        db.commit()

        return {"message": "Item updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )

@router.delete("/{template_id}/items/{item_id}", response_model=dict)
async def delete_template_item(
    template_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete template item"""
    try:
        # Delete item
        result = db.execute(
            text("""
                DELETE FROM estimate_template_items
                WHERE id = :id AND template_id = :template_id
            """),
            {"id": item_id, "template_id": template_id}
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template item not found"
            )

        # Update template timestamp
        db.execute(
            text("UPDATE estimate_templates SET updated_at = NOW() WHERE id = :id"),
            {"id": template_id}
        )

        db.commit()

        return {"message": "Item deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )

@router.post("/{template_id}/create-estimate", response_model=dict)
async def create_estimate_from_template(
    template_id: str,
    customer_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    apply_optional_items: bool = False,
    price_adjustment_percent: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Create an estimate from a template"""
    try:
        # Get template
        template = db.execute(
            text("SELECT * FROM estimate_templates WHERE id = :id AND is_active = true"),
            {"id": template_id}
        ).fetchone()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )

        # Verify customer
        customer = db.execute(
            text("SELECT id, name FROM customers WHERE id = :id"),
            {"id": customer_id}
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

        # Create estimate
        estimate_id = str(uuid4())

        db.execute(
            text("""
                INSERT INTO estimates (
                    id, estimate_number, customer_id,
                    title, description, status,
                    created_from_template_id, created_by,
                    created_at, updated_at
                )
                VALUES (
                    :id, :estimate_number, :customer_id,
                    :title, :description, 'draft',
                    :template_id, :created_by,
                    NOW(), NOW()
                )
            """),
            {
                "id": estimate_id,
                "estimate_number": estimate_number,
                "customer_id": customer_id,
                "title": title or template.name,
                "description": description or template.description,
                "template_id": template_id,
                "created_by": current_user["id"]
            }
        )

        # Add line items from template
        items_query = """
            INSERT INTO estimate_line_items (
                id, estimate_id, description, quantity, unit,
                unit_price, line_total, created_at
            )
            SELECT
                gen_random_uuid(), :estimate_id, description,
                default_quantity, unit,
                default_price * COALESCE(:adjustment, 1.0),
                default_quantity * default_price * COALESCE(:adjustment, 1.0),
                NOW()
            FROM estimate_template_items
            WHERE template_id = :template_id
        """

        params = {
            "estimate_id": estimate_id,
            "template_id": template_id,
            "adjustment": 1 + (price_adjustment_percent or 0) / 100
        }

        if not apply_optional_items:
            items_query += " AND is_optional = false"

        db.execute(text(items_query), params)

        # Update template use count
        db.execute(
            text("""
                UPDATE estimate_templates
                SET use_count = use_count + 1,
                    updated_at = NOW()
                WHERE id = :id
            """),
            {"id": template_id}
        )

        db.commit()

        return {
            "message": "Estimate created from template successfully",
            "estimate_id": estimate_id,
            "estimate_number": estimate_number,
            "customer_name": customer.name
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create estimate from template: {str(e)}"
        )

@router.get("/categories/list", response_model=List[Dict[str, Any]])
async def list_template_categories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all template categories with counts"""
    try:
        result = db.execute(
            text("""
                SELECT
                    category,
                    COUNT(*) as template_count,
                    SUM(use_count) as total_uses,
                    AVG(use_count) as avg_uses
                FROM estimate_templates
                WHERE category IS NOT NULL AND is_active = true
                GROUP BY category
                ORDER BY template_count DESC
            """)
        )

        categories = []
        for row in result:
            categories.append({
                "name": row.category,
                "template_count": row.template_count,
                "total_uses": row.total_uses or 0,
                "avg_uses": round(row.avg_uses or 0, 1)
            })

        return categories

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)} RETURNING * RETURNING *"
        )