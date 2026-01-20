"""
Marketplace compatibility endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db


router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


@router.get("")
def list_marketplace_products(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        rows = (
            db.execute(
                text(
                    """
                    SELECT id, name, description, unit_price, monthly_price, unit_label,
                           category, features, usage_limits, is_active, created_at
                    FROM marketplace_products
                    WHERE is_active = true
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
            .mappings()
            .all()
        )

        return {
            "products": [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "unit_price": row["unit_price"],
                    "monthly_price": row["monthly_price"],
                    "unit_label": row["unit_label"],
                    "category": row["category"],
                    "features": row["features"] or [],
                    "usage_limits": row["usage_limits"] or {},
                }
                for row in rows
            ],
            "total": len(rows),
        }
    except Exception as exc:
        message = str(exc).lower()
        if "does not exist" in message or "undefinedtable" in message:
            rows = (
                db.execute(
                    text(
                        """
                        SELECT id, name, description, price, category, features, stripe_price_id, created_at
                        FROM products
                        WHERE is_active = true
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"limit": limit},
                )
                .mappings()
                .all()
            )
            return {
                "products": [
                    {
                        "id": str(row["id"]),
                        "name": row["name"],
                        "description": row["description"],
                        "unit_price": row["price"],
                        "category": row["category"],
                        "features": row["features"] or [],
                        "stripe_price_id": row["stripe_price_id"],
                    }
                    for row in rows
                ],
                "total": len(rows),
            }

        raise HTTPException(status_code=500, detail="Failed to load marketplace products") from exc
