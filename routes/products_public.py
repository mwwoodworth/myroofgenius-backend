from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import os

router = APIRouter(tags=["Public Products"])

class Product(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price_cents: Optional[int]
    category: Optional[str]
    is_active: bool
    created_at: datetime

@router.get("/", response_model=List[Product])
async def get_public_products(category: Optional[str] = None):
    """Get all public products - NO AUTH REQUIRED"""
    try:
        conn = psycopg2.connect(
            host='aws-0-us-east-2.pooler.supabase.com',
            port=6543,
            database='postgres',
            user='postgres.yomagoqdmxszqtdwuhab',
            password='Brain0ps2O2S'
        )
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}", response_model=Product)
async def get_product_by_id(product_id: str):
    """Get a specific product - NO AUTH REQUIRED"""
    try:
        conn = psycopg2.connect(
            host='aws-0-us-east-2.pooler.supabase.com',
            port=6543,
            database='postgres',
            user='postgres.yomagoqdmxszqtdwuhab',
            password='Brain0ps2O2S'
        )
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
        raise HTTPException(status_code=500, detail=str(e))
