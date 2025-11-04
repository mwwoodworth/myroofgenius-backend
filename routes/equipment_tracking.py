"""
Equipment Tracking System
Task 41: Comprehensive equipment management and tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, UploadFile, File
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

logger = logging.getLogger(__name__)

router = APIRouter()

# Enums for equipment tracking
class EquipmentType(str, Enum):
    VEHICLE = "vehicle"
    HEAVY_MACHINERY = "heavy_machinery"
    POWER_TOOL = "power_tool"
    HAND_TOOL = "hand_tool"
    SAFETY_EQUIPMENT = "safety_equipment"
    COMPUTER = "computer"
    COMMUNICATION = "communication"
    MEASUREMENT = "measurement"
    OTHER = "other"

class EquipmentStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    RESERVED = "reserved"
    RETIRED = "retired"
    LOST = "lost"
    STOLEN = "stolen"

class ConditionRating(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"

class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"
    CALIBRATION = "calibration"
    CLEANING = "cleaning"
    EMERGENCY = "emergency"

class MaintenanceStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class CheckoutStatus(str, Enum):
    CHECKED_OUT = "checked_out"
    RETURNED = "returned"
    OVERDUE = "overdue"
    DAMAGED = "damaged"
    LOST = "lost"

class FuelType(str, Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PROPANE = "propane"
    NATURAL_GAS = "natural_gas"
    NA = "not_applicable"

# Pydantic models
class EquipmentCreate(BaseModel):
    equipment_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    equipment_type: EquipmentType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    location_id: Optional[str] = None
    assigned_to: Optional[str] = None
    fuel_type: Optional[FuelType] = FuelType.NA
    capacity: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EquipmentStatus] = None
    condition: Optional[ConditionRating] = None
    location_id: Optional[str] = None
    assigned_to: Optional[str] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None

class EquipmentResponse(BaseModel):
    id: str
    equipment_code: str
    name: str
    description: Optional[str]
    equipment_type: EquipmentType
    status: EquipmentStatus
    condition: ConditionRating
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    year: Optional[int]
    purchase_date: Optional[date]
    purchase_price: Optional[float]
    current_value: Optional[float]
    location_id: Optional[str]
    location_name: Optional[str]
    assigned_to: Optional[str]
    fuel_type: Optional[FuelType]
    last_maintenance_date: Optional[date]
    next_maintenance_date: Optional[date]
    total_maintenance_cost: Optional[float]
    utilization_rate: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MaintenanceSchedule(BaseModel):
    equipment_id: str
    maintenance_type: MaintenanceType
    scheduled_date: date
    frequency_days: Optional[int] = None
    description: str
    estimated_duration_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    assigned_technician: Optional[str] = None
    parts_required: Optional[List[str]] = None

class MaintenanceRecord(BaseModel):
    equipment_id: str
    maintenance_type: MaintenanceType
    performed_date: date
    performed_by: str
    duration_hours: float
    cost: float
    parts_used: Optional[List[Dict[str, Any]]] = None
    issues_found: Optional[str] = None
    actions_taken: str
    next_maintenance_date: Optional[date] = None
    notes: Optional[str] = None

class EquipmentCheckout(BaseModel):
    equipment_id: str
    checked_out_to: str
    job_id: Optional[str] = None
    expected_return_date: Optional[date] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None

class EquipmentReturn(BaseModel):
    checkout_id: str
    condition: ConditionRating
    meter_reading: Optional[float] = None
    fuel_level: Optional[float] = None
    damages: Optional[str] = None
    notes: Optional[str] = None

class UsageLog(BaseModel):
    equipment_id: str
    start_time: datetime
    end_time: datetime
    operator: str
    job_id: Optional[str] = None
    hours_used: float
    meter_start: Optional[float] = None
    meter_end: Optional[float] = None
    fuel_used: Optional[float] = None
    notes: Optional[str] = None

class InspectionReport(BaseModel):
    equipment_id: str
    inspection_date: date
    inspector: str
    inspection_type: str
    checklist_items: List[Dict[str, Any]]
    overall_condition: ConditionRating
    pass_fail: bool
    issues_found: Optional[List[str]] = None
    recommendations: Optional[str] = None
    next_inspection_date: Optional[date] = None
    photos: Optional[List[str]] = None

class EquipmentCost(BaseModel):
    equipment_id: str
    cost_type: str  # maintenance, repair, fuel, insurance, registration, other
    amount: float
    date: date
    description: str
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    job_id: Optional[str] = None

class GPSLocation(BaseModel):
    equipment_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None

# Helper functions
def generate_equipment_code() -> str:
    """Generate unique equipment code"""
    timestamp = datetime.now().strftime("%Y%m")
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"EQ-{timestamp}-{random_suffix}"

async def calculate_utilization_rate(conn, equipment_id: str, days: int = 30) -> float:
    """Calculate equipment utilization rate"""
    since_date = datetime.now() - timedelta(days=days)

    result = await conn.fetchrow("""
        SELECT
            SUM(EXTRACT(EPOCH FROM (return_time - checkout_time)) / 3600) as hours_used,
            $2 * 24 as total_hours
        FROM equipment_checkouts
        WHERE equipment_id = $1
            AND checkout_time >= $3
            AND return_time IS NOT NULL
    """, uuid.UUID(equipment_id), days, since_date)

    if result and result["hours_used"]:
        return round((result["hours_used"] / result["total_hours"]) * 100, 2)
    return 0

async def calculate_maintenance_costs(conn, equipment_id: str) -> float:
    """Calculate total maintenance costs"""
    result = await conn.fetchval("""
        SELECT COALESCE(SUM(cost), 0)
        FROM maintenance_records
        WHERE equipment_id = $1
    """, uuid.UUID(equipment_id))

    return float(result) if result else 0

async def get_next_maintenance(conn, equipment_id: str) -> Optional[date]:
    """Get next scheduled maintenance date"""
    result = await conn.fetchval("""
        SELECT MIN(scheduled_date)
        FROM maintenance_schedules
        WHERE equipment_id = $1
            AND status = 'scheduled'
            AND scheduled_date >= CURRENT_DATE
    """, uuid.UUID(equipment_id))

    return result

async def check_equipment_availability(conn, equipment_id: str, start_date: date, end_date: date) -> bool:
    """Check if equipment is available for a period"""
    conflicts = await conn.fetchval("""
        SELECT COUNT(*)
        FROM equipment_checkouts
        WHERE equipment_id = $1
            AND status = 'checked_out'
            AND (
                (checkout_time::date <= $2 AND COALESCE(expected_return_date, CURRENT_DATE + INTERVAL '1 year') >= $2)
                OR (checkout_time::date <= $3 AND COALESCE(expected_return_date, CURRENT_DATE + INTERVAL '1 year') >= $3)
                OR (checkout_time::date >= $2 AND checkout_time::date <= $3)
            )
    """, uuid.UUID(equipment_id), start_date, end_date)

    return conflicts == 0

# API Endpoints
@router.post("/equipment", response_model=EquipmentResponse)
async def create_equipment(
    equipment: EquipmentCreate,
    conn = Depends(get_db_connection)
):
    """Create new equipment"""
    try:
        # Check for duplicate code
        existing = await conn.fetchval(
            "SELECT id FROM equipment WHERE equipment_code = $1",
            equipment.equipment_code
        )
        if existing:
            raise HTTPException(status_code=400, detail="Equipment code already exists")

        equipment_id = str(uuid.uuid4())

        # Create equipment
        result = await conn.fetchrow("""
            INSERT INTO equipment (
                id, equipment_code, name, description, equipment_type,
                manufacturer, model, serial_number, year,
                purchase_date, purchase_price, current_value,
                location_id, assigned_to, fuel_type, capacity,
                specifications, status, condition
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING *
        """,
            uuid.UUID(equipment_id),
            equipment.equipment_code,
            equipment.name,
            equipment.description,
            equipment.equipment_type,
            equipment.manufacturer,
            equipment.model,
            equipment.serial_number,
            equipment.year,
            equipment.purchase_date,
            equipment.purchase_price,
            equipment.current_value or equipment.purchase_price,
            uuid.UUID(equipment.location_id) if equipment.location_id else None,
            equipment.assigned_to,
            equipment.fuel_type,
            equipment.capacity,
            json.dumps(equipment.specifications) if equipment.specifications else None,
            EquipmentStatus.AVAILABLE,
            ConditionRating.GOOD
        )

        # Get location name
        location_name = None
        if equipment.location_id:
            location = await conn.fetchrow(
                "SELECT location_name FROM inventory_locations WHERE id = $1",
                uuid.UUID(equipment.location_id)
            )
            if location:
                location_name = location["location_name"]

        response = EquipmentResponse(
            **dict(result),
            location_name=location_name,
            last_maintenance_date=None,
            next_maintenance_date=None,
            total_maintenance_cost=0,
            utilization_rate=0
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment", response_model=List[EquipmentResponse])
async def get_equipment(
    equipment_type: Optional[EquipmentType] = None,
    status: Optional[EquipmentStatus] = None,
    location_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    available_only: bool = False,
    search: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    conn = Depends(get_db_connection)
):
    """Get equipment with filters"""
    try:
        # Build query
        query = """
            SELECT e.*, l.location_name,
                   mr.last_maintenance_date,
                   ms.next_maintenance_date
            FROM equipment e
            LEFT JOIN inventory_locations l ON e.location_id = l.id
            LEFT JOIN (
                SELECT equipment_id, MAX(performed_date) as last_maintenance_date
                FROM maintenance_records
                GROUP BY equipment_id
            ) mr ON e.id = mr.equipment_id
            LEFT JOIN (
                SELECT equipment_id, MIN(scheduled_date) as next_maintenance_date
                FROM maintenance_schedules
                WHERE status = 'scheduled' AND scheduled_date >= CURRENT_DATE
                GROUP BY equipment_id
            ) ms ON e.id = ms.equipment_id
            WHERE 1=1
        """
        params = []
        param_count = 0

        if equipment_type:
            param_count += 1
            query += f" AND e.equipment_type = ${param_count}"
            params.append(equipment_type)

        if status:
            param_count += 1
            query += f" AND e.status = ${param_count}"
            params.append(status)

        if location_id:
            param_count += 1
            query += f" AND e.location_id = ${param_count}"
            params.append(uuid.UUID(location_id))

        if assigned_to:
            param_count += 1
            query += f" AND e.assigned_to = ${param_count}"
            params.append(assigned_to)

        if available_only:
            query += " AND e.status = 'available'"

        if search:
            param_count += 1
            query += f" AND (e.name ILIKE ${param_count} OR e.equipment_code ILIKE ${param_count} OR e.serial_number ILIKE ${param_count})"
            params.append(f"%{search}%")

        query += f" ORDER BY e.name LIMIT {limit} OFFSET {offset}"

        rows = await conn.fetch(query, *params)

        equipment_list = []
        for row in rows:
            # Calculate additional metrics
            utilization = await calculate_utilization_rate(conn, str(row["id"]))
            maintenance_cost = await calculate_maintenance_costs(conn, str(row["id"]))

            equipment_list.append(EquipmentResponse(
                **dict(row),
                total_maintenance_cost=maintenance_cost,
                utilization_rate=utilization
            ))

        return equipment_list

    except Exception as e:
        logger.error(f"Error fetching equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_details(
    equipment_id: str,
    conn = Depends(get_db_connection)
):
    """Get equipment details"""
    try:
        result = await conn.fetchrow("""
            SELECT e.*, l.location_name
            FROM equipment e
            LEFT JOIN inventory_locations l ON e.location_id = l.id
            WHERE e.id = $1
        """, uuid.UUID(equipment_id))

        if not result:
            raise HTTPException(status_code=404, detail="Equipment not found")

        # Get additional data
        last_maintenance = await conn.fetchval("""
            SELECT MAX(performed_date)
            FROM maintenance_records
            WHERE equipment_id = $1
        """, uuid.UUID(equipment_id))

        next_maintenance = await get_next_maintenance(conn, equipment_id)
        utilization = await calculate_utilization_rate(conn, equipment_id)
        maintenance_cost = await calculate_maintenance_costs(conn, equipment_id)

        return EquipmentResponse(
            **dict(result),
            last_maintenance_date=last_maintenance,
            next_maintenance_date=next_maintenance,
            total_maintenance_cost=maintenance_cost,
            utilization_rate=utilization
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    update: EquipmentUpdate,
    conn = Depends(get_db_connection)
):
    """Update equipment"""
    try:
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
        params.append(uuid.UUID(equipment_id))

        query = f"""
            UPDATE equipment
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """

        result = await conn.fetchrow(query, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Equipment not found")

        # Get additional data
        location_name = None
        if result["location_id"]:
            location = await conn.fetchrow(
                "SELECT location_name FROM inventory_locations WHERE id = $1",
                result["location_id"]
            )
            if location:
                location_name = location["location_name"]

        last_maintenance = await conn.fetchval("""
            SELECT MAX(performed_date)
            FROM maintenance_records
            WHERE equipment_id = $1
        """, uuid.UUID(equipment_id))

        next_maintenance = await get_next_maintenance(conn, equipment_id)
        utilization = await calculate_utilization_rate(conn, equipment_id)
        maintenance_cost = await calculate_maintenance_costs(conn, equipment_id)

        return EquipmentResponse(
            **dict(result),
            location_name=location_name,
            last_maintenance_date=last_maintenance,
            next_maintenance_date=next_maintenance,
            total_maintenance_cost=maintenance_cost,
            utilization_rate=utilization
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/equipment/{equipment_id}/checkout")
async def checkout_equipment(
    equipment_id: str,
    checkout: EquipmentCheckout,
    conn = Depends(get_db_connection)
):
    """Check out equipment"""
    try:
        # Verify equipment exists and is available
        equipment = await conn.fetchrow(
            "SELECT * FROM equipment WHERE id = $1",
            uuid.UUID(equipment_id)
        )

        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")

        if equipment["status"] != EquipmentStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=f"Equipment is {equipment['status']}")

        checkout_id = str(uuid.uuid4())

        # Create checkout record
        await conn.execute("""
            INSERT INTO equipment_checkouts (
                id, equipment_id, checked_out_to, checkout_time,
                expected_return_date, job_id, purpose, notes, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            uuid.UUID(checkout_id),
            uuid.UUID(equipment_id),
            checkout.checked_out_to,
            datetime.now(),
            checkout.expected_return_date,
            uuid.UUID(checkout.job_id) if checkout.job_id else None,
            checkout.purpose,
            checkout.notes,
            CheckoutStatus.CHECKED_OUT
        )

        # Update equipment status
        await conn.execute("""
            UPDATE equipment
            SET status = 'in_use',
                assigned_to = $2,
                updated_at = NOW()
            WHERE id = $1
        """, uuid.UUID(equipment_id), checkout.checked_out_to)

        # Log activity
        await conn.execute("""
            INSERT INTO equipment_activity_log (
                equipment_id, activity_type, performed_by,
                description, activity_date
            ) VALUES ($1, $2, $3, $4, $5)
        """,
            uuid.UUID(equipment_id),
            "checkout",
            checkout.checked_out_to,
            f"Equipment checked out to {checkout.checked_out_to}",
            datetime.now()
        )

        return {
            "message": "Equipment checked out successfully",
            "checkout_id": checkout_id,
            "equipment_id": equipment_id,
            "checked_out_to": checkout.checked_out_to,
            "expected_return": checkout.expected_return_date
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking out equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/equipment/return")
async def return_equipment(
    return_info: EquipmentReturn,
    conn = Depends(get_db_connection)
):
    """Return checked out equipment"""
    try:
        # Get checkout record
        checkout = await conn.fetchrow("""
            SELECT * FROM equipment_checkouts
            WHERE id = $1 AND status = 'checked_out'
        """, uuid.UUID(return_info.checkout_id))

        if not checkout:
            raise HTTPException(status_code=404, detail="Active checkout not found")

        # Update checkout record
        await conn.execute("""
            UPDATE equipment_checkouts
            SET return_time = $1,
                return_condition = $2,
                meter_reading_return = $3,
                fuel_level_return = $4,
                damages = $5,
                return_notes = $6,
                status = 'returned'
            WHERE id = $7
        """,
            datetime.now(),
            return_info.condition,
            return_info.meter_reading,
            return_info.fuel_level,
            return_info.damages,
            return_info.notes,
            uuid.UUID(return_info.checkout_id)
        )

        # Update equipment status
        new_status = EquipmentStatus.AVAILABLE
        if return_info.condition == ConditionRating.POOR or return_info.damages:
            new_status = EquipmentStatus.MAINTENANCE

        await conn.execute("""
            UPDATE equipment
            SET status = $1,
                condition = $2,
                assigned_to = NULL,
                updated_at = NOW()
            WHERE id = $3
        """, new_status, return_info.condition, checkout["equipment_id"])

        # Log activity
        await conn.execute("""
            INSERT INTO equipment_activity_log (
                equipment_id, activity_type, performed_by,
                description, activity_date
            ) VALUES ($1, $2, $3, $4, $5)
        """,
            checkout["equipment_id"],
            "return",
            checkout["checked_out_to"],
            f"Equipment returned in {return_info.condition} condition",
            datetime.now()
        )

        # Calculate usage hours
        hours_used = (datetime.now() - checkout["checkout_time"]).total_seconds() / 3600

        return {
            "message": "Equipment returned successfully",
            "checkout_id": return_info.checkout_id,
            "equipment_id": str(checkout["equipment_id"]),
            "hours_used": round(hours_used, 2),
            "condition": return_info.condition,
            "new_status": new_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error returning equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/equipment/{equipment_id}/maintenance")
async def schedule_maintenance(
    equipment_id: str,
    schedule: MaintenanceSchedule,
    background_tasks: BackgroundTasks,
    conn = Depends(get_db_connection)
):
    """Schedule equipment maintenance"""
    try:
        schedule_id = str(uuid.uuid4())

        # Create maintenance schedule
        await conn.execute("""
            INSERT INTO maintenance_schedules (
                id, equipment_id, maintenance_type, scheduled_date,
                frequency_days, description, estimated_duration_hours,
                estimated_cost, assigned_technician, parts_required,
                status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            uuid.UUID(schedule_id),
            uuid.UUID(equipment_id),
            schedule.maintenance_type,
            schedule.scheduled_date,
            schedule.frequency_days,
            schedule.description,
            schedule.estimated_duration_hours,
            schedule.estimated_cost,
            schedule.assigned_technician,
            json.dumps(schedule.parts_required) if schedule.parts_required else None,
            MaintenanceStatus.SCHEDULED
        )

        # Update equipment if maintenance is soon
        if schedule.scheduled_date <= date.today() + timedelta(days=7):
            await conn.execute("""
                UPDATE equipment
                SET status = CASE
                    WHEN $1 <= CURRENT_DATE THEN 'maintenance'
                    ELSE status
                END
                WHERE id = $2
            """, schedule.scheduled_date, uuid.UUID(equipment_id))

        # Schedule recurring maintenance if frequency is set
        if schedule.frequency_days:
            background_tasks.add_task(
                create_recurring_maintenance,
                equipment_id,
                schedule_id,
                schedule.frequency_days
            )

        return {
            "message": "Maintenance scheduled",
            "schedule_id": schedule_id,
            "scheduled_date": schedule.scheduled_date,
            "recurring": schedule.frequency_days is not None
        }

    except Exception as e:
        logger.error(f"Error scheduling maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/equipment/{equipment_id}/maintenance/record")
async def record_maintenance(
    equipment_id: str,
    record: MaintenanceRecord,
    conn = Depends(get_db_connection)
):
    """Record completed maintenance"""
    try:
        record_id = str(uuid.uuid4())

        # Create maintenance record
        await conn.execute("""
            INSERT INTO maintenance_records (
                id, equipment_id, maintenance_type, performed_date,
                performed_by, duration_hours, cost, parts_used,
                issues_found, actions_taken, next_maintenance_date,
                notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
            uuid.UUID(record_id),
            uuid.UUID(equipment_id),
            record.maintenance_type,
            record.performed_date,
            record.performed_by,
            record.duration_hours,
            record.cost,
            json.dumps(record.parts_used) if record.parts_used else None,
            record.issues_found,
            record.actions_taken,
            record.next_maintenance_date,
            record.notes
        )

        # Update equipment status
        await conn.execute("""
            UPDATE equipment
            SET status = 'available',
                last_maintenance_date = $1,
                updated_at = NOW()
            WHERE id = $2 AND status = 'maintenance'
        """, record.performed_date, uuid.UUID(equipment_id))

        # Mark scheduled maintenance as completed
        await conn.execute("""
            UPDATE maintenance_schedules
            SET status = 'completed',
                actual_date = $1,
                actual_cost = $2
            WHERE equipment_id = $3
                AND scheduled_date <= $1
                AND status = 'scheduled'
        """, record.performed_date, record.cost, uuid.UUID(equipment_id))

        # Log activity
        await conn.execute("""
            INSERT INTO equipment_activity_log (
                equipment_id, activity_type, performed_by,
                description, activity_date
            ) VALUES ($1, $2, $3, $4, $5)
        """,
            uuid.UUID(equipment_id),
            "maintenance",
            record.performed_by,
            f"{record.maintenance_type} maintenance completed",
            datetime.now()
        )

        return {
            "message": "Maintenance recorded",
            "record_id": record_id,
            "total_cost": record.cost,
            "next_maintenance": record.next_maintenance_date
        }

    except Exception as e:
        logger.error(f"Error recording maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/equipment/{equipment_id}/inspection")
async def record_inspection(
    equipment_id: str,
    inspection: InspectionReport,
    conn = Depends(get_db_connection)
):
    """Record equipment inspection"""
    try:
        inspection_id = str(uuid.uuid4())

        # Create inspection record
        await conn.execute("""
            INSERT INTO equipment_inspections (
                id, equipment_id, inspection_date, inspector,
                inspection_type, checklist_items, overall_condition,
                pass_fail, issues_found, recommendations,
                next_inspection_date, photos
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
            uuid.UUID(inspection_id),
            uuid.UUID(equipment_id),
            inspection.inspection_date,
            inspection.inspector,
            inspection.inspection_type,
            json.dumps(inspection.checklist_items),
            inspection.overall_condition,
            inspection.pass_fail,
            json.dumps(inspection.issues_found) if inspection.issues_found else None,
            inspection.recommendations,
            inspection.next_inspection_date,
            json.dumps(inspection.photos) if inspection.photos else None
        )

        # Update equipment condition
        await conn.execute("""
            UPDATE equipment
            SET condition = $1,
                last_inspection_date = $2,
                updated_at = NOW()
            WHERE id = $3
        """, inspection.overall_condition, inspection.inspection_date, uuid.UUID(equipment_id))

        # Create maintenance schedule if issues found
        if not inspection.pass_fail and inspection.issues_found:
            await conn.execute("""
                INSERT INTO maintenance_schedules (
                    id, equipment_id, maintenance_type, scheduled_date,
                    description, status
                ) VALUES ($1, $2, 'corrective', $3, $4, 'scheduled')
            """,
                uuid.uuid4(),
                uuid.UUID(equipment_id),
                date.today() + timedelta(days=7),
                f"Address inspection issues: {', '.join(inspection.issues_found[:3])}"
            )

        return {
            "message": "Inspection recorded",
            "inspection_id": inspection_id,
            "pass_fail": inspection.pass_fail,
            "condition": inspection.overall_condition,
            "next_inspection": inspection.next_inspection_date
        }

    except Exception as e:
        logger.error(f"Error recording inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/{equipment_id}/history")
async def get_equipment_history(
    equipment_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn = Depends(get_db_connection)
):
    """Get equipment usage and maintenance history"""
    try:
        # Build date filter
        date_filter = ""
        if start_date:
            date_filter += f" AND activity_date >= '{start_date}'"
        if end_date:
            date_filter += f" AND activity_date <= '{end_date}'"

        # Get activity log
        activities = await conn.fetch(f"""
            SELECT activity_type, performed_by, description,
                   activity_date, metadata
            FROM equipment_activity_log
            WHERE equipment_id = $1 {date_filter}
            ORDER BY activity_date DESC
        """, uuid.UUID(equipment_id))

        # Get maintenance records
        maintenance = await conn.fetch(f"""
            SELECT maintenance_type, performed_date, performed_by,
                   duration_hours, cost, actions_taken
            FROM maintenance_records
            WHERE equipment_id = $1
                AND performed_date >= COALESCE($2, '1900-01-01')
                AND performed_date <= COALESCE($3, '2100-12-31')
            ORDER BY performed_date DESC
        """, uuid.UUID(equipment_id), start_date, end_date)

        # Get checkout history
        checkouts = await conn.fetch(f"""
            SELECT checked_out_to, checkout_time, return_time,
                   job_id, purpose, return_condition
            FROM equipment_checkouts
            WHERE equipment_id = $1
                AND checkout_time >= COALESCE($2, '1900-01-01')::timestamptz
                AND checkout_time <= COALESCE($3, '2100-12-31')::timestamptz
            ORDER BY checkout_time DESC
        """, uuid.UUID(equipment_id), start_date, end_date)

        return {
            "equipment_id": equipment_id,
            "period": f"{start_date or 'All time'} to {end_date or 'Present'}",
            "activities": [dict(row) for row in activities],
            "maintenance": [dict(row) for row in maintenance],
            "checkouts": [dict(row) for row in checkouts],
            "total_maintenance_cost": sum(m["cost"] for m in maintenance),
            "total_checkouts": len(checkouts),
            "total_usage_hours": sum(
                ((c["return_time"] or datetime.now()) - c["checkout_time"]).total_seconds() / 3600
                for c in checkouts
            )
        }

    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/{equipment_id}/availability")
async def check_availability(
    equipment_id: str,
    start_date: date,
    end_date: date,
    conn = Depends(get_db_connection)
):
    """Check equipment availability for a period"""
    try:
        is_available = await check_equipment_availability(conn, equipment_id, start_date, end_date)

        # Get conflicting bookings if not available
        conflicts = []
        if not is_available:
            conflicts = await conn.fetch("""
                SELECT checkout_time, expected_return_date,
                       checked_out_to, job_id
                FROM equipment_checkouts
                WHERE equipment_id = $1
                    AND status = 'checked_out'
                    AND (
                        (checkout_time::date <= $2 AND COALESCE(expected_return_date, CURRENT_DATE + INTERVAL '1 year') >= $2)
                        OR (checkout_time::date <= $3 AND COALESCE(expected_return_date, CURRENT_DATE + INTERVAL '1 year') >= $3)
                        OR (checkout_time::date >= $2 AND checkout_time::date <= $3)
                    )
            """, uuid.UUID(equipment_id), start_date, end_date)

        # Get maintenance schedules
        maintenance = await conn.fetch("""
            SELECT scheduled_date, maintenance_type, description
            FROM maintenance_schedules
            WHERE equipment_id = $1
                AND status = 'scheduled'
                AND scheduled_date BETWEEN $2 AND $3
        """, uuid.UUID(equipment_id), start_date, end_date)

        return {
            "equipment_id": equipment_id,
            "period": f"{start_date} to {end_date}",
            "is_available": is_available,
            "conflicts": [dict(row) for row in conflicts],
            "scheduled_maintenance": [dict(row) for row in maintenance]
        }

    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/reports/utilization")
async def get_utilization_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    equipment_type: Optional[EquipmentType] = None,
    conn = Depends(get_db_connection)
):
    """Get equipment utilization report"""
    try:
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # Build query
        type_filter = ""
        if equipment_type:
            type_filter = f"AND e.equipment_type = '{equipment_type}'"

        report = await conn.fetch(f"""
            SELECT
                e.id, e.equipment_code, e.name, e.equipment_type,
                COUNT(ec.id) as checkout_count,
                SUM(EXTRACT(EPOCH FROM (
                    COALESCE(ec.return_time, NOW()) - ec.checkout_time
                )) / 3600) as total_hours,
                AVG(EXTRACT(EPOCH FROM (
                    COALESCE(ec.return_time, NOW()) - ec.checkout_time
                )) / 3600) as avg_hours_per_use,
                MAX(ec.checkout_time) as last_used
            FROM equipment e
            LEFT JOIN equipment_checkouts ec ON e.id = ec.equipment_id
                AND ec.checkout_time >= $1
                AND ec.checkout_time <= $2
            WHERE 1=1 {type_filter}
            GROUP BY e.id, e.equipment_code, e.name, e.equipment_type
            ORDER BY total_hours DESC NULLS LAST
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()))

        total_days = (end_date - start_date).days + 1
        total_hours = total_days * 24

        return {
            "period": f"{start_date} to {end_date}",
            "equipment_count": len(report),
            "data": [
                {
                    **dict(row),
                    "utilization_rate": round((row["total_hours"] / total_hours * 100) if row["total_hours"] else 0, 2)
                }
                for row in report
            ],
            "summary": {
                "total_checkouts": sum(r["checkout_count"] for r in report),
                "total_usage_hours": sum(r["total_hours"] or 0 for r in report),
                "avg_utilization": round(
                    sum(r["total_hours"] or 0 for r in report) / (len(report) * total_hours) * 100
                    if report else 0, 2
                )
            }
        }

    except Exception as e:
        logger.error(f"Error generating utilization report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/reports/maintenance-costs")
async def get_maintenance_cost_report(
    year: Optional[int] = None,
    equipment_type: Optional[EquipmentType] = None,
    conn = Depends(get_db_connection)
):
    """Get maintenance cost report"""
    try:
        if not year:
            year = datetime.now().year

        # Build filters
        type_filter = ""
        if equipment_type:
            type_filter = f"AND e.equipment_type = '{equipment_type}'"

        report = await conn.fetch(f"""
            SELECT
                e.equipment_code, e.name, e.equipment_type,
                e.purchase_price, e.current_value,
                COUNT(mr.id) as maintenance_count,
                SUM(mr.cost) as total_maintenance_cost,
                AVG(mr.cost) as avg_maintenance_cost,
                SUM(mr.cost) / NULLIF(e.purchase_price, 0) * 100 as maintenance_to_purchase_ratio
            FROM equipment e
            LEFT JOIN maintenance_records mr ON e.id = mr.equipment_id
                AND EXTRACT(YEAR FROM mr.performed_date) = $1
            WHERE 1=1 {type_filter}
            GROUP BY e.id, e.equipment_code, e.name, e.equipment_type,
                     e.purchase_price, e.current_value
            ORDER BY total_maintenance_cost DESC NULLS LAST
        """, year)

        return {
            "year": year,
            "equipment_count": len(report),
            "data": [dict(row) for row in report],
            "summary": {
                "total_maintenance_cost": sum(r["total_maintenance_cost"] or 0 for r in report),
                "total_maintenance_events": sum(r["maintenance_count"] for r in report),
                "avg_cost_per_equipment": round(
                    sum(r["total_maintenance_cost"] or 0 for r in report) / len(report)
                    if report else 0, 2
                )
            }
        }

    except Exception as e:
        logger.error(f"Error generating maintenance cost report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def create_recurring_maintenance(equipment_id: str, template_id: str, frequency_days: int):
    """Create recurring maintenance schedules"""
    logger.info(f"Creating recurring maintenance for equipment {equipment_id} every {frequency_days} days RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *")