"""
Relationships System API Routes
Manages entity relationships and awareness
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/relationships", tags=["Relationships"])

@router.get("/status")
async def get_relationship_status(request: Request):
    """Get relationship system status"""
    try:
        db_pool = request.app.state.db_pool

        # Get statistics from database
        async with db_pool.acquire() as conn:
            # Count relationships by type
            customer_count = await conn.fetchval("SELECT COUNT(*) FROM customers")
            job_count = await conn.fetchval("SELECT COUNT(*) FROM jobs")
            invoice_count = await conn.fetchval("SELECT COUNT(*) FROM invoices")

            # Count active relationships
            jobs_with_customers = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs
                WHERE customer_id IS NOT NULL
            """)

            invoices_with_customers = await conn.fetchval("""
                SELECT COUNT(*) FROM invoices
                WHERE customer_id IS NOT NULL
            """)

        return {
            "status": "operational",
            "relationship_aware": True,
            "entities": {
                "customers": customer_count,
                "jobs": job_count,
                "invoices": invoice_count
            },
            "relationships": {
                "jobs_linked_to_customers": jobs_with_customers,
                "invoices_linked_to_customers": invoices_with_customers
            },
            "capabilities": [
                "auto_linking",
                "relationship_discovery",
                "entity_validation",
                "cross_reference_detection",
                "duplicate_prevention"
            ]
        }

    except Exception as e:
        logger.error(f"Error getting relationship status: {e}")
        return {
            "status": "error",
            "relationship_aware": False,
            "error": str(e)
        }

@router.get("/analyze/{entity_type}/{entity_id}")
async def analyze_relationships(
    entity_type: str,
    entity_id: str,
    request: Request
):
    """Analyze relationships for a specific entity"""
    try:
        db_pool = request.app.state.db_pool

        relationships = {}

        async with db_pool.acquire() as conn:
            if entity_type == "customer":
                # Get related jobs
                jobs = await conn.fetch("""
                    SELECT id, title, status
                    FROM jobs
                    WHERE customer_id = $1::uuid
                """, entity_id)
                relationships["jobs"] = [dict(j) for j in jobs]

                # Get related invoices
                invoices = await conn.fetch("""
                    SELECT id, invoice_number, status, total_amount
                    FROM invoices
                    WHERE customer_id = $1::uuid
                """, entity_id)
                relationships["invoices"] = [dict(i) for i in invoices]

            elif entity_type == "job":
                # Get customer
                customer = await conn.fetchrow("""
                    SELECT c.id, c.name, c.email
                    FROM customers c
                    JOIN jobs j ON j.customer_id = c.id
                    WHERE j.id = $1::uuid
                """, entity_id)
                if customer:
                    relationships["customer"] = dict(customer)

                # Get related invoices
                invoices = await conn.fetch("""
                    SELECT id, invoice_number, status, total_amount
                    FROM invoices
                    WHERE job_id = $1::uuid
                """, entity_id)
                relationships["invoices"] = [dict(i) for i in invoices]

        return {
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "relationships": relationships
        }

    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}")
        return {
            "success": False,
            "error": str(e)
        }