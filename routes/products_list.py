"""
Product List Route
Provides product catalog functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import logging

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/list")
def get_products_list(db: Session = Depends(get_db)):
    """Get list of all products"""
    try:
        # Check if products table exists
        check_table = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'products'
            )
        """)

        table_exists = db.execute(check_table).scalar()

        if not table_exists:
            return {
                "success": True,
                "data": [],
                "message": "No products available"
            }

        # Get real products if table exists
        query = text("""
            SELECT
                id,
                name,
                description,
                price,
                category,
                sku,
                status,
                created_at
            FROM products
            WHERE status = 'active'
            ORDER BY category, name
            LIMIT 100
        """)

        result = db.execute(query)
        products = []

        for row in result:
            product = dict(row._mapping)
            # Convert UUID to string if needed
            if product.get('id'):
                product['id'] = str(product['id'])
            # Convert datetime to ISO format
            if product.get('created_at'):
                product['created_at'] = product['created_at'].isoformat()
            products.append(product)

        return {
            "success": True,
            "data": products
        }

    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")
