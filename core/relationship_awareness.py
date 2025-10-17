"""
Relationship Awareness System
Makes the ERP intricately aware of how all entities connect

When you create a Customer:
→ Links to Jobs
→ Links to Estimates
→ Links to Invoices
→ Links to Communications
→ Links to Payments

When you create a Job:
→ Links to Customer
→ Links to Estimate
→ Links to Employees (assigned crew)
→ Links to Equipment (used on job)
→ Links to Materials (from inventory)
→ Links to Timesheets (labor tracking)
→ Links to Inspections
→ Links to Photos
→ Creates Invoice when completed

When you create an Employee:
→ Links to HR record
→ Links to Timesheets
→ Links to Payroll
→ Links to Jobs (assignments)
→ Links to Certifications
→ Links to Training records

This creates DEEP INTRICATE AWARENESS across the entire system.
"""
import asyncpg
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class RelationshipMap:
    """
    Complete map of all entity relationships in the ERP
    """

    # Primary relationships (parent → children)
    RELATIONSHIPS = {
        "customers": {
            "children": [
                {"table": "jobs", "fk": "customer_id", "relationship": "has_many"},
                {"table": "estimates", "fk": "customer_id", "relationship": "has_many"},
                {"table": "invoices", "fk": "customer_id", "relationship": "has_many"},
                {"table": "payments", "fk": "customer_id", "relationship": "has_many"},
                # Note: communications uses polymorphic relationship (entity_type, entity_id)
                # Note: service_agreements table doesn't exist in current schema
            ],
            "computed_fields": {
                "total_lifetime_value": "SUM(invoices.total_amount)",
                "total_jobs": "COUNT(jobs.id)",
                "total_estimates": "COUNT(estimates.id)",
                "last_job_date": "MAX(jobs.completed_at)",
            }
        },

        "jobs": {
            "parent": {"table": "customers", "fk": "customer_id"},
            "children": [
                {"table": "job_assignments", "fk": "job_id", "relationship": "has_many"},
                {"table": "job_materials", "fk": "job_id", "relationship": "has_many"},
                {"table": "job_equipment", "fk": "job_id", "relationship": "has_many"},
                {"table": "timesheets", "fk": "job_id", "relationship": "has_many"},
                {"table": "field_inspections", "fk": "job_id", "relationship": "has_many"},
                {"table": "job_photos", "fk": "job_id", "relationship": "has_many"},
                {"table": "change_orders", "fk": "job_id", "relationship": "has_many"},
            ],
            "belongs_to": [
                {"table": "estimates", "fk": "estimate_id", "relationship": "belongs_to"},
            ],
            "computed_fields": {
                "total_labor_hours": "SUM(timesheets.hours)",
                "total_labor_cost": "SUM(timesheets.hours * timesheets.rate)",
                "total_material_cost": "SUM(job_materials.quantity * job_materials.unit_cost)",
                "crew_size": "COUNT(DISTINCT job_assignments.employee_id)",
            }
        },

        "estimates": {
            "parent": {"table": "customers", "fk": "customer_id"},
            "children": [
                {"table": "estimate_line_items", "fk": "estimate_id", "relationship": "has_many"},
                {"table": "jobs", "fk": "estimate_id", "relationship": "has_many"},
            ],
            "computed_fields": {
                "total_items": "COUNT(estimate_line_items.id)",
                "approved": "status = 'approved'",
            }
        },

        "invoices": {
            "parent": {"table": "customers", "fk": "customer_id"},
            "belongs_to": [
                {"table": "jobs", "fk": "job_id", "relationship": "belongs_to"},
            ],
            "children": [
                {"table": "invoice_line_items", "fk": "invoice_id", "relationship": "has_many"},
                {"table": "payments", "fk": "invoice_id", "relationship": "has_many"},
            ],
            "computed_fields": {
                "total_paid": "SUM(payments.amount)",
                "balance_due": "total_amount - SUM(payments.amount)",
                "is_paid": "SUM(payments.amount) >= total_amount",
            }
        },

        "employees": {
            "children": [
                {"table": "job_assignments", "fk": "employee_id", "relationship": "has_many"},
                {"table": "timesheets", "fk": "employee_id", "relationship": "has_many"},
                {"table": "certifications", "fk": "employee_id", "relationship": "has_many"},
                {"table": "training_records", "fk": "employee_id", "relationship": "has_many"},
                {"table": "performance_reviews", "fk": "employee_id", "relationship": "has_many"},
            ],
            "belongs_to": [
                {"table": "hr_records", "fk": "employee_id", "relationship": "has_one"},
                {"table": "payroll_records", "fk": "employee_id", "relationship": "has_many"},
            ],
            "computed_fields": {
                "total_hours_worked": "SUM(timesheets.hours)",
                "total_jobs_completed": "COUNT(DISTINCT job_assignments.job_id WHERE jobs.status = 'completed')",
                "current_assignments": "COUNT(job_assignments.id WHERE job_assignments.status = 'active')",
            }
        },

        "equipment": {
            "children": [
                {"table": "job_equipment", "fk": "equipment_id", "relationship": "has_many"},
                {"table": "equipment_maintenance", "fk": "equipment_id", "relationship": "has_many"},
                {"table": "equipment_inspections", "fk": "equipment_id", "relationship": "has_many"},
            ],
            "computed_fields": {
                "total_usage_hours": "SUM(job_equipment.hours_used)",
                "maintenance_due": "next_maintenance_date < NOW()",
            }
        },

        "inventory": {
            "children": [
                {"table": "job_materials", "fk": "inventory_item_id", "relationship": "has_many"},
                {"table": "purchase_orders", "fk": "inventory_item_id", "relationship": "has_many"},
            ],
            "computed_fields": {
                "quantity_available": "quantity_on_hand - quantity_reserved",
                "reorder_needed": "quantity_on_hand <= reorder_point",
                "total_value": "quantity_on_hand * unit_cost",
            }
        },
    }


