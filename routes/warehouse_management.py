"""
Warehouse Management System
Task 42: Comprehensive warehouse operations and management
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

# Enums for warehouse management
class WarehouseType(str, Enum):
    MAIN = "main"
    DISTRIBUTION = "distribution"
    COLD_STORAGE = "cold_storage"
    HAZMAT = "hazmat"
    CROSS_DOCK = "cross_dock"
    FULFILLMENT = "fulfillment"
    RETURNS = "returns"

class ZoneType(str, Enum):
    RECEIVING = "receiving"
    STORAGE = "storage"
    PICKING = "picking"
    PACKING = "packing"
    SHIPPING = "shipping"
    RETURNS = "returns"
    QUARANTINE = "quarantine"
    STAGING = "staging"

class StorageType(str, Enum):
    RACK = "rack"
    SHELF = "shelf"
    BIN = "bin"
    PALLET = "pallet"
    FLOOR = "floor"
    MEZZANINE = "mezzanine"
    OUTDOOR = "outdoor"

class ReceivingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    UNLOADING = "unloading"
    CHECKING = "checking"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ShippingStatus(str, Enum):
    PENDING = "pending"
    PICKING = "picking"
    PACKING = "packing"
    READY = "ready"
    LOADED = "loaded"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PickingMethod(str, Enum):
    SINGLE = "single"
    BATCH = "batch"
    WAVE = "wave"
    ZONE = "zone"
    CLUSTER = "cluster"

class PickStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PutawayStrategy(str, Enum):
    FIXED = "fixed"
    RANDOM = "random"
    ABC = "abc"
    FIFO = "fifo"
    LIFO = "lifo"
    CLOSEST = "closest"
    ZONE_BASED = "zone_based"

# Pydantic models
class WarehouseCreate(BaseModel):
    warehouse_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    warehouse_type: WarehouseType
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None
    capacity_sqft: Optional[int] = None
    operating_hours: Optional[Dict[str, str]] = None
    features: Optional[List[str]] = None

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    manager: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

class WarehouseResponse(BaseModel):
    id: str
    warehouse_code: str
    name: str
    warehouse_type: WarehouseType
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    manager: Optional[str]
    capacity_sqft: Optional[int]
    used_sqft: Optional[int]
    utilization_percent: Optional[float]
    total_locations: int
    occupied_locations: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ZoneCreate(BaseModel):
    warehouse_id: str
    zone_code: str = Field(..., min_length=1, max_length=50)
    zone_name: str
    zone_type: ZoneType
    area_sqft: Optional[int] = None
    temperature_range: Optional[Dict[str, float]] = None
    humidity_range: Optional[Dict[str, float]] = None
    security_level: Optional[int] = Field(None, ge=1, le=5)

class LocationCreate(BaseModel):
    warehouse_id: str
    zone_id: Optional[str] = None
    location_code: str = Field(..., min_length=1, max_length=50)
    aisle: Optional[str] = None
    rack: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None
    storage_type: StorageType
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None
    is_available: bool = True

class LocationResponse(BaseModel):
    id: str
    warehouse_id: str
    zone_id: Optional[str]
    location_code: str
    full_path: str
    storage_type: StorageType
    is_occupied: bool
    current_item_id: Optional[str]
    current_quantity: Optional[int]
    max_weight: Optional[float]
    max_volume: Optional[float]
    last_activity_date: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ReceivingOrder(BaseModel):
    warehouse_id: str
    supplier_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    expected_date: date
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    items: List[Dict[str, Any]]  # [{item_id, expected_quantity, unit}]
    notes: Optional[str] = None

class ReceivingUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[ReceivingStatus] = None
    received_by: Optional[str] = None
    items_received: Optional[List[Dict[str, Any]]] = None  # [{item_id, received_quantity, condition}]
    discrepancies: Optional[List[str]] = None
    notes: Optional[str] = None

class PutawayTask(BaseModel):
    receiving_id: str
    item_id: str
    quantity: int
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    strategy: PutawayStrategy = PutawayStrategy.RANDOM
    assigned_to: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)

class PickingOrder(BaseModel):
    warehouse_id: str
    order_id: str
    customer_id: Optional[str] = None
    method: PickingMethod = PickingMethod.SINGLE
    priority: int = Field(5, ge=1, le=10)
    items: List[Dict[str, Any]]  # [{item_id, quantity, location_id}]
    required_date: Optional[date] = None
    assigned_to: Optional[str] = None

class PickingUpdate(BaseModel):
    status: PickStatus
    picked_items: Optional[List[Dict[str, Any]]] = None  # [{item_id, picked_quantity, location}]
    picker: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exceptions: Optional[List[str]] = None

class ShippingOrder(BaseModel):
    warehouse_id: str
    order_id: str
    customer_id: Optional[str] = None
    ship_to_address: str
    carrier: str
    service_type: str
    items: List[Dict[str, Any]]  # [{item_id, quantity}]
    ship_date: date
    tracking_number: Optional[str] = None

class TransferOrder(BaseModel):
    from_warehouse_id: str
    to_warehouse_id: str
    items: List[Dict[str, Any]]  # [{item_id, quantity}]
    transfer_date: date
    reason: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)

class CycleCountRequest(BaseModel):
    warehouse_id: str
    zone_id: Optional[str] = None
    locations: Optional[List[str]] = None
    count_date: date
    assigned_to: Optional[str] = None

class InventoryAdjustment(BaseModel):
    warehouse_id: str
    location_id: str
    item_id: str
    current_quantity: int
    new_quantity: int
    reason: str
    approved_by: Optional[str] = None

class WarehouseMetrics(BaseModel):
    warehouse_id: str
    period: str
    receiving_volume: int
    shipping_volume: int
    inventory_turnover: float
    order_accuracy: float
    picking_efficiency: float
    space_utilization: float
    labor_productivity: float
    cost_per_order: float
    on_time_delivery: float

# Helper functions
def generate_location_code(aisle: str, rack: str, shelf: str, bin: str) -> str:
    """Generate location code from components"""
    return f"{aisle}-{rack}-{shelf}-{bin}"

async def find_optimal_location(conn, warehouse_id: str, item_id: str, quantity: int, strategy: PutawayStrategy) -> Optional[str]:
    """Find optimal storage location based on strategy"""

    if strategy == PutawayStrategy.RANDOM:
        # Find any available location
        result = await conn.fetchrow("""
            SELECT id FROM warehouse_locations
            WHERE warehouse_id = $1
                AND is_available = true
                AND is_occupied = false
            ORDER BY RANDOM()
            LIMIT 1
        """, uuid.UUID(warehouse_id))

    elif strategy == PutawayStrategy.ABC:
        # Place based on item velocity (ABC classification)
        result = await conn.fetchrow("""
            SELECT wl.id
            FROM warehouse_locations wl
            JOIN warehouse_zones wz ON wl.zone_id = wz.id
            WHERE wl.warehouse_id = $1
                AND wl.is_available = true
                AND wl.is_occupied = false
                AND wz.zone_type = 'picking'
            ORDER BY wl.distance_from_shipping ASC
            LIMIT 1
        """, uuid.UUID(warehouse_id))

    elif strategy == PutawayStrategy.CLOSEST:
        # Find closest available location to receiving
        result = await conn.fetchrow("""
            SELECT wl.id
            FROM warehouse_locations wl
            JOIN warehouse_zones wz ON wl.zone_id = wz.id
            WHERE wl.warehouse_id = $1
                AND wl.is_available = true
                AND wl.is_occupied = false
            ORDER BY wz.zone_type = 'receiving' DESC, wl.location_code
            LIMIT 1
        """, uuid.UUID(warehouse_id))
    else:
        result = None

    return str(result["id"]) if result else None

async def calculate_warehouse_utilization(conn, warehouse_id: str) -> Dict[str, Any]:
    """Calculate warehouse space utilization"""

    # Get total and occupied locations
    location_stats = await conn.fetchrow("""
        SELECT
            COUNT(*) as total_locations,
            COUNT(CASE WHEN is_occupied THEN 1 END) as occupied_locations
        FROM warehouse_locations
        WHERE warehouse_id = $1
    """, uuid.UUID(warehouse_id))

    # Get capacity info
    warehouse = await conn.fetchrow("""
        SELECT capacity_sqft,
               (SELECT SUM(area_sqft) FROM warehouse_zones WHERE warehouse_id = $1) as used_sqft
        FROM warehouses
        WHERE id = $1
    """, uuid.UUID(warehouse_id))

    utilization = 0
    if location_stats["total_locations"] > 0:
        utilization = (location_stats["occupied_locations"] / location_stats["total_locations"]) * 100

    return {
        "total_locations": location_stats["total_locations"],
        "occupied_locations": location_stats["occupied_locations"],
        "location_utilization": round(utilization, 2),
        "capacity_sqft": warehouse["capacity_sqft"],
        "used_sqft": warehouse["used_sqft"],
        "space_utilization": round((warehouse["used_sqft"] / warehouse["capacity_sqft"] * 100) if warehouse["capacity_sqft"] else 0, 2)
    }

async def calculate_picking_efficiency(conn, warehouse_id: str, days: int = 30) -> float:
    """Calculate picking efficiency metrics"""
    since_date = datetime.now() - timedelta(days=days)

    result = await conn.fetchrow("""
        SELECT
            COUNT(*) as total_picks,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60) as avg_pick_time,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_picks
        FROM picking_tasks
        WHERE warehouse_id = $1
            AND created_at >= $2
    """, uuid.UUID(warehouse_id), since_date)

    if result["total_picks"] > 0:
        return round((result["completed_picks"] / result["total_picks"]) * 100, 2)
    return 0

# API Endpoints
@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse: WarehouseCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create new warehouse"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Check for duplicate code within tenant
        existing = await conn.fetchval(
            "SELECT id FROM warehouses WHERE warehouse_code = $1 AND tenant_id = $2",
            warehouse.warehouse_code,
            uuid.UUID(tenant_id)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Warehouse code already exists")

        warehouse_id = str(uuid.uuid4())

        # Create warehouse
        result = await conn.fetchrow("""
            INSERT INTO warehouses (
                id, tenant_id, warehouse_code, name, warehouse_type,
                address, city, state, zip_code, country,
                phone, email, manager, capacity_sqft,
                operating_hours, features, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, true)
            RETURNING *
        """,
            uuid.UUID(warehouse_id),
            uuid.UUID(tenant_id),
            warehouse.warehouse_code,
            warehouse.name,
            warehouse.warehouse_type,
            warehouse.address,
            warehouse.city,
            warehouse.state,
            warehouse.zip_code,
            warehouse.country,
            warehouse.phone,
            warehouse.email,
            warehouse.manager,
            warehouse.capacity_sqft,
            json.dumps(warehouse.operating_hours) if warehouse.operating_hours else None,
            warehouse.features
        )

        # Calculate initial metrics
        utilization = await calculate_warehouse_utilization(conn, warehouse_id)

        response = WarehouseResponse(
            **dict(result),
            used_sqft=0,
            utilization_percent=0,
            total_locations=0,
            occupied_locations=0
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating warehouse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses", response_model=List[WarehouseResponse])
async def get_warehouses(
    warehouse_type: Optional[WarehouseType] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get warehouses with filters"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Build query
        query = """
            SELECT w.*,
                   COUNT(DISTINCT wl.id) as total_locations,
                   COUNT(DISTINCT CASE WHEN wl.is_occupied THEN wl.id END) as occupied_locations
            FROM warehouses w
            LEFT JOIN warehouse_locations wl ON w.id = wl.warehouse_id
            WHERE w.tenant_id = $1
        """
        params = [uuid.UUID(tenant_id)]
        param_count = 1

        if warehouse_type:
            param_count += 1
            query += f" AND w.warehouse_type = ${param_count}"
            params.append(warehouse_type)

        if is_active is not None:
            param_count += 1
            query += f" AND w.is_active = ${param_count}"
            params.append(is_active)

        query += " GROUP BY w.id"
        # Use parameterized queries for LIMIT/OFFSET to prevent SQL injection
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        query += f" ORDER BY w.name LIMIT ${limit_param} OFFSET ${offset_param}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        warehouses = []
        for row in rows:
            utilization = 0
            if row["total_locations"] > 0:
                utilization = (row["occupied_locations"] / row["total_locations"]) * 100

            warehouses.append(WarehouseResponse(
                **dict(row),
                used_sqft=0,  # Would need calculation
                utilization_percent=round(utilization, 2)
            ))

        return warehouses

    except Exception as e:
        logger.error(f"Error fetching warehouses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse_details(
    warehouse_id: str,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get warehouse details"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        result = await conn.fetchrow("""
            SELECT * FROM warehouses WHERE id = $1 AND tenant_id = $2
        """, uuid.UUID(warehouse_id), uuid.UUID(tenant_id))

        if not result:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        # Get utilization metrics
        utilization = await calculate_warehouse_utilization(conn, warehouse_id)

        return WarehouseResponse(
            **dict(result),
            used_sqft=utilization["used_sqft"],
            utilization_percent=utilization["space_utilization"],
            total_locations=utilization["total_locations"],
            occupied_locations=utilization["occupied_locations"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching warehouse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/zones")
async def create_warehouse_zone(
    warehouse_id: str,
    zone: ZoneCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create warehouse zone"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        zone_id = str(uuid.uuid4())

        await conn.execute("""
            INSERT INTO warehouse_zones (
                id, tenant_id, warehouse_id, zone_code, zone_name, zone_type,
                area_sqft, temperature_range, humidity_range, security_level
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            uuid.UUID(zone_id),
            uuid.UUID(tenant_id),
            uuid.UUID(warehouse_id),
            zone.zone_code,
            zone.zone_name,
            zone.zone_type,
            zone.area_sqft,
            json.dumps(zone.temperature_range) if zone.temperature_range else None,
            json.dumps(zone.humidity_range) if zone.humidity_range else None,
            zone.security_level
        )

        return {"message": "Zone created", "zone_id": zone_id}

    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses/{warehouse_id}/locations")
async def create_location(
    warehouse_id: str,
    location: LocationCreate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create warehouse location"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        location_id = str(uuid.uuid4())

        # Generate full path
        full_path = generate_location_code(
            location.aisle or "",
            location.rack or "",
            location.shelf or "",
            location.bin or ""
        )

        await conn.execute("""
            INSERT INTO warehouse_locations (
                id, tenant_id, warehouse_id, zone_id, location_code, full_path,
                aisle, rack, shelf, bin, storage_type,
                max_weight, max_volume, is_available, is_occupied
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, false)
        """,
            uuid.UUID(location_id),
            uuid.UUID(tenant_id),
            uuid.UUID(warehouse_id),
            uuid.UUID(location.zone_id) if location.zone_id else None,
            location.location_code,
            full_path,
            location.aisle,
            location.rack,
            location.shelf,
            location.bin,
            location.storage_type,
            location.max_weight,
            location.max_volume,
            location.is_available
        )

        return {"message": "Location created", "location_id": location_id, "full_path": full_path}

    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}/locations", response_model=List[LocationResponse])
async def get_warehouse_locations(
    warehouse_id: str,
    zone_id: Optional[str] = None,
    is_occupied: Optional[bool] = None,
    storage_type: Optional[StorageType] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get warehouse locations"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        query = """
            SELECT * FROM warehouse_locations
            WHERE warehouse_id = $1 AND tenant_id = $2
        """
        params = [uuid.UUID(warehouse_id), uuid.UUID(tenant_id)]
        param_count = 2

        if zone_id:
            param_count += 1
            query += f" AND zone_id = ${param_count}"
            params.append(uuid.UUID(zone_id))

        if is_occupied is not None:
            param_count += 1
            query += f" AND is_occupied = ${param_count}"
            params.append(is_occupied)

        if storage_type:
            param_count += 1
            query += f" AND storage_type = ${param_count}"
            params.append(storage_type)

        # Use parameterized queries for LIMIT/OFFSET to prevent SQL injection
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        query += f" ORDER BY location_code LIMIT ${limit_param} OFFSET ${offset_param}"
        params.extend([limit, offset])

        rows = await conn.fetch(query, *params)

        return [LocationResponse(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/receiving/orders")
async def create_receiving_order(
    order: ReceivingOrder,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create receiving order"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(order.warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        receiving_id = str(uuid.uuid4())
        receiving_number = f"RCV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create receiving order
        await conn.execute("""
            INSERT INTO receiving_orders (
                id, tenant_id, receiving_number, warehouse_id, supplier_id,
                purchase_order_id, expected_date, carrier,
                tracking_number, status, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            uuid.UUID(receiving_id),
            uuid.UUID(tenant_id),
            receiving_number,
            uuid.UUID(order.warehouse_id),
            uuid.UUID(order.supplier_id) if order.supplier_id else None,
            uuid.UUID(order.purchase_order_id) if order.purchase_order_id else None,
            order.expected_date,
            order.carrier,
            order.tracking_number,
            ReceivingStatus.SCHEDULED,
            order.notes
        )

        # Add items
        for item in order.items:
            await conn.execute("""
                INSERT INTO receiving_order_items (
                    id, receiving_order_id, item_id,
                    expected_quantity, unit
                ) VALUES ($1, $2, $3, $4, $5)
            """,
                uuid.uuid4(),
                uuid.UUID(receiving_id),
                uuid.UUID(item["item_id"]),
                item["expected_quantity"],
                item.get("unit", "EACH")
            )

        return {
            "message": "Receiving order created",
            "receiving_id": receiving_id,
            "receiving_number": receiving_number
        }

    except Exception as e:
        logger.error(f"Error creating receiving order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/receiving/orders/{receiving_id}")
async def update_receiving_order(
    receiving_id: str,
    update: ReceivingUpdate,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update receiving order (process receipt)"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify receiving order belongs to tenant
        order_exists = await conn.fetchval(
            "SELECT id FROM receiving_orders WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(receiving_id), uuid.UUID(tenant_id)
        )
        if not order_exists:
            raise HTTPException(status_code=404, detail="Receiving order not found")

        # Update order
        if update.status:
            await conn.execute("""
                UPDATE receiving_orders
                SET status = $1,
                    actual_date = $2,
                    received_by = $3,
                    updated_at = NOW()
                WHERE id = $4
            """,
                update.status,
                update.actual_date or date.today(),
                update.received_by,
                uuid.UUID(receiving_id)
            )

        # Process received items
        if update.items_received:
            for item in update.items_received:
                # Update receiving items
                await conn.execute("""
                    UPDATE receiving_order_items
                    SET received_quantity = $1,
                        condition = $2,
                        discrepancy = $3
                    WHERE receiving_order_id = $4 AND item_id = $5
                """,
                    item["received_quantity"],
                    item.get("condition", "good"),
                    item["received_quantity"] != item.get("expected_quantity"),
                    uuid.UUID(receiving_id),
                    uuid.UUID(item["item_id"])
                )

                # Create putaway task if received
                if update.status == ReceivingStatus.COMPLETED:
                    background_tasks.add_task(
                        create_putaway_task,
                        receiving_id,
                        item["item_id"],
                        item["received_quantity"]
                    )

        # Log discrepancies
        if update.discrepancies:
            for discrepancy in update.discrepancies:
                await conn.execute("""
                    INSERT INTO warehouse_discrepancies (
                        warehouse_id, reference_type, reference_id,
                        description, reported_by
                    )
                    SELECT warehouse_id, 'receiving', $1, $2, $3
                    FROM receiving_orders WHERE id = $1
                """,
                    uuid.UUID(receiving_id),
                    discrepancy,
                    update.received_by
                )

        return {"message": "Receiving order updated", "status": update.status}

    except Exception as e:
        logger.error(f"Error updating receiving order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/putaway/tasks")
async def create_putaway_task_endpoint(
    task: PutawayTask,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create putaway task"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        task_id = str(uuid.uuid4())

        # Find optimal location if not specified
        if not task.to_location:
            # Get warehouse from receiving order (verify tenant)
            warehouse = await conn.fetchval("""
                SELECT warehouse_id FROM receiving_orders WHERE id = $1 AND tenant_id = $2
            """, uuid.UUID(task.receiving_id), uuid.UUID(tenant_id))

            if warehouse:
                task.to_location = await find_optimal_location(
                    conn, str(warehouse), task.item_id, task.quantity, task.strategy
                )

        if not task.to_location:
            raise HTTPException(status_code=400, detail="No available location found")

        # Create putaway task
        await conn.execute("""
            INSERT INTO putaway_tasks (
                id, receiving_id, item_id, quantity,
                from_location, to_location, strategy,
                assigned_to, priority, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'pending')
        """,
            uuid.UUID(task_id),
            uuid.UUID(task.receiving_id),
            uuid.UUID(task.item_id),
            task.quantity,
            task.from_location,
            task.to_location,
            task.strategy,
            task.assigned_to,
            task.priority
        )

        return {"message": "Putaway task created", "task_id": task_id, "location": task.to_location}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating putaway task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/picking/orders")
async def create_picking_order(
    order: PickingOrder,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create picking order"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(order.warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        picking_id = str(uuid.uuid4())
        picking_number = f"PCK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create picking order
        await conn.execute("""
            INSERT INTO picking_orders (
                id, tenant_id, picking_number, warehouse_id, order_id,
                customer_id, method, priority, required_date,
                assigned_to, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            uuid.UUID(picking_id),
            uuid.UUID(tenant_id),
            picking_number,
            uuid.UUID(order.warehouse_id),
            order.order_id,
            uuid.UUID(order.customer_id) if order.customer_id else None,
            order.method,
            order.priority,
            order.required_date,
            order.assigned_to,
            PickStatus.PENDING
        )

        # Add items to pick
        for item in order.items:
            await conn.execute("""
                INSERT INTO picking_order_items (
                    id, picking_order_id, item_id, quantity,
                    location_id, status
                ) VALUES ($1, $2, $3, $4, $5, 'pending')
            """,
                uuid.uuid4(),
                uuid.UUID(picking_id),
                uuid.UUID(item["item_id"]),
                item["quantity"],
                uuid.UUID(item.get("location_id")) if item.get("location_id") else None
            )

        return {
            "message": "Picking order created",
            "picking_id": picking_id,
            "picking_number": picking_number
        }

    except Exception as e:
        logger.error(f"Error creating picking order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/picking/orders/{picking_id}")
async def update_picking_order(
    picking_id: str,
    update: PickingUpdate,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Update picking order status"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify picking order belongs to tenant
        order_exists = await conn.fetchval(
            "SELECT id FROM picking_orders WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(picking_id), uuid.UUID(tenant_id)
        )
        if not order_exists:
            raise HTTPException(status_code=404, detail="Picking order not found")

        # Update order status
        await conn.execute("""
            UPDATE picking_orders
            SET status = $1,
                picker = COALESCE($2, picker),
                started_at = COALESCE($3, started_at),
                completed_at = $4,
                updated_at = NOW()
            WHERE id = $5
        """,
            update.status,
            update.picker,
            update.start_time,
            update.end_time,
            uuid.UUID(picking_id)
        )

        # Update picked items
        if update.picked_items:
            for item in update.picked_items:
                await conn.execute("""
                    UPDATE picking_order_items
                    SET picked_quantity = $1,
                        picked_from_location = $2,
                        status = 'completed'
                    WHERE picking_order_id = $3 AND item_id = $4
                """,
                    item["picked_quantity"],
                    item.get("location"),
                    uuid.UUID(picking_id),
                    uuid.UUID(item["item_id"])
                )

                # Update location inventory
                if item.get("location"):
                    await conn.execute("""
                        UPDATE warehouse_locations
                        SET current_quantity = GREATEST(0, current_quantity - $1),
                            is_occupied = (current_quantity - $1) > 0
                        WHERE id = $2
                    """,
                        item["picked_quantity"],
                        uuid.UUID(item["location"])
                    )

        # Log exceptions
        if update.exceptions:
            for exception in update.exceptions:
                await conn.execute("""
                    INSERT INTO picking_exceptions (
                        picking_order_id, description, reported_by
                    ) VALUES ($1, $2, $3)
                """,
                    uuid.UUID(picking_id),
                    exception,
                    update.picker
                )

        return {"message": "Picking order updated", "status": update.status}

    except Exception as e:
        logger.error(f"Error updating picking order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/shipping/orders")
async def create_shipping_order(
    order: ShippingOrder,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create shipping order"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(order.warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        shipping_id = str(uuid.uuid4())
        shipping_number = f"SHP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create shipping order
        await conn.execute("""
            INSERT INTO shipping_orders (
                id, tenant_id, shipping_number, warehouse_id, order_id,
                customer_id, ship_to_address, carrier,
                service_type, ship_date, tracking_number, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
            uuid.UUID(shipping_id),
            uuid.UUID(tenant_id),
            shipping_number,
            uuid.UUID(order.warehouse_id),
            order.order_id,
            uuid.UUID(order.customer_id) if order.customer_id else None,
            order.ship_to_address,
            order.carrier,
            order.service_type,
            order.ship_date,
            order.tracking_number,
            ShippingStatus.PENDING
        )

        # Add items
        for item in order.items:
            await conn.execute("""
                INSERT INTO shipping_order_items (
                    id, shipping_order_id, item_id, quantity
                ) VALUES ($1, $2, $3, $4)
            """,
                uuid.uuid4(),
                uuid.UUID(shipping_id),
                uuid.UUID(item["item_id"]),
                item["quantity"]
            )

        return {
            "message": "Shipping order created",
            "shipping_id": shipping_id,
            "shipping_number": shipping_number,
            "tracking_number": order.tracking_number
        }

    except Exception as e:
        logger.error(f"Error creating shipping order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfers")
async def create_transfer_order(
    transfer: TransferOrder,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create warehouse transfer order"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify both warehouses belong to tenant
        from_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(transfer.from_warehouse_id), uuid.UUID(tenant_id)
        )
        to_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(transfer.to_warehouse_id), uuid.UUID(tenant_id)
        )
        if not from_exists or not to_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        transfer_id = str(uuid.uuid4())
        transfer_number = f"TRF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create transfer order
        await conn.execute("""
            INSERT INTO warehouse_transfers (
                id, tenant_id, transfer_number, from_warehouse_id,
                to_warehouse_id, transfer_date, reason,
                priority, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
        """,
            uuid.UUID(transfer_id),
            uuid.UUID(tenant_id),
            transfer_number,
            uuid.UUID(transfer.from_warehouse_id),
            uuid.UUID(transfer.to_warehouse_id),
            transfer.transfer_date,
            transfer.reason,
            transfer.priority
        )

        # Add items
        for item in transfer.items:
            await conn.execute("""
                INSERT INTO warehouse_transfer_items (
                    id, transfer_id, item_id, quantity
                ) VALUES ($1, $2, $3, $4)
            """,
                uuid.uuid4(),
                uuid.UUID(transfer_id),
                uuid.UUID(item["item_id"]),
                item["quantity"]
            )

        return {
            "message": "Transfer order created",
            "transfer_id": transfer_id,
            "transfer_number": transfer_number
        }

    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses/{warehouse_id}/metrics")
async def get_warehouse_metrics(
    warehouse_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get warehouse performance metrics"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # Get receiving volume
        receiving = await conn.fetchrow("""
            SELECT COUNT(*) as orders, SUM(roi.received_quantity) as items
            FROM receiving_orders ro
            JOIN receiving_order_items roi ON ro.id = roi.receiving_order_id
            WHERE ro.warehouse_id = $1
                AND ro.actual_date BETWEEN $2 AND $3
        """, uuid.UUID(warehouse_id), start_date, end_date)

        # Get shipping volume
        shipping = await conn.fetchrow("""
            SELECT COUNT(*) as orders, SUM(soi.quantity) as items
            FROM shipping_orders so
            JOIN shipping_order_items soi ON so.id = soi.shipping_order_id
            WHERE so.warehouse_id = $1
                AND so.ship_date BETWEEN $2 AND $3
        """, uuid.UUID(warehouse_id), start_date, end_date)

        # Get picking efficiency
        picking_efficiency = await calculate_picking_efficiency(conn, warehouse_id, (end_date - start_date).days)

        # Get utilization
        utilization = await calculate_warehouse_utilization(conn, warehouse_id)

        # Get order accuracy
        accuracy = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_orders,
                COUNT(CASE WHEN no_errors THEN 1 END) as accurate_orders
            FROM picking_orders
            WHERE warehouse_id = $1
                AND completed_at BETWEEN $2 AND $3
        """, uuid.UUID(warehouse_id), datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()))

        order_accuracy = 100
        if accuracy["total_orders"] > 0:
            order_accuracy = (accuracy["accurate_orders"] / accuracy["total_orders"]) * 100

        return WarehouseMetrics(
            warehouse_id=warehouse_id,
            period=f"{start_date} to {end_date}",
            receiving_volume=receiving["items"] or 0,
            shipping_volume=shipping["items"] or 0,
            inventory_turnover=0,  # Would need calculation
            order_accuracy=round(order_accuracy, 2),
            picking_efficiency=picking_efficiency,
            space_utilization=utilization["space_utilization"],
            labor_productivity=0,  # Would need labor data
            cost_per_order=0,  # Would need cost data
            on_time_delivery=0  # Would need delivery data
        )

    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/adjustments")
async def create_inventory_adjustment(
    adjustment: InventoryAdjustment,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create inventory adjustment"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Verify warehouse belongs to tenant
        warehouse_exists = await conn.fetchval(
            "SELECT id FROM warehouses WHERE id = $1 AND tenant_id = $2",
            uuid.UUID(adjustment.warehouse_id), uuid.UUID(tenant_id)
        )
        if not warehouse_exists:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        adjustment_id = str(uuid.uuid4())
        variance = adjustment.new_quantity - adjustment.current_quantity

        # Create adjustment record
        await conn.execute("""
            INSERT INTO inventory_adjustments (
                id, tenant_id, warehouse_id, location_id, item_id,
                previous_quantity, new_quantity, variance,
                reason, approved_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            uuid.UUID(adjustment_id),
            uuid.UUID(tenant_id),
            uuid.UUID(adjustment.warehouse_id),
            uuid.UUID(adjustment.location_id),
            uuid.UUID(adjustment.item_id),
            adjustment.current_quantity,
            adjustment.new_quantity,
            variance,
            adjustment.reason,
            adjustment.approved_by
        )

        # Update location inventory
        await conn.execute("""
            UPDATE warehouse_locations
            SET current_quantity = $1,
                current_item_id = $2,
                is_occupied = $1 > 0,
                last_activity_date = NOW()
            WHERE id = $3
        """,
            adjustment.new_quantity,
            uuid.UUID(adjustment.item_id) if adjustment.new_quantity > 0 else None,
            uuid.UUID(adjustment.location_id)
        )

        return {
            "message": "Inventory adjusted",
            "adjustment_id": adjustment_id,
            "variance": variance
        }

    except Exception as e:
        logger.error(f"Error creating adjustment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def create_putaway_task(receiving_id: str, item_id: str, quantity: int):
    """Create putaway task after receiving"""
    logger.info(f"Creating putaway task for {quantity} units of item {item_id} RETURNING * RETURNING * RETURNING * RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *")