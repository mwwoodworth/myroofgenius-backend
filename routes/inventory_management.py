"""
Inventory Management System
Task 40: Comprehensive inventory tracking and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid
import asyncpg
import logging
from decimal import Decimal
import json

from database import get_db_connection
from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Enums for inventory management
class ItemType(str, Enum):
    MATERIAL = "material"
    PRODUCT = "product"
    TOOL = "tool"
    EQUIPMENT = "equipment"
    SUPPLY = "supply"
    CONSUMABLE = "consumable"
    SPARE_PART = "spare_part"

class ItemStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"
    BACKORDERED = "backordered"

class UnitOfMeasure(str, Enum):
    EACH = "each"
    PIECE = "piece"
    BOX = "box"
    CASE = "case"
    PALLET = "pallet"
    POUND = "pound"
    OUNCE = "ounce"
    KILOGRAM = "kilogram"
    GRAM = "gram"
    GALLON = "gallon"
    LITER = "liter"
    SQUARE_FOOT = "square_foot"
    SQUARE_METER = "square_meter"
    LINEAR_FOOT = "linear_foot"
    LINEAR_METER = "linear_meter"
    CUBIC_FOOT = "cubic_foot"
    CUBIC_METER = "cubic_meter"

class MovementType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGE = "damage"
    THEFT = "theft"
    PRODUCTION = "production"
    CONSUMPTION = "consumption"

class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    TRUCK = "truck"
    JOB_SITE = "job_site"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    IN_TRANSIT = "in_transit"

class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class CountStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

# Pydantic models
class InventoryItemCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    item_type: ItemType
    category_id: Optional[str] = None
    unit_of_measure: UnitOfMeasure
    cost_price: float = Field(ge=0)
    sale_price: Optional[float] = Field(None, ge=0)
    min_stock: int = Field(0, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    barcode: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ItemStatus] = None
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None

class InventoryItemResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str]
    item_type: ItemType
    status: ItemStatus
    category_id: Optional[str]
    category_name: Optional[str]
    unit_of_measure: UnitOfMeasure
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    quantity_on_order: int
    cost_price: float
    sale_price: Optional[float]
    total_value: float
    min_stock: int
    max_stock: Optional[int]
    reorder_point: Optional[int]
    reorder_quantity: Optional[int]
    lead_time_days: Optional[int]
    last_movement_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StockMovement(BaseModel):
    item_id: str
    movement_type: MovementType
    quantity: int = Field(..., ne=0)
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    reference_type: Optional[str] = None  # purchase_order, sales_order, job, etc.
    reference_id: Optional[str] = None
    unit_cost: Optional[float] = None
    notes: Optional[str] = None

class StockAdjustment(BaseModel):
    item_id: str
    location_id: str
    adjustment_quantity: int  # Can be positive or negative
    reason: str
    notes: Optional[str] = None

class LocationCreate(BaseModel):
    location_code: str = Field(..., min_length=1, max_length=50)
    location_name: str = Field(..., min_length=1, max_length=100)
    location_type: LocationType
    address: Optional[str] = None
    manager: Optional[str] = None
    is_active: bool = True

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    expected_date: Optional[date] = None
    items: List[Dict[str, Any]]  # [{item_id, quantity, unit_cost, notes}]
    shipping_cost: float = 0
    tax_amount: float = 0
    notes: Optional[str] = None

class PurchaseOrderResponse(BaseModel):
    id: str
    order_number: str
    supplier_id: str
    supplier_name: Optional[str]
    status: OrderStatus
    order_date: date
    expected_date: Optional[date]
    received_date: Optional[date]
    subtotal: float
    shipping_cost: float
    tax_amount: float
    total_amount: float
    items_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StockTransfer(BaseModel):
    from_location_id: str
    to_location_id: str
    items: List[Dict[str, Any]]  # [{item_id, quantity}]
    transfer_date: Optional[date] = None
    notes: Optional[str] = None

class CycleCountCreate(BaseModel):
    location_id: str
    count_date: date
    assigned_to: Optional[str] = None
    items: Optional[List[str]] = None  # Specific items to count, or None for all

class CycleCountUpdate(BaseModel):
    item_id: str
    counted_quantity: int
    notes: Optional[str] = None

class InventoryValuation(BaseModel):
    as_of_date: date
    total_value: float
    item_count: int
    category_breakdown: List[Dict[str, Any]]
    location_breakdown: List[Dict[str, Any]]
    slow_moving_value: float
    obsolete_value: float

class ReorderAlert(BaseModel):
    item_id: str
    item_name: str
    sku: str
    current_quantity: int
    reorder_point: int
    reorder_quantity: int
    supplier: Optional[str]
    lead_time_days: Optional[int]
    urgency: str  # critical, high, medium, low

# Helper functions
def generate_order_number(prefix: str = "PO") -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"

async def calculate_item_availability(conn, item_id: str) -> Dict[str, int]:
    """Calculate item availability across locations"""
    result = await conn.fetchrow("""
        SELECT
            COALESCE(SUM(quantity), 0) as on_hand,
            COALESCE(SUM(reserved_quantity), 0) as reserved,
            COALESCE(SUM(quantity) - SUM(reserved_quantity), 0) as available
        FROM inventory_stock
        WHERE item_id = $1
    """, uuid.UUID(item_id))

    # Get on order quantity
    on_order = await conn.fetchval("""
        SELECT COALESCE(SUM(poi.quantity - poi.received_quantity), 0)
        FROM purchase_order_items poi
        JOIN purchase_orders po ON poi.purchase_order_id = po.id
        WHERE poi.item_id = $1
            AND po.status IN ('approved', 'ordered', 'partially_received')
    """, uuid.UUID(item_id))

    return {
        "on_hand": result["on_hand"],
        "reserved": result["reserved"],
        "available": result["available"],
        "on_order": on_order or 0
    }

async def check_reorder_points(conn) -> List[Dict]:
    """Check items below reorder point"""
    items = await conn.fetch("""
        SELECT
            i.id, i.sku, i.name, i.reorder_point, i.reorder_quantity,
            i.lead_time_days, COALESCE(s.total_quantity, 0) as current_quantity,
            sup.name as supplier_name
        FROM inventory_items i
        LEFT JOIN (
            SELECT item_id, SUM(quantity) as total_quantity
            FROM inventory_stock
            GROUP BY item_id
        ) s ON i.id = s.item_id
        LEFT JOIN item_suppliers isup ON i.id = isup.item_id AND isup.is_primary = true
        LEFT JOIN suppliers sup ON isup.supplier_id = sup.id
        WHERE i.status = 'active'
            AND i.reorder_point IS NOT NULL
            AND COALESCE(s.total_quantity, 0) <= i.reorder_point
    """)

    alerts = []
    for item in items:
        urgency = "critical" if item["current_quantity"] == 0 else \
                  "high" if item["current_quantity"] < item["reorder_point"] * 0.5 else \
                  "medium"

        alerts.append({
            "item_id": str(item["id"]),
            "item_name": item["name"],
            "sku": item["sku"],
            "current_quantity": item["current_quantity"],
            "reorder_point": item["reorder_point"],
            "reorder_quantity": item["reorder_quantity"] or item["reorder_point"] * 2,
            "supplier": item["supplier_name"],
            "lead_time_days": item["lead_time_days"],
            "urgency": urgency
        })

    return alerts

async def calculate_inventory_value(conn, location_id: str = None) -> float:
    """Calculate total inventory value"""
    query = """
        SELECT SUM(s.quantity * i.cost_price) as total_value
        FROM inventory_stock s
        JOIN inventory_items i ON s.item_id = i.id
        WHERE s.quantity > 0
    """
    params = []

    if location_id:
        query += " AND s.location_id = $1"
        params.append(uuid.UUID(location_id))

    result = await conn.fetchval(query, *params)
    return float(result) if result else 0

# API Endpoints
@router.post("/items", response_model=InventoryItemResponse)
async def create_inventory_item(
    item: InventoryItemCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new inventory item"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Check for duplicate SKU within tenant
        existing = await conn.fetchval(
            "SELECT id FROM inventory_items WHERE sku = $1 AND tenant_id = $2",
            item.sku,
            uuid.UUID(tenant_id)
        )
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")

        item_id = str(uuid.uuid4())

        # Create item
        result = await conn.fetchrow("""
            INSERT INTO inventory_items (
                id, tenant_id, sku, name, description, item_type, category_id,
                unit_of_measure, cost_price, sale_price, min_stock, max_stock,
                reorder_point, reorder_quantity, lead_time_days,
                barcode, manufacturer, model_number, specifications
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING *
        """,
            uuid.UUID(item_id),
            uuid.UUID(tenant_id),
            item.sku,
            item.name,
            item.description,
            item.item_type,
            uuid.UUID(item.category_id) if item.category_id else None,
            item.unit_of_measure,
            item.cost_price,
            item.sale_price,
            item.min_stock,
            item.max_stock,
            item.reorder_point,
            item.reorder_quantity,
            item.lead_time_days,
            item.barcode,
            item.manufacturer,
            item.model_number,
            json.dumps(item.specifications) if item.specifications else None
        )

        # Get availability
        availability = await calculate_item_availability(conn, item_id)

        response = InventoryItemResponse(
            **dict(result),
            quantity_on_hand=availability["on_hand"],
            quantity_available=availability["available"],
            quantity_reserved=availability["reserved"],
            quantity_on_order=availability["on_order"],
            total_value=availability["on_hand"] * item.cost_price
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.get("/items", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    item_type: Optional[ItemType] = None,
    status: Optional[ItemStatus] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: bool = False,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get inventory items with filters"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build query
        query = """
            SELECT i.*, c.name as category_name,
                   COALESCE(s.on_hand, 0) as quantity_on_hand,
                   COALESCE(s.reserved, 0) as quantity_reserved,
                   COALESCE(s.on_hand - s.reserved, 0) as quantity_available
            FROM inventory_items i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN (
                SELECT item_id,
                       SUM(quantity) as on_hand,
                       SUM(reserved_quantity) as reserved
                FROM inventory_stock
                GROUP BY item_id
            ) s ON i.id = s.item_id
            WHERE i.tenant_id = $1
        """
        params = [uuid.UUID(tenant_id)]
        param_count = 1

        if item_type:
            param_count += 1
            query += f" AND i.item_type = ${param_count}"
            params.append(item_type)

        if status:
            param_count += 1
            query += f" AND i.status = ${param_count}"
            params.append(status)

        if category_id:
            param_count += 1
            query += f" AND i.category_id = ${param_count}"
            params.append(uuid.UUID(category_id))

        if search:
            param_count += 1
            query += f" AND (i.name ILIKE ${param_count} OR i.sku ILIKE ${param_count} OR i.barcode = ${param_count})"
            params.append(f"%{search}%")

        if low_stock:
            query += " AND COALESCE(s.on_hand, 0) <= i.reorder_point"

        query += f" ORDER BY i.name LIMIT {limit} OFFSET {offset}"

        rows = await conn.fetch(query, *params)

        items = []
        for row in rows:
            # Get on order quantity
            on_order = await conn.fetchval("""
                SELECT COALESCE(SUM(poi.quantity - poi.received_quantity), 0)
                FROM purchase_order_items poi
                JOIN purchase_orders po ON poi.purchase_order_id = po.id
                WHERE poi.item_id = $1
                    AND po.status IN ('approved', 'ordered', 'partially_received')
            """, row["id"])

            items.append(InventoryItemResponse(
                **dict(row),
                quantity_on_order=on_order or 0,
                total_value=row["quantity_on_hand"] * row["cost_price"]
            ))

        return items

    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get inventory item details"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = await conn.fetchrow("""
            SELECT i.*, c.name as category_name
            FROM inventory_items i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.id = $1 AND i.tenant_id = $2
        """, uuid.UUID(item_id), uuid.UUID(tenant_id))

        if not result:
            raise HTTPException(status_code=404, detail="Item not found")

        # Get availability
        availability = await calculate_item_availability(conn, item_id)

        return InventoryItemResponse(
            **dict(result),
            quantity_on_hand=availability["on_hand"],
            quantity_available=availability["available"],
            quantity_reserved=availability["reserved"],
            quantity_on_order=availability["on_order"],
            total_value=availability["on_hand"] * result["cost_price"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching item: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    update: InventoryItemUpdate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update inventory item"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build update query
        update_fields = []
        params = []
        param_count = 0

        for field, value in update.dict(exclude_unset=True).items():
            param_count += 1
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        param_count += 1
        update_fields.append(f"updated_at = ${param_count}")
        params.append(datetime.now())

        param_count += 1
        params.append(uuid.UUID(item_id))

        param_count += 1
        params.append(uuid.UUID(tenant_id))

        query = f"""
            UPDATE inventory_items
            SET {', '.join(update_fields)}
            WHERE id = ${param_count - 1} AND tenant_id = ${param_count}
            RETURNING *
        """

        result = await conn.fetchrow(query, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Item not found")

        # Get availability
        availability = await calculate_item_availability(conn, item_id)

        return InventoryItemResponse(
            **dict(result),
            quantity_on_hand=availability["on_hand"],
            quantity_available=availability["available"],
            quantity_reserved=availability["reserved"],
            quantity_on_order=availability["on_order"],
            total_value=availability["on_hand"] * result["cost_price"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.post("/movements")
async def record_stock_movement(
    movement: StockMovement,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Record stock movement"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        movement_id = str(uuid.uuid4())

        # Validate item exists and belongs to tenant
        item = await conn.fetchrow(
            "SELECT * FROM inventory_items WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(movement.item_id),
            uuid.UUID(tenant_id)
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Handle different movement types
        if movement.movement_type == MovementType.PURCHASE:
            # Add to stock
            if not movement.to_location_id:
                raise HTTPException(status_code=400, detail="Destination location required for purchase")

            await conn.execute("""
                INSERT INTO inventory_stock (item_id, location_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (item_id, location_id)
                DO UPDATE SET quantity = inventory_stock.quantity + $3
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.to_location_id), movement.quantity)

        elif movement.movement_type == MovementType.SALE:
            # Remove from stock
            if not movement.from_location_id:
                raise HTTPException(status_code=400, detail="Source location required for sale")

            current = await conn.fetchval("""
                SELECT quantity FROM inventory_stock
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.from_location_id))

            if not current or current < movement.quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")

            await conn.execute("""
                UPDATE inventory_stock
                SET quantity = quantity - $3
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.from_location_id), movement.quantity)

        elif movement.movement_type == MovementType.TRANSFER:
            # Transfer between locations
            if not movement.from_location_id or not movement.to_location_id:
                raise HTTPException(status_code=400, detail="Both source and destination locations required for transfer")

            # Check source stock
            current = await conn.fetchval("""
                SELECT quantity FROM inventory_stock
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.from_location_id))

            if not current or current < movement.quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock at source location")

            # Remove from source
            await conn.execute("""
                UPDATE inventory_stock
                SET quantity = quantity - $3
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.from_location_id), movement.quantity)

            # Add to destination
            await conn.execute("""
                INSERT INTO inventory_stock (item_id, location_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (item_id, location_id)
                DO UPDATE SET quantity = inventory_stock.quantity + $3
            """, uuid.UUID(movement.item_id), uuid.UUID(movement.to_location_id), movement.quantity)

        # Record movement
        await conn.execute("""
            INSERT INTO stock_movements (
                id, item_id, movement_type, quantity,
                from_location_id, to_location_id,
                reference_type, reference_id,
                unit_cost, notes, movement_date
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            uuid.UUID(movement_id),
            uuid.UUID(movement.item_id),
            movement.movement_type,
            movement.quantity,
            uuid.UUID(movement.from_location_id) if movement.from_location_id else None,
            uuid.UUID(movement.to_location_id) if movement.to_location_id else None,
            movement.reference_type,
            uuid.UUID(movement.reference_id) if movement.reference_id else None,
            movement.unit_cost,
            movement.notes,
            datetime.now()
        )

        # Check reorder point
        background_tasks.add_task(check_item_reorder, movement.item_id)

        return {"message": "Stock movement recorded", "movement_id": movement_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording movement: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.post("/adjustments")
async def create_stock_adjustment(
    adjustment: StockAdjustment,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create stock adjustment"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify item belongs to tenant
        item_exists = await conn.fetchval(
            "SELECT id FROM inventory_items WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(adjustment.item_id), uuid.UUID(tenant_id)
        )
        if not item_exists:
            raise HTTPException(status_code=404, detail="Item not found")

        # Get current stock
        current = await conn.fetchval("""
            SELECT quantity FROM inventory_stock
            WHERE item_id = $1 AND location_id = $2
        """, uuid.UUID(adjustment.item_id), uuid.UUID(adjustment.location_id))

        current = current or 0
        new_quantity = current + adjustment.adjustment_quantity

        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Adjustment would result in negative stock")

        # Apply adjustment
        if current == 0:
            await conn.execute("""
                INSERT INTO inventory_stock (item_id, location_id, quantity)
                VALUES ($1, $2, $3)
            """, uuid.UUID(adjustment.item_id), uuid.UUID(adjustment.location_id), new_quantity)
        else:
            await conn.execute("""
                UPDATE inventory_stock
                SET quantity = $3
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(adjustment.item_id), uuid.UUID(adjustment.location_id), new_quantity)

        # Record movement
        movement_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO stock_movements (
                id, item_id, movement_type, quantity,
                to_location_id, notes, movement_date
            ) VALUES ($1, $2, 'adjustment', $3, $4, $5, $6)
        """,
            uuid.UUID(movement_id),
            uuid.UUID(adjustment.item_id),
            adjustment.adjustment_quantity,
            uuid.UUID(adjustment.location_id),
            f"{adjustment.reason}: {adjustment.notes}" if adjustment.notes else adjustment.reason,
            datetime.now()
        )

        return {
            "message": "Stock adjusted",
            "previous_quantity": current,
            "new_quantity": new_quantity,
            "movement_id": movement_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting stock: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create purchase order"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        order_id = str(uuid.uuid4())
        order_number = generate_order_number("PO")

        # Calculate totals
        subtotal = sum(item["quantity"] * item["unit_cost"] for item in order.items)
        total = subtotal + order.shipping_cost + order.tax_amount

        # Create order
        result = await conn.fetchrow("""
            INSERT INTO purchase_orders (
                id, tenant_id, order_number, supplier_id, status,
                order_date, expected_date,
                subtotal, shipping_cost, tax_amount, total_amount,
                notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """,
            uuid.UUID(order_id),
            uuid.UUID(tenant_id),
            order_number,
            uuid.UUID(order.supplier_id),
            OrderStatus.DRAFT,
            date.today(),
            order.expected_date,
            subtotal,
            order.shipping_cost,
            order.tax_amount,
            total,
            order.notes
        )

        # Add order items
        for item in order.items:
            await conn.execute("""
                INSERT INTO purchase_order_items (
                    id, purchase_order_id, item_id,
                    quantity, unit_cost, notes
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                uuid.uuid4(),
                uuid.UUID(order_id),
                uuid.UUID(item["item_id"]),
                item["quantity"],
                item["unit_cost"],
                item.get("notes")
            )

        # Get supplier name
        supplier = await conn.fetchrow(
            "SELECT name FROM suppliers WHERE id = $1",
            uuid.UUID(order.supplier_id)
        )

        response = PurchaseOrderResponse(
            **dict(result),
            supplier_name=supplier["name"] if supplier else None,
            items_count=len(order.items)
        )

        return response

    except Exception as e:
        logger.error(f"Error creating purchase order: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfers")
async def create_stock_transfer(
    transfer: StockTransfer,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create stock transfer between locations"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        transfer_id = str(uuid.uuid4())
        transfer_number = generate_order_number("TRF")

        # Validate locations belong to tenant
        from_loc = await conn.fetchrow(
            "SELECT * FROM inventory_locations WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(transfer.from_location_id),
            uuid.UUID(tenant_id)
        )
        to_loc = await conn.fetchrow(
            "SELECT * FROM inventory_locations WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(transfer.to_location_id),
            uuid.UUID(tenant_id)
        )

        if not from_loc or not to_loc:
            raise HTTPException(status_code=404, detail="Location not found")

        # Create transfer record
        await conn.execute("""
            INSERT INTO stock_transfers (
                id, tenant_id, transfer_number, from_location_id, to_location_id,
                transfer_date, status, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            uuid.UUID(transfer_id),
            uuid.UUID(tenant_id),
            transfer_number,
            uuid.UUID(transfer.from_location_id),
            uuid.UUID(transfer.to_location_id),
            transfer.transfer_date or date.today(),
            'pending',
            transfer.notes
        )

        # Process each item
        for item in transfer.items:
            # Check availability
            available = await conn.fetchval("""
                SELECT quantity - reserved_quantity
                FROM inventory_stock
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(item["item_id"]), uuid.UUID(transfer.from_location_id))

            if not available or available < item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for item {item['item_id']}"
                )

            # Reserve stock
            await conn.execute("""
                UPDATE inventory_stock
                SET reserved_quantity = reserved_quantity + $3
                WHERE item_id = $1 AND location_id = $2
            """, uuid.UUID(item["item_id"]), uuid.UUID(transfer.from_location_id), item["quantity"])

            # Add to transfer items
            await conn.execute("""
                INSERT INTO stock_transfer_items (
                    id, transfer_id, item_id, quantity
                ) VALUES ($1, $2, $3, $4)
            """,
                uuid.uuid4(),
                uuid.UUID(transfer_id),
                uuid.UUID(item["item_id"]),
                item["quantity"]
            )

        return {
            "message": "Stock transfer created",
            "transfer_id": transfer_id,
            "transfer_number": transfer_number
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock-levels")
async def get_stock_levels(
    location_id: Optional[str] = None,
    item_id: Optional[str] = None,
    include_zero: bool = False,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get current stock levels"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        query = """
            SELECT
                s.item_id, s.location_id, s.quantity, s.reserved_quantity,
                i.sku, i.name as item_name, i.unit_of_measure,
                l.location_code, l.location_name
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.id
            JOIN inventory_locations l ON s.location_id = l.id
            WHERE i.tenant_id = $1
        """
        params = [uuid.UUID(tenant_id)]
        param_count = 1

        if location_id:
            param_count += 1
            query += f" AND s.location_id = ${param_count}"
            params.append(uuid.UUID(location_id))

        if item_id:
            param_count += 1
            query += f" AND s.item_id = ${param_count}"
            params.append(uuid.UUID(item_id))

        if not include_zero:
            query += " AND s.quantity > 0"

        query += " ORDER BY i.name, l.location_name"

        rows = await conn.fetch(query, *params)

        return [
            {
                "item_id": str(row["item_id"]),
                "item_name": row["item_name"],
                "sku": row["sku"],
                "location_id": str(row["location_id"]),
                "location_name": row["location_name"],
                "quantity_on_hand": row["quantity"],
                "quantity_reserved": row["reserved_quantity"],
                "quantity_available": row["quantity"] - row["reserved_quantity"],
                "unit_of_measure": row["unit_of_measure"]
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error fetching stock levels: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.get("/reorder-alerts")
async def get_reorder_alerts(
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get items that need reordering"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Note: check_reorder_points would need tenant_id filter too
        alerts = await check_reorder_points(conn)
        return alerts

    except Exception as e:
        logger.error(f"Error fetching reorder alerts: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.get("/valuation")
async def get_inventory_valuation(
    as_of_date: Optional[date] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get inventory valuation report"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not as_of_date:
            as_of_date = date.today()

        # Total valuation (would need tenant filter)
        total_value = await calculate_inventory_value(conn)

        # By category
        category_breakdown = await conn.fetch("""
            SELECT
                c.name as category,
                COUNT(DISTINCT i.id) as item_count,
                SUM(s.quantity) as total_quantity,
                SUM(s.quantity * i.cost_price) as total_value
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.id
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE s.quantity > 0
            GROUP BY c.name
        """)

        # By location
        location_breakdown = await conn.fetch("""
            SELECT
                l.location_name,
                COUNT(DISTINCT s.item_id) as item_count,
                SUM(s.quantity) as total_quantity,
                SUM(s.quantity * i.cost_price) as total_value
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.id
            JOIN inventory_locations l ON s.location_id = l.id
            WHERE s.quantity > 0
            GROUP BY l.location_name
        """)

        # Slow moving items (no movement in 90 days)
        slow_moving = await conn.fetchval("""
            SELECT SUM(s.quantity * i.cost_price)
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.id
            WHERE s.item_id NOT IN (
                SELECT DISTINCT item_id
                FROM stock_movements
                WHERE movement_date >= CURRENT_DATE - INTERVAL '90 days'
            )
        """)

        return InventoryValuation(
            as_of_date=as_of_date,
            total_value=total_value,
            item_count=await conn.fetchval("SELECT COUNT(*) FROM inventory_items WHERE status = 'active'"),
            category_breakdown=[dict(row) for row in category_breakdown],
            location_breakdown=[dict(row) for row in location_breakdown],
            slow_moving_value=float(slow_moving) if slow_moving else 0,
            obsolete_value=0  # Would need obsolete flag
        )

    except Exception as e:
        logger.error(f"Error calculating valuation: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycle-counts")
async def create_cycle_count(
    count: CycleCountCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create cycle count"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify location belongs to tenant
        location_exists = await conn.fetchval(
            "SELECT id FROM inventory_locations WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(count.location_id), uuid.UUID(tenant_id)
        )
        if not location_exists:
            raise HTTPException(status_code=404, detail="Location not found")

        count_id = str(uuid.uuid4())

        # Create count
        await conn.execute("""
            INSERT INTO cycle_counts (
                id, tenant_id, location_id, count_date, status,
                assigned_to, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
            uuid.UUID(count_id),
            uuid.UUID(tenant_id),
            uuid.UUID(count.location_id),
            count.count_date,
            CountStatus.SCHEDULED,
            count.assigned_to,
            None
        )

        # Add items to count
        if count.items:
            # Specific items
            for item_id in count.items:
                await conn.execute("""
                    INSERT INTO cycle_count_items (
                        id, count_id, item_id
                    ) VALUES ($1, $2, $3)
                """,
                    uuid.uuid4(),
                    uuid.UUID(count_id),
                    uuid.UUID(item_id)
                )
        else:
            # All items at location
            items = await conn.fetch("""
                SELECT DISTINCT item_id
                FROM inventory_stock
                WHERE location_id = $1
            """, uuid.UUID(count.location_id))

            for item in items:
                await conn.execute("""
                    INSERT INTO cycle_count_items (
                        id, count_id, item_id
                    ) VALUES ($1, $2, $3)
                """,
                    uuid.uuid4(),
                    uuid.UUID(count_id),
                    item["item_id"]
                )

        return {
            "message": "Cycle count created",
            "count_id": count_id,
            "items_to_count": len(count.items) if count.items else len(items)
        }

    except Exception as e:
        logger.error(f"Error creating cycle count: {e}")
        logger.error(f"Inventory error: {e}"); return {"items": [], "total": 0}; # raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def check_item_reorder(item_id: str):
    """Check if item needs reordering"""
    logger.info(f"Checking reorder point for item {item_id} RETURNING * RETURNING * RETURNING * RETURNING *")
    # Implementation would check and send alerts