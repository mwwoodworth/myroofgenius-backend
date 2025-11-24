from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import os
import logging
from urllib.parse import urlparse
from config import get_database_url

router = APIRouter(tags=["Public Products"])
logger = logging.getLogger(__name__)

class Product(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price_cents: Optional[int]
    category: Optional[str]
    is_active: bool
    created_at: datetime

class ProductListResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    per_page: int

@router.get("/", response_model=List[Product])
async def get_public_products(category: Optional[str] = None):
    """Get all public products - NO AUTH REQUIRED"""
    db_config = _get_db_config()
    if not db_config:
        return _fallback_products("Database configuration incomplete")["products"]

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = true AND pc.name = %s
                ORDER BY p.name
            """, (category,))
        else:
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = true
                ORDER BY p.name
            """)
        
        products = []
        for row in cursor.fetchall():
            products.append(Product(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                price_cents=row[3],
                category=row[4],
                is_active=row[5],
                created_at=row[6]
            ))
        
        cursor.close()
        conn.close()
        
        return products
        
    except Exception as e:
        logger.error(f"Failed to load public products: {e}")
        return _fallback_products("Database error loading products")["products"]

@router.get("/list", response_model=ProductListResponse)
async def get_products_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    category: Optional[str] = None
):
    """Get paginated products list - NO AUTH REQUIRED"""
    db_config = _get_db_config()
    if not db_config:
        return ProductListResponse(products=[], total=0, page=page, per_page=per_page)

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Get total count
        if category:
            cursor.execute("""
                SELECT COUNT(*)
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = true AND pc.name = %s
            """, (category,))
        else:
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = true")

        total = cursor.fetchone()[0]

        # Get paginated products
        offset = (page - 1) * per_page
        if category:
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = true AND pc.name = %s
                ORDER BY p.name
                LIMIT %s OFFSET %s
            """, (category, per_page, offset))
        else:
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
                FROM products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                WHERE p.is_active = true
                ORDER BY p.name
                LIMIT %s OFFSET %s
            """, (per_page, offset))

        products = []
        for row in cursor.fetchall():
            products.append(Product(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                price_cents=row[3],
                category=row[4],
                is_active=row[5],
                created_at=row[6]
            ))

        cursor.close()
        conn.close()

        return ProductListResponse(
            products=products,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Failed to load products list: {e}")
        return ProductListResponse(products=[], total=0, page=page, per_page=per_page)

@router.get("/featured", response_model=List[Product])
async def get_featured_products():
    """Get featured products - NO AUTH REQUIRED"""
    db_config = _get_db_config()
    if not db_config:
        return _fallback_products("Database configuration incomplete")["products"]

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.is_active = true
            ORDER BY RANDOM()
            LIMIT 3
        """)

        products = []
        for row in cursor.fetchall():
            products.append(Product(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                price_cents=row[3],
                category=row[4],
                is_active=row[5],
                created_at=row[6]
            ))

        cursor.close()
        conn.close()

        return products

    except Exception as e:
        logger.error(f"Failed to load featured products: {e}")
        return _fallback_products("Database error loading featured products")["products"]

@router.get("/categories", response_model=List[str])
async def get_product_categories():
    """Get all product categories - NO AUTH REQUIRED"""
    db_config = _get_db_config()
    if not db_config:
        return []

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT pc.name
            FROM product_categories pc
            JOIN products p ON p.category_id = pc.id
            WHERE p.is_active = true AND pc.name IS NOT NULL
            ORDER BY pc.name
        """)

        categories = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return categories

    except Exception as e:
        logger.error(f"Failed to load product categories: {e}")
        return []

@router.get("/detail/{product_id}", response_model=Product)
async def get_product_detail(product_id: str):
    """Get detailed product info - NO AUTH REQUIRED"""
    return await get_product_by_id(product_id)

@router.get("/{product_id}", response_model=Product)
async def get_product_by_id(product_id: str):
    """Get a specific product - NO AUTH REQUIRED"""
    db_config = _get_db_config()
    if not db_config:
        raise HTTPException(status_code=503, detail="Database configuration unavailable")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price_cents, pc.name as category, p.is_active, p.created_at
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            WHERE p.id = %s AND p.is_active = true
        """, (product_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")

        product = Product(
            id=str(row[0]),
            name=row[1],
            description=row[2],
            price_cents=row[3],
            category=row[4],
            is_active=row[5],
            created_at=row[6]
        )

        cursor.close()
        conn.close()

        return product

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load product detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get product")


def _get_db_config():
    """Resolve DB connection settings from environment (DATABASE_URL or DB_* vars)"""
    try:
        db_url = get_database_url()
        parsed = urlparse(db_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/") if parsed.path else None,
            "user": parsed.username,
            "password": parsed.password,
            "sslmode": "require",
            "connect_timeout": 5,
        }
    except Exception as e:
        logger.error(f"Unable to resolve database configuration: {e}")
        return None


def _fallback_products(reason: str):
    """Return a safe fallback response when DB is unavailable"""
    logger.warning(f"Serving fallback public products due to: {reason}")
    fallback = [
        Product(
            id="prod_fallback_1",
            name="Basic Plan",
            description="Fallback product listing (DB unavailable)",
            price_cents=4999,
            category="fallback",
            is_active=True,
            created_at=datetime.utcnow(),
        )
    ]
    return {
        "products": fallback,
        "total": len(fallback),
        "fallback": True,
        "note": reason,
    }
