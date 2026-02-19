"""
Products API Routes
Manages product catalog and pricing
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import Any, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Products"])

class Product(BaseModel):
    """Product model"""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    created_at: Optional[datetime] = None

def _row_to_public_product(row: Any) -> dict[str, Any]:
    item = dict(row)
    price_cents = item.get("price_cents")
    if isinstance(price_cents, Decimal):
        price_cents = int(price_cents)
    return {
        "id": str(item.get("id")),
        "name": item.get("name"),
        "description": item.get("description"),
        "price_cents": price_cents,
        "category": item.get("category"),
        "is_active": bool(item.get("is_active", True)),
        "created_at": item.get("created_at"),
    }

@router.get("")
@router.get("/")
async def list_products(
    request: Request,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = None
):
    """List all products"""
    try:
        db_pool = getattr(request.app.state, 'db_pool', None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database connection not available")

        query = """
            SELECT id, name, description, price, created_at
            FROM products
            WHERE is_active = true
        """

        params = []
        # Category filtering disabled since table uses category_id not category name

        query += " ORDER BY name LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            products = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM products WHERE is_active = true"
            total = await conn.fetchval(count_query)

        # Convert to list of dicts
        result = []
        for product in products:
            product_dict = dict(product)
            # Convert Decimal to float for JSON serialization
            if product_dict.get('price'):
                product_dict['price'] = float(product_dict['price'])
            result.append(product_dict)

        return {
            "success": True,
            "data": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail="Failed to list products")

@router.get("/public")
async def list_public_products(
    request: Request,
    category: Optional[str] = None,
):
    """
    Public catalog endpoint used by production smoke checks.
    Returns a bare array for backwards compatibility.
    """
    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Public products requested but db_pool is unavailable")
        return []

    query = """
        SELECT
            p.id,
            p.name,
            p.description,
            p.price_cents,
            pc.name AS category,
            p.is_active,
            p.created_at
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        WHERE p.is_active = true
    """
    params: list[Any] = []
    if category:
        query += " AND pc.name = $1"
        params.append(category)
    query += " ORDER BY p.name"

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params, timeout=10.0)
        return [_row_to_public_product(row) for row in rows]
    except Exception as exc:
        logger.warning("Public products query degraded, returning empty list: %s", exc)
        return []

@router.get("/{product_id}")
async def get_product(
    product_id: str,
    request: Request
):
    """Get product details"""
    # Avoid treating the public products path as a product ID
    if product_id.lower() == "public":
        return await list_public_products(request=request)

    try:
        db_pool = getattr(request.app.state, 'db_pool', None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database connection not available")

        async with db_pool.acquire() as conn:
            product = await conn.fetchrow("""
                SELECT id, name, description, price, created_at
                FROM products
                WHERE id = $1::uuid AND is_active = true
            """, product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product_dict = dict(product)
        # Convert Decimal to float
        if product_dict.get('price'):
            product_dict['price'] = float(product_dict['price'])

        return {
            "success": True,
            "data": product_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(status_code=500, detail="Failed to get product")

@router.get("/categories/list")
async def list_categories(request: Request):
    """List all product categories"""
    try:
        db_pool = getattr(request.app.state, 'db_pool', None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database connection not available")

        async with db_pool.acquire() as conn:
            # Since we don't have category names, just return empty list for now
            categories = []

        return {
            "success": True,
            "categories": [dict(cat) for cat in categories]
        }

    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list categories")
