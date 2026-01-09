"""
Invoices API Routes
Manages invoices and billing
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
import logging
import json
from uuid import UUID, uuid4

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

def _parse_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
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


def _compute_amounts_from_items(items: Any) -> tuple[float, float, float]:
    """Return (subtotal, tax, total) from loosely-typed invoice items."""
    if not items:
        return 0.0, 0.0, 0.0
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return 0.0, 0.0, 0.0

    subtotal = 0.0
    tax = 0.0

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("total") is not None:
            subtotal += _coerce_float(item.get("total"))
        else:
            quantity = _coerce_float(item.get("quantity") or 1)
            unit_price = _coerce_float(item.get("unit_price") or item.get("price") or 0)
            subtotal += quantity * unit_price

        tax_rate = item.get("tax_rate")
        if tax_rate is not None:
            try:
                tax += subtotal * (_coerce_float(tax_rate) / 100.0)
            except Exception:
                pass

    total = subtotal + tax
    return subtotal, tax, total

class Invoice(BaseModel):
    """Invoice model"""
    id: str
    invoice_number: str
    customer_id: str
    total_amount: float
    status: str = "draft"
    due_date: Optional[date] = None
    items: Optional[List[dict]] = []
    created_at: Optional[datetime] = None

@router.get("")
async def list_invoices(
    request: Request,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all invoices for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT i.id, i.invoice_number, i.customer_id, i.job_id,
                   COALESCE(i.subtotal_amount, i.subtotal, 0) as subtotal,
                   COALESCE(i.tax_amount, i.tax, 0) as tax_amount,
                   COALESCE(i.total_amount, i.total, i.amount, 0) as total_amount,
                   COALESCE(i.paid_amount, 0) as paid_amount,
                   COALESCE(i.balance_due, i.amount_due, (COALESCE(i.total_amount, i.total, i.amount, 0) - COALESCE(i.paid_amount, 0))) as balance,
                   i.status,
                   i.due_date,
                   COALESCE(i.issue_date, i.invoice_date) as issued_date,
                   i.created_at,
                   c.name as customer_name,
                   j.title as job_title
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.tenant_id = $1
        """

        params = [tenant_id]
        param_count = 0

        if status:
            param_count += 1
            query += f" AND i.status = ${param_count + 1}"
            params.append(status)

        if customer_id:
            param_count += 1
            query += f" AND i.customer_id = ${param_count + 1}"
            params.append(customer_id)

        if job_id:
            param_count += 1
            query += f" AND i.job_id = ${param_count + 1}"
            params.append(job_id)

        query += " ORDER BY i.created_at DESC LIMIT ${} OFFSET ${}".format(param_count + 2, param_count + 3)
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            invoices = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM invoices WHERE tenant_id = $1"
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

        # Convert to list of dicts
        result = []
        for invoice in invoices:
            invoice_dict = dict(invoice)
            # Convert Decimal to float for JSON serialization
            for field in ['subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance']:
                value = invoice_dict.get(field)
                if value is not None:
                    invoice_dict[field] = float(value)
            result.append(invoice_dict)

        return {
            "success": True,
            "data": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@router.post("/")  # Handle both with and without trailing slash
async def create_invoice(
    request: Request,
    invoice: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create an invoice for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")

        customer_id_raw = invoice.get("customer_id")
        if not customer_id_raw:
            raise HTTPException(status_code=400, detail="customer_id is required")
        customer_id = _parse_uuid(customer_id_raw, "customer_id")

        invoice_number = (invoice.get("invoice_number") or f"INV-{uuid4().hex[:10].upper()}").strip()
        title = (invoice.get("title") or "Invoice").strip() or "Invoice"
        status = (invoice.get("status") or "draft").strip() or "draft"

        line_items = invoice.get("line_items") or invoice.get("items") or []
        if isinstance(line_items, str):
            try:
                line_items = json.loads(line_items)
            except Exception:
                line_items = []
        line_items_json = json.dumps(line_items)

        subtotal_amount = invoice.get("subtotal_amount") or invoice.get("subtotal") or None
        tax_amount = invoice.get("tax_amount") or invoice.get("tax") or 0
        total_amount = invoice.get("total_amount") or invoice.get("total") or invoice.get("amount") or None

        if subtotal_amount is None or total_amount is None:
            computed_subtotal, computed_tax, computed_total = _compute_amounts_from_items(line_items)
            subtotal_amount = computed_subtotal if subtotal_amount is None else _coerce_float(subtotal_amount)
            total_amount = computed_total if total_amount is None else _coerce_float(total_amount)
            tax_amount = _coerce_float(tax_amount) if tax_amount is not None else computed_tax

        subtotal_amount_f = _coerce_float(subtotal_amount)
        tax_amount_f = _coerce_float(tax_amount)
        total_amount_f = _coerce_float(total_amount)

        paid_amount_f = _coerce_float(invoice.get("paid_amount") or 0)
        balance_amount_f = max(0.0, total_amount_f - paid_amount_f)

        invoice_date = invoice.get("invoice_date") or invoice.get("issue_date") or None
        due_date = invoice.get("due_date") or None

        invoice_id = uuid4()

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                org_id = await conn.fetchval(
                    "SELECT org_id FROM invoices WHERE tenant_id = $1 LIMIT 1",
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
                    INSERT INTO invoices (
                        id,
                        tenant_id,
                        org_id,
                        invoice_number,
                        customer_id,
                        title,
                        status,
                        invoice_date,
                        issue_date,
                        due_date,
                        line_items,
                        items,
                        subtotal_amount,
                        tax_amount,
                        total_amount,
                        subtotal_cents,
                        tax_cents,
                        total_cents,
                        amount_paid_cents,
                        paid_amount,
                        balance_cents,
                        balance_due,
                        created_at,
                        updated_at
                    ) VALUES (
                        $1, $2, $3,
                        $4, $5, $6, $7,
                        COALESCE($8::date, CURRENT_DATE),
                        COALESCE($8::date, CURRENT_DATE),
                        COALESCE($9::date, CURRENT_DATE + INTERVAL '14 days'),
                        $10::jsonb,
                        $10::jsonb,
                        $11, $12, $13,
                        $14, $15, $16,
                        $17, $18,
                        $19, $20,
                        NOW(), NOW()
                    )
                    RETURNING id::text AS id
                    """,
                    invoice_id,
                    tenant_id,
                    org_id,
                    invoice_number,
                    customer_id,
                    title,
                    status,
                    invoice_date,
                    due_date,
                    line_items_json,
                    subtotal_amount_f,
                    tax_amount_f,
                    total_amount_f,
                    int(round(subtotal_amount_f * 100)),
                    int(round(tax_amount_f * 100)),
                    int(round(total_amount_f * 100)),
                    int(round(paid_amount_f * 100)),
                    paid_amount_f,
                    int(round(balance_amount_f * 100)),
                    balance_amount_f,
                )

        return {"success": True, "data": {"id": row["id"] if row else str(invoice_id)}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating invoice: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create invoice")


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    request: Request,
    invoice: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update an invoice for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        invoice_uuid = _parse_uuid(invoice_id, "invoice_id")

        update_fields: Dict[str, Any] = {}

        if "title" in invoice:
            update_fields["title"] = (invoice.get("title") or "").strip() or None
        if "status" in invoice:
            update_fields["status"] = (invoice.get("status") or "").strip() or None
        if "due_date" in invoice:
            update_fields["due_date"] = invoice.get("due_date")
        if "invoice_date" in invoice or "issue_date" in invoice:
            update_fields["invoice_date"] = invoice.get("invoice_date") or invoice.get("issue_date")
            update_fields["issue_date"] = update_fields["invoice_date"]
        if "notes" in invoice:
            update_fields["notes"] = invoice.get("notes")
        if "payment_terms" in invoice or "terms_conditions" in invoice or "terms" in invoice:
            update_fields["terms_conditions"] = invoice.get("terms_conditions") or invoice.get("terms") or invoice.get("payment_terms")

        # Items/line items update (recompute totals)
        if "items" in invoice or "line_items" in invoice:
            line_items = invoice.get("line_items") or invoice.get("items") or []
            if isinstance(line_items, str):
                try:
                    line_items = json.loads(line_items)
                except Exception:
                    line_items = []

            subtotal, tax, total = _compute_amounts_from_items(line_items)
            line_items_json = json.dumps(line_items)
            update_fields.update(
                {
                    "line_items": line_items_json,
                    "items": line_items_json,
                    "subtotal_amount": subtotal,
                    "tax_amount": tax,
                    "total_amount": total,
                    "subtotal_cents": int(round(subtotal * 100)),
                    "tax_cents": int(round(tax * 100)),
                    "total_cents": int(round(total * 100)),
                }
            )

        if "paid_amount" in invoice:
            paid_amount = _coerce_float(invoice.get("paid_amount"))
            update_fields["paid_amount"] = paid_amount
            update_fields["amount_paid_cents"] = int(round(paid_amount * 100))

        # Drop None fields to avoid blanking.
        cleaned = {k: v for k, v in update_fields.items() if v is not None}
        if not cleaned:
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        set_clauses = []
        values: list[Any] = []
        idx = 1
        for key, value in cleaned.items():
            if key in {"line_items", "items"}:
                set_clauses.append(f"{key} = ${idx}::jsonb")
            else:
                set_clauses.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1
        set_clauses.append("updated_at = NOW()")

        # If totals or paid_amount changed, keep balance fields consistent.
        needs_balance_refresh = any(k in cleaned for k in ("total_amount", "total_cents", "paid_amount", "amount_paid_cents"))
        if needs_balance_refresh:
            set_clauses.append("balance_due = GREATEST(0, COALESCE(total_amount, total, 0) - COALESCE(paid_amount, 0))")
            set_clauses.append("balance_cents = GREATEST(0, COALESCE(total_cents, 0) - COALESCE(amount_paid_cents, 0))")

        values.extend([invoice_uuid, tenant_id])

        query = f"""
            UPDATE invoices
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND tenant_id = ${idx + 1}
            RETURNING id::text AS id
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {"success": True, "data": {"id": row["id"]}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating invoice: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update invoice")


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Void an invoice for the authenticated tenant (soft delete)."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        invoice_uuid = _parse_uuid(invoice_id, "invoice_id")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE invoices
                SET status = 'voided',
                    void_date = NOW(),
                    void_reason = 'Voided via API',
                    updated_at = NOW()
                WHERE id = $1 AND tenant_id = $2
                RETURNING id::text AS id
                """,
                invoice_uuid,
                tenant_id,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting invoice: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete invoice")

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get invoice details for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            invoice = await conn.fetchrow("""
                SELECT i.id, i.invoice_number, i.customer_id, i.job_id,
                       COALESCE(i.subtotal_amount, i.subtotal, 0) as subtotal,
                       COALESCE(i.tax_amount, i.tax, 0) as tax_amount,
                       COALESCE(i.total_amount, i.total, i.amount, 0) as total_amount,
                       COALESCE(i.paid_amount, 0) as paid_amount,
                       COALESCE(i.balance_due, i.amount_due, (COALESCE(i.total_amount, i.total, i.amount, 0) - COALESCE(i.paid_amount, 0))) as balance,
                       i.status,
                       i.due_date,
                       COALESCE(i.issue_date, i.invoice_date) as issued_date,
                       COALESCE(i.items, i.line_items) as items,
                       i.notes,
                       COALESCE(i.terms_conditions, i.payment_terms) as terms,
                       i.created_at,
                       c.name as customer_name, c.email as customer_email, c.address as customer_address,
                       j.title as job_title
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN jobs j ON i.job_id = j.id
                WHERE i.id = $1::uuid AND i.tenant_id = $2
            """, invoice_id, tenant_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice_dict = dict(invoice)
        # Convert Decimal to float
        for field in ['subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance']:
            value = invoice_dict.get(field)
            if value is not None:
                invoice_dict[field] = float(value)
        
        # Parse items if string
        if invoice_dict.get('items') and isinstance(invoice_dict['items'], str):
            try:
                invoice_dict['items'] = json.loads(invoice_dict['items'])
            except:
                invoice_dict['items'] = []

        return {
            "success": True,
            "data": invoice_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invoice details")

@router.get("/stats/summary")
async def get_invoice_stats(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get invoice statistics for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_invoices,
                    COUNT(*) FILTER (WHERE status = 'draft') as draft,
                    COUNT(*) FILTER (WHERE status = 'sent') as sent,
                    COUNT(*) FILTER (WHERE status = 'paid') as paid,
                    COUNT(*) FILTER (WHERE status = 'overdue') as overdue,
                    COALESCE(SUM(total_amount), 0) as total_amount,
                    COALESCE(SUM(total_amount) FILTER (WHERE status = 'paid'), 0) as paid_amount,
                    COALESCE(SUM(total_amount) FILTER (WHERE status = 'overdue'), 0) as overdue_amount
                FROM invoices
                WHERE tenant_id = $1
            """, tenant_id)

        return {
            "success": True,
            "data": {
                "total_invoices": stats['total_invoices'],
                "by_status": {
                    "draft": stats['draft'],
                    "sent": stats['sent'],
                    "paid": stats['paid'],
                    "overdue": stats['overdue']
                },
                "amounts": {
                    "total": float(stats['total_amount']),
                    "paid": float(stats['paid_amount']),
                    "overdue": float(stats['overdue_amount'])
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting invoice stats: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to get invoice statistics")
