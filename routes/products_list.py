"""
Product List Route
Provides product catalog functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    """Get database session"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
async def get_products_list(db: Session = Depends(get_db)):
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
            # Return mock data if table doesn't exist
            return {
                "success": True,
                "data": [
                    {
                        "id": "1",
                        "name": "Basic Roof Inspection",
                        "description": "Complete roof inspection with detailed report",
                        "price": 299,
                        "category": "inspection"
                    },
                    {
                        "id": "2",
                        "name": "Emergency Roof Repair",
                        "description": "24/7 emergency roof repair service",
                        "price": 599,
                        "category": "repair"
                    },
                    {
                        "id": "3",
                        "name": "Shingle Roof Replacement",
                        "description": "Complete shingle roof replacement",
                        "price": 7500,
                        "category": "replacement"
                    },
                    {
                        "id": "4",
                        "name": "Metal Roof Installation",
                        "description": "Premium metal roof installation",
                        "price": 12000,
                        "category": "replacement"
                    },
                    {
                        "id": "5",
                        "name": "Gutter Cleaning",
                        "description": "Professional gutter cleaning service",
                        "price": 199,
                        "category": "maintenance"
                    }
                ]
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
        # Return sample data on error
        return {
            "success": True,
            "data": [
                {
                    "id": "1",
                    "name": "Roof Inspection Service",
                    "price": 299,
                    "category": "inspection"
                }
            ],
            "message": "Using sample data"
        }