"""
Estimates API
Full CRUD for Estimates with Tenant Isolation
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import date, datetime
from uuid import UUID, uuid4

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/estimates", tags=["Estimates"])

def _parse_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc


def _parse_date(value: Any, field: str) -> date:
    if value is None or value == "":
        return date.today()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc


def _coerce_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except Exception:
        return 0.0


def _compute_amounts_from_line_items(items: Any) -> tuple[float, float, float]:
    """Return (subtotal, tax, total) from loosely-typed estimate items."""
    if not items:
        return 0.0, 0.0, 0.0
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return 0.0, 0.0, 0.0

    subtotal = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("total") is not None:
            subtotal += _coerce_float(item.get("total"))
        else:
            quantity = _coerce_float(item.get("quantity") or 1)
            unit_price = _coerce_float(item.get("unit_price") or item.get("price") or 0)
            subtotal += quantity * unit_price

    tax = 0.0
    total = subtotal + tax
    return subtotal, tax, total

@router.get("")
@router.get("/")
async def list_estimates(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List estimates for the authenticated tenant."""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT e.id, e.estimate_number, e.customer_id, e.job_id, e.title, e.status,
                   e.total_amount, e.subtotal, e.tax_amount, e.valid_until as expires_at, e.created_at,
                   c.name as customer_name,
                   j.title as job_title
            FROM estimates e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN jobs j ON e.job_id = j.id
            WHERE e.tenant_id = $1
        """
        params = [tenant_id]
        param_idx = 1

        if status:
            param_idx += 1
            query += f" AND e.status = ${param_idx}"
            params.append(status)

        if customer_id:
            param_idx += 1
            query += f" AND e.customer_id = ${param_idx}"
            params.append(customer_id)

        if job_id:
            param_idx += 1
            query += f" AND e.job_id = ${param_idx}"
            params.append(job_id)

        query += f" ORDER BY e.created_at DESC LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            # Count query
            count_query = "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1"
            count_params = [tenant_id]
            cp = 1
            
            if status:
                cp += 1
                count_query += f" AND status = ${cp}"
                count_params.append(status)
            if customer_id:
                cp += 1
                count_query += f" AND customer_id = ${cp}"
                count_params.append(customer_id)
            if job_id:
                cp += 1
                count_query += f" AND job_id = ${cp}"
                count_params.append(job_id)
                
            total = await conn.fetchval(count_query, *count_params)

        estimates = []
        for row in rows:
            record = dict(row)
            record["id"] = str(record.get("id"))
            # Convert decimals
            for f in ["total_amount", "subtotal", "tax_amount"]:
                if record.get(f) is not None:
                    record[f] = float(record[f])
            estimates.append(record)

        return {
            "success": True,
            "data": {
                "total": total or 0,
                "estimates": estimates,
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"Error listing estimates: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to list estimates")


@router.post("")
@router.post("/")  # Handle both with and without trailing slash
async def create_estimate(
    request: Request,
    estimate: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create an estimate for the authenticated tenant."""
    try:
        tenant_id_raw = current_user.get("tenant_id")
        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        customer_id_raw = estimate.get("customer_id")
        if not customer_id_raw:
            raise HTTPException(status_code=400, detail="customer_id is required")
        customer_id = _parse_uuid(customer_id_raw, "customer_id")

        estimate_number = (estimate.get("estimate_number") or f"EST-{uuid4().hex[:6].upper()}-{uuid4().hex[:6].upper()}").strip()
        title = (estimate.get("title") or estimate.get("name") or "Estimate").strip() or "Estimate"
        description = estimate.get("description") or None
        status = (estimate.get("status") or "draft").strip() or "draft"

        line_items = estimate.get("line_items") or estimate.get("items") or []
        if isinstance(line_items, str):
            try:
                line_items = json.loads(line_items)
            except Exception:
                line_items = []

        if not isinstance(line_items, (list, dict)):
            raise HTTPException(status_code=400, detail="line_items must be an array/object")

        subtotal_amount = estimate.get("subtotal_amount") or estimate.get("subtotal") or None
        tax_amount = estimate.get("tax_amount") or estimate.get("tax") or 0
        total_amount = estimate.get("total_amount") or estimate.get("total") or None

        if subtotal_amount is None or total_amount is None:
            computed_subtotal, computed_tax, computed_total = _compute_amounts_from_line_items(line_items)
            subtotal_amount = computed_subtotal if subtotal_amount is None else _coerce_float(subtotal_amount)
            total_amount = computed_total if total_amount is None else _coerce_float(total_amount)
            tax_amount = _coerce_float(tax_amount) if tax_amount is not None else computed_tax

        subtotal_amount_f = _coerce_float(subtotal_amount)
        tax_amount_f = _coerce_float(tax_amount)
        total_amount_f = _coerce_float(total_amount)

        estimate_date = _parse_date(estimate.get("estimate_date"), "estimate_date")
        valid_until = estimate.get("valid_until") or estimate.get("expires_at") or None

        estimate_id = uuid4()

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                org_id = await conn.fetchval(
                    "SELECT org_id FROM estimates WHERE tenant_id = $1 LIMIT 1",
                    tenant_id,
                )
                if not org_id:
                    org_id = await conn.fetchval(
                        "SELECT org_id FROM customers WHERE tenant_id = $1 LIMIT 1",
                        tenant_id,
                    )
                if not org_id:
                    org_id = UUID("00000000-0000-0000-0000-000000000001")

                row = await conn.fetchrow(
                    """
                    INSERT INTO estimates (
                        id,
                        tenant_id,
                        org_id,
                        estimate_number,
                        customer_id,
                        estimate_date,
                        valid_until,
                        status,
                        title,
                        description,
                        line_items,
                        subtotal,
                        tax_amount,
                        total,
                        subtotal_amount,
                        total_amount,
                        subtotal_cents,
                        tax_cents,
                        total_cents,
                        created_at,
                        updated_at
                    ) VALUES (
                        $1, $2, $3,
                        $4, $5,
                        $6::date,
                        $7::date,
                        $8, $9, $10,
                        $11::jsonb,
                        $12, $13, $14,
                        $12, $14,
                        $15, $16, $17,
                        NOW(), NOW()
                    )
                    RETURNING id::text AS id
                    """,
                    estimate_id,
                    tenant_id,
                    org_id,
                    estimate_number,
                    customer_id,
                    estimate_date,
                    valid_until,
                    status,
                    title,
                    description,
                    json.dumps(line_items),
                    subtotal_amount_f,
                    tax_amount_f,
                    total_amount_f,
                    int(round(subtotal_amount_f * 100)),
                    int(round(tax_amount_f * 100)),
                    int(round(total_amount_f * 100)),
                )

        return {"success": True, "data": {"id": row["id"] if row else str(estimate_id)}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating estimate: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create estimate")


@router.put("/{estimate_id}")
async def update_estimate(
    estimate_id: str,
    request: Request,
    estimate: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update an estimate for the authenticated tenant."""
    try:
        tenant_id_raw = current_user.get("tenant_id")
        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        estimate_uuid = _parse_uuid(estimate_id, "estimate_id")

        update_fields: Dict[str, Any] = {}

        if "title" in estimate or "name" in estimate:
            update_fields["title"] = (estimate.get("title") or estimate.get("name") or "").strip() or None
        if "description" in estimate:
            update_fields["description"] = estimate.get("description")
        if "status" in estimate:
            update_fields["status"] = (estimate.get("status") or "").strip() or None
        if "valid_until" in estimate or "expires_at" in estimate:
            update_fields["valid_until"] = estimate.get("valid_until") or estimate.get("expires_at")

        if "line_items" in estimate or "items" in estimate:
            line_items = estimate.get("line_items") or estimate.get("items") or []
            if isinstance(line_items, str):
                try:
                    line_items = json.loads(line_items)
                except Exception:
                    line_items = []
            if not isinstance(line_items, (list, dict)):
                raise HTTPException(status_code=400, detail="line_items must be an array/object")

            subtotal, tax, total = _compute_amounts_from_line_items(line_items)
            update_fields.update(
                {
                    "line_items": json.dumps(line_items),
                    "subtotal": subtotal,
                    "tax_amount": tax,
                    "total": total,
                    "subtotal_amount": subtotal,
                    "total_amount": total,
                    "subtotal_cents": int(round(subtotal * 100)),
                    "tax_cents": int(round(tax * 100)),
                    "total_cents": int(round(total * 100)),
                }
            )

        # Allow explicit overrides for amounts
        if "subtotal" in estimate or "subtotal_amount" in estimate:
            subtotal_amount = estimate.get("subtotal_amount") or estimate.get("subtotal")
            update_fields["subtotal"] = _coerce_float(subtotal_amount)
            update_fields["subtotal_amount"] = update_fields["subtotal"]
            update_fields["subtotal_cents"] = int(round(update_fields["subtotal"] * 100))
        if "tax_amount" in estimate:
            update_fields["tax_amount"] = _coerce_float(estimate.get("tax_amount"))
            update_fields["tax_cents"] = int(round(update_fields["tax_amount"] * 100))
        if "total" in estimate or "total_amount" in estimate:
            total_amount = estimate.get("total_amount") or estimate.get("total")
            update_fields["total"] = _coerce_float(total_amount)
            update_fields["total_amount"] = update_fields["total"]
            update_fields["total_cents"] = int(round(update_fields["total"] * 100))

        cleaned = {k: v for k, v in update_fields.items() if v is not None}
        if not cleaned:
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        set_clauses = []
        values: list[Any] = []
        idx = 1
        for key, value in cleaned.items():
            if key == "line_items":
                set_clauses.append(f"{key} = ${idx}::jsonb")
            else:
                set_clauses.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1
        set_clauses.append("updated_at = NOW()")

        values.extend([estimate_uuid, tenant_id])

        query = f"""
            UPDATE estimates
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND tenant_id = ${idx + 1}
            RETURNING id::text AS id
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(status_code=404, detail="Estimate not found")

        return {"success": True, "data": {"id": row["id"]}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating estimate: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update estimate")


@router.delete("/{estimate_id}")
async def delete_estimate(
    estimate_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Soft-delete an estimate for the authenticated tenant."""
    try:
        tenant_id_raw = current_user.get("tenant_id")
        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        estimate_uuid = _parse_uuid(estimate_id, "estimate_id")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE estimates
                SET status = 'declined',
                    updated_at = NOW()
                WHERE id = $1 AND tenant_id = $2
                RETURNING id::text AS id
                """,
                estimate_uuid,
                tenant_id,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Estimate not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting estimate: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete estimate")


@router.post("/{estimate_id}/convert-to-job")
async def convert_to_job(
    estimate_id: str,
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Convert an estimate to a job using the atomic DB RPC."""
    try:
        tenant_id_raw = current_user.get("tenant_id")
        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        estimate_uuid = _parse_uuid(estimate_id, "estimate_id")

        metadata = data.get("metadata") if isinstance(data, dict) else None
        if metadata is None:
            metadata = {}

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                created_by_row = await conn.fetchrow(
                    "SELECT created_by, created_by_id FROM estimates WHERE id = $1 AND tenant_id = $2 FOR UPDATE",
                    estimate_uuid,
                    tenant_id,
                )
                if not created_by_row:
                    raise HTTPException(status_code=404, detail="Estimate not found")

                created_by_data = dict(created_by_row)
                user_id = created_by_data.get("created_by") or created_by_data.get("created_by_id")
                if not user_id:
                    # Fall back to current_user if it is a UUID.
                    try:
                        user_id = _parse_uuid(current_user.get("id"), "user_id")
                    except HTTPException:
                        raise HTTPException(status_code=400, detail="Estimate has no created_by user context")

                result = await conn.fetchval(
                    "SELECT public.convert_estimate_to_job($1, $2, $3, $4::jsonb)",
                    estimate_uuid,
                    tenant_id,
                    user_id,
                    json.dumps(metadata),
                )

        # asyncpg may return jsonb as a dict, or as a string depending on codecs.
        if isinstance(result, str):
            try:
                return json.loads(result)
            except Exception:
                return {"success": True, "result": result}
        if isinstance(result, dict):
            return result
        return {"success": True, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error converting estimate to job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to convert estimate to job")

@router.get("/{estimate_id}")
async def get_estimate(
    estimate_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get estimate details."""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT e.id, e.estimate_number, e.customer_id, e.job_id, e.title, e.status,
                       e.total_amount, e.subtotal, e.tax_amount,
                       e.line_items as items,
                       e.notes,
                       e.terms_conditions as terms,
                       e.valid_until as expires_at,
                       e.created_at,
                       c.name as customer_name, c.email as customer_email,
                       j.title as job_title
                FROM estimates e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN jobs j ON e.job_id = j.id
                WHERE e.id = $1::uuid AND e.tenant_id = $2
            """, estimate_id, tenant_id)

        if not row:
            raise HTTPException(status_code=404, detail="Estimate not found")

        estimate = dict(row)
        estimate["id"] = str(estimate.get("id"))
        
        # Convert decimals
        for f in ["total_amount", "subtotal", "tax_amount"]:
            if estimate.get(f) is not None:
                estimate[f] = float(estimate[f])
        
        # Parse items if string
        if estimate.get('items') and isinstance(estimate['items'], str):
            try:
                estimate['items'] = json.loads(estimate['items'])
            except:
                estimate['items'] = []

        return {
            "success": True,
            "data": estimate
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting estimate: {e}")
        raise HTTPException(status_code=500, detail="Failed to get estimate details")
