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

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

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
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all invoices for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            logger.warning("Database pool unavailable; returning fallback invoices list.")
            return {
                "success": True,
                "data": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "degraded": True,
                "message": "Database unavailable; returning empty invoices list."
            }

        query = """
            SELECT i.id, i.invoice_number, i.customer_id, i.total_amount,
                   i.status, i.due_date, i.items, i.created_at,
                   c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
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

            total = await conn.fetchval(count_query, *count_params)

        # Convert to list of dicts
        result = []
        for invoice in invoices:
            invoice_dict = dict(invoice)
            # Convert Decimal to float for JSON serialization
            if invoice_dict.get('total_amount'):
                invoice_dict['total_amount'] = float(invoice_dict['total_amount'])
            # Parse items if string
            if invoice_dict.get('items') and isinstance(invoice_dict['items'], str):
                try:
                    invoice_dict['items'] = json.loads(invoice_dict['items'])
                except:
                    invoice_dict['items'] = []
            result.append(invoice_dict)

        return {
            "success": True,
            "data": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        message = str(e)
        logger.warning(f"Invoices listing degraded fallback activated: {message}")
        return {
            "success": True,
            "data": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "degraded": True,
            "message": "Invoices data unavailable; returning empty list."
        }

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
            logger.warning("Database pool unavailable; returning fallback invoice detail.")
            return {
                "success": True,
                "data": None,
                "degraded": True,
                "message": "Database unavailable; invoice details unavailable."
            }

        async with db_pool.acquire() as conn:
            invoice = await conn.fetchrow("""
                SELECT i.id, i.invoice_number, i.customer_id, i.total_amount,
                       i.status, i.due_date, i.items, i.created_at,
                       c.name as customer_name, c.email as customer_email
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.id = $1::uuid AND i.tenant_id = $2
            """, invoice_id, tenant_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice_dict = dict(invoice)
        # Convert Decimal to float
        if invoice_dict.get('total_amount'):
            invoice_dict['total_amount'] = float(invoice_dict['total_amount'])
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
        message = str(e)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Invoices schema not available; returning fallback invoice detail.")
            return {
                "success": True,
                "data": None,
                "degraded": True,
                "message": "Invoices schema unavailable; details cannot be retrieved."
            }
        logger.error(f"Error getting invoice: {message}")
        raise HTTPException(status_code=500, detail="Failed to get invoice")

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
            logger.warning("Database pool unavailable; returning fallback invoice stats.")
            return {
                "success": True,
                "data": {
                    "total_invoices": 0,
                    "by_status": {
                        "draft": 0,
                        "sent": 0,
                        "paid": 0,
                        "overdue": 0
                    },
                    "amounts": {
                        "total": 0.0,
                        "paid": 0.0,
                        "overdue": 0.0
                    }
                },
                "degraded": True,
                "message": "Database unavailable; returning empty invoice statistics."
            }

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
        message = str(e)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Invoices statistics schema unavailable; returning fallback statistics.")
            return {
                "success": True,
                "data": {
                    "total_invoices": 0,
                    "by_status": {
                        "draft": 0,
                        "sent": 0,
                        "paid": 0,
                        "overdue": 0
                    },
                    "amounts": {
                        "total": 0.0,
                        "paid": 0.0,
                        "overdue": 0.0
                    }
                },
                "degraded": True,
                "message": "Invoice statistics unavailable; returning empty dataset."
            }
        logger.error(f"Error getting invoice stats: {message}")
        raise HTTPException(status_code=500, detail="Failed to get invoice statistics")
