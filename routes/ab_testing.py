"""
A/B Testing Module - Task 78
Marketing experiment management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json
import math

from core.supabase_auth import get_authenticated_user

router = APIRouter()

# Database connection
async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool

# Models
class ABTestCreate(BaseModel):
    name: str
    test_type: str = "email"  # email, landing_page, ad, content
    control_variant: Dict[str, Any]
    test_variants: List[Dict[str, Any]]
    success_metric: str
    sample_size: Optional[int] = None
    duration_days: Optional[int] = 14

# Endpoints
@router.post("/tests", response_model=dict)
async def create_ab_test(
    test: ABTestCreate,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Create A/B test"""
    query = """
        INSERT INTO ab_tests (
            name, test_type, control_variant, test_variants,
            success_metric, sample_size, duration_days, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            query,
            test.name,
            test.test_type,
            json.dumps(test.control_variant),
            json.dumps(test.test_variants),
            test.success_metric,
            test.sample_size,
            test.duration_days,
            "draft",
        )

    return {**dict(result), "id": str(result['id'])}

@router.get("/tests/{test_id}/results", response_model=dict)
async def get_test_results(
    test_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get A/B test results"""
    async with pool.acquire() as conn:
        test = await conn.fetchrow(
            """
            SELECT id, name, status, control_variant, test_variants, success_metric, created_at,
                   started_at, completed_at
            FROM ab_tests
            WHERE id = $1::uuid
            """,
            test_id,
        )

        if not test:
            raise HTTPException(status_code=404, detail="Test not found")

        assignments = await conn.fetch(
            """
            SELECT
                variant_name,
                COUNT(*)::int AS visitors,
                COUNT(*) FILTER (WHERE converted IS TRUE)::int AS conversions
            FROM ab_test_assignments
            WHERE test_id = $1::uuid
            GROUP BY variant_name
            """,
            test_id,
        )

    control_variant = test.get("control_variant")
    test_variants = test.get("test_variants")
    try:
        control_variant = json.loads(control_variant) if isinstance(control_variant, str) else control_variant
    except Exception:
        control_variant = {}
    try:
        test_variants = json.loads(test_variants) if isinstance(test_variants, str) else test_variants
    except Exception:
        test_variants = []

    results: Dict[str, Any] = {}
    for row in assignments:
        visitors = row["visitors"] or 0
        conversions = row["conversions"] or 0
        conversion_rate = round((conversions / visitors) * 100, 2) if visitors else 0.0
        results[row["variant_name"]] = {
            "visitors": visitors,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
        }

    # Determine winner (highest conversion rate among variants with data)
    winner = None
    best_rate = None
    for variant_name, stats in results.items():
        if stats["visitors"] <= 0:
            continue
        if best_rate is None or stats["conversion_rate"] > best_rate:
            best_rate = stats["conversion_rate"]
            winner = variant_name

    return {
        "test_id": str(test["id"]),
        "name": test["name"],
        "status": test["status"],
        "success_metric": test["success_metric"],
        "results": results,
        "winner": winner,
        "generated_at": datetime.utcnow().isoformat(),
    }