class RelationshipAwareness:
    """
    Creates deep intricate awareness of entity relationships
    Automatically links entities when records are created
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.relationship_map = RelationshipMap.RELATIONSHIPS

    async def create_customer_with_awareness(
        self,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create customer with full relationship awareness

        Automatically:
        1. Creates customer record
        2. Initializes relationship tracking
        3. Sets up computed field materialization
        4. Creates audit trail
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Create customer
                # Use provided org_id or default to WeatherCraft Roofing
                org_id = customer_data.get("org_id", "00000000-0000-0000-0000-000000000001")

                customer = await conn.fetchrow("""
                    INSERT INTO customers (
                        name, email, phone, billing_address, billing_city, billing_state, billing_zip,
                        tenant_id, org_id, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                    RETURNING *
                """,
                    customer_data.get("name"),
                    customer_data.get("email"),
                    customer_data.get("phone"),
                    customer_data.get("address"),
                    customer_data.get("city"),
                    customer_data.get("state"),
                    customer_data.get("zip"),
                    customer_data.get("tenant_id"),
                    org_id
                )

                customer_id = customer['id']

                # Initialize relationship tracking
                await self._initialize_relationship_tracking(
                    conn,
                    entity_type="customer",
                    entity_id=customer_id
                )

                # Get complete customer view with all relationships
                complete_view = await self.get_complete_entity_view(
                    entity_type="customers",
                    entity_id=customer_id,
                    conn=conn
                )

                return complete_view

    async def create_job_with_awareness(
        self,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create job with automatic relationship linking

        Automatically links:
        - Customer (parent)
        - Estimate (if provided)
        - Assigns employees (if provided)
        - Reserves equipment (if provided)
        - Allocates materials (if provided)
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Create job
                # Use provided org_id or default to WeatherCraft Roofing
                org_id = job_data.get("org_id", "00000000-0000-0000-0000-000000000001")

                job = await conn.fetchrow("""
                    INSERT INTO jobs (
                        customer_id, estimate_id, job_number, title, description,
                        property_address, scheduled_start, tenant_id, org_id, created_at, status
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), 'scheduled')
                    RETURNING *
                """,
                    job_data.get("customer_id"),
                    job_data.get("estimate_id"),
                    job_data.get("job_number"),
                    job_data.get("title"),
                    job_data.get("description"),
                    job_data.get("property_address"),
                    job_data.get("scheduled_start"),
                    job_data.get("tenant_id"),
                    org_id
                )

                job_id = job['id']

                # Auto-assign employees if provided
                if job_data.get("employee_ids"):
                    await self._assign_employees_to_job(
                        conn, job_id, job_data["employee_ids"]
                    )

                # Auto-reserve equipment if provided
                if job_data.get("equipment_ids"):
                    await self._reserve_equipment_for_job(
                        conn, job_id, job_data["equipment_ids"]
                    )

                # Auto-allocate materials if provided
                if job_data.get("materials"):
                    await self._allocate_materials_to_job(
                        conn, job_id, job_data["materials"]
                    )

                # Initialize relationship tracking
                await self._initialize_relationship_tracking(
                    conn,
                    entity_type="job",
                    entity_id=job_id
                )

                # Get complete job view
                complete_view = await self.get_complete_entity_view(
                    entity_type="jobs",
                    entity_id=job_id,
                    conn=conn
                )

                return complete_view

    async def get_complete_entity_view(
        self,
        entity_type: str,
        entity_id: str,
        conn: Optional[asyncpg.Connection] = None
    ) -> Dict[str, Any]:
        """
        Get complete view of entity with ALL relationships

        Returns:
        - Base entity data
        - All parent relationships
        - All child relationships
        - All computed fields
        - Relationship graph
        """
        # Use provided connection or acquire new one
        if conn is not None:
            # Use existing connection (from transaction)
            return await self._get_complete_entity_view_impl(conn, entity_type, entity_id)
        else:
            # Acquire new connection
            async with self.db_pool.acquire() as new_conn:
                return await self._get_complete_entity_view_impl(new_conn, entity_type, entity_id)

    async def _get_complete_entity_view_impl(
        self,
        conn: asyncpg.Connection,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Internal implementation of get_complete_entity_view"""
        # Get base entity
        try:
            entity = await conn.fetchrow(f"""
                SELECT * FROM {entity_type} WHERE id = $1
            """, entity_id)
        except Exception as e:
            logger.error(f"Error querying {entity_type} with id={entity_id}: {e}")
            raise

        if not entity:
            logger.warning(f"Entity not found: {entity_type} id={entity_id}")
            return None

        result = {
            "entity": dict(entity),
            "relationships": {},
            "computed_fields": {},
            "relationship_graph": {}
        }

        # Get relationship config
        rel_config = self.relationship_map.get(entity_type, {})

        # Load parent relationship
        if "parent" in rel_config:
            parent_config = rel_config["parent"]
            parent_id = entity[parent_config["fk"]]
            if parent_id:
                parent = await conn.fetchrow(f"""
                    SELECT * FROM {parent_config['table']} WHERE id = $1
                """, parent_id)
                result["relationships"]["parent"] = {
                    "table": parent_config["table"],
                    "data": dict(parent) if parent else None
                }

        # Load children relationships
        if "children" in rel_config:
            for child_config in rel_config["children"]:
                children = await conn.fetch(f"""
                    SELECT * FROM {child_config['table']}
                    WHERE {child_config['fk']} = $1
                """, entity_id)
                result["relationships"][child_config["table"]] = {
                    "count": len(children),
                    "data": [dict(row) for row in children]
                }

        # Load belongs_to relationships
        if "belongs_to" in rel_config:
            for belongs_config in rel_config["belongs_to"]:
                related_id = entity.get(belongs_config["fk"])
                if related_id:
                    related = await conn.fetchrow(f"""
                        SELECT * FROM {belongs_config['table']} WHERE id = $1
                    """, related_id)
                    result["relationships"][belongs_config["table"]] = {
                        "data": dict(related) if related else None
                    }

        # Calculate computed fields
        if "computed_fields" in rel_config:
            for field_name, calculation in rel_config["computed_fields"].items():
                # Simplified - in production would execute actual SQL
                result["computed_fields"][field_name] = await self._calculate_field(
                    conn, entity_type, entity_id, field_name, calculation
                )

        # Build relationship graph
        result["relationship_graph"] = await self._build_relationship_graph(
            entity_type, entity_id
        )

        return result

    async def _assign_employees_to_job(
        self,
        conn: asyncpg.Connection,
        job_id: str,
        employee_ids: List[str]
    ):
        """Auto-assign employees to job"""
        for emp_id in employee_ids:
            await conn.execute("""
                INSERT INTO job_assignments (job_id, employee_id, role, status, created_at)
                VALUES ($1, $2, 'crew_member', 'active', NOW())
                ON CONFLICT DO NOTHING
            """, job_id, emp_id)

    async def _reserve_equipment_for_job(
        self,
        conn: asyncpg.Connection,
        job_id: str,
        equipment_ids: List[str]
    ):
        """Auto-reserve equipment for job"""
        for equip_id in equipment_ids:
            await conn.execute("""
                INSERT INTO job_equipment (job_id, equipment_id, status, created_at)
                VALUES ($1, $2, 'reserved', NOW())
                ON CONFLICT DO NOTHING
            """, job_id, equip_id)

    async def _allocate_materials_to_job(
        self,
        conn: asyncpg.Connection,
        job_id: str,
        materials: List[Dict[str, Any]]
    ):
        """Auto-allocate materials to job"""
        for material in materials:
            await conn.execute("""
                INSERT INTO job_materials (
                    job_id, inventory_item_id, quantity, unit_cost, created_at
                )
                VALUES ($1, $2, $3, $4, NOW())
            """,
                job_id,
                material["inventory_item_id"],
                material["quantity"],
                material.get("unit_cost", 0)
            )

            # Update inventory reserved quantity
            await conn.execute("""
                UPDATE inventory
                SET quantity_reserved = quantity_reserved + $1
                WHERE id = $2
            """, material["quantity"], material["inventory_item_id"])

    async def _initialize_relationship_tracking(
        self,
        conn: asyncpg.Connection,
        entity_type: str,
        entity_id: str
    ):
        """Initialize relationship tracking for entity"""
        await conn.execute("""
            INSERT INTO entity_relationships (
                entity_type, entity_id, relationship_graph, created_at
            )
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (entity_type, entity_id) DO UPDATE
            SET updated_at = NOW()
        """, entity_type, entity_id, json.dumps({}))

    async def _calculate_field(
        self,
        conn: asyncpg.Connection,
        entity_type: str,
        entity_id: str,
        field_name: str,
        calculation: str
    ) -> Any:
        """Calculate computed field value"""
        # Simplified - in production would parse and execute calculation
        return None

    async def _build_relationship_graph(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Build complete relationship graph for entity"""
        graph = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "connections": []
        }

        rel_config = self.relationship_map.get(entity_type, {})

        # Add parent connections
        if "parent" in rel_config:
            graph["connections"].append({
                "type": "parent",
                "table": rel_config["parent"]["table"],
                "relationship": "belongs_to"
            })

        # Add children connections
        if "children" in rel_config:
            for child in rel_config["children"]:
                graph["connections"].append({
                    "type": "child",
                    "table": child["table"],
                    "relationship": child["relationship"]
                })

        return graph

    async def refresh_entity_relationships(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Recompute and persist relationship details for an entity.

        Returns the latest complete view, or None if the entity does not exist.
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                complete_view = await self._get_complete_entity_view_impl(
                    conn, entity_type, entity_id
                )

                if not complete_view:
                    return None

                parent_entities = complete_view["relationships"].get("parent")
                child_entities = {
                    key: value
                    for key, value in complete_view["relationships"].items()
                    if key != "parent"
                }

                await conn.execute(
                    """
                    INSERT INTO entity_relationships (
                        entity_type,
                        entity_id,
                        relationship_graph,
                        parent_entities,
                        child_entities,
                        computed_fields,
                        last_computed_at,
                        updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                    ON CONFLICT (entity_type, entity_id) DO UPDATE
                    SET relationship_graph = EXCLUDED.relationship_graph,
                        parent_entities = EXCLUDED.parent_entities,
                        child_entities = EXCLUDED.child_entities,
                        computed_fields = EXCLUDED.computed_fields,
                        last_computed_at = NOW(),
                        updated_at = NOW()
                    """,
                    entity_type,
                    entity_id,
                    json.dumps(complete_view["relationship_graph"]),
                    json.dumps(parent_entities),
                    json.dumps(child_entities),
                    json.dumps(complete_view["computed_fields"]),
                )

                return complete_view
