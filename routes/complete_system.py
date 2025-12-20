"""
Complete System Routes
Replaces hardcoded demo payloads with real database-backed responses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


def _get_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return pool


@router.get("/products/list")
async def get_products(request: Request) -> Dict[str, Any]:
    """Get product list (DB-backed; returns empty list if table is missing)."""
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT id, name, description, price, created_at
                FROM products
                WHERE is_active = true
                ORDER BY name
                """
            )
            products = []
            for row in rows:
                data = dict(row)
                if data.get("price") is not None:
                    data["price"] = float(data["price"])
                data["id"] = str(data["id"])
                products.append(data)
            return {"success": True, "data": products}
        except asyncpg.exceptions.UndefinedColumnError:
            rows = await conn.fetch(
                """
                SELECT id, name, description, price_cents, created_at
                FROM products
                WHERE is_active = true
                ORDER BY name
                """
            )
            products = []
            for row in rows:
                data = dict(row)
                cents = data.pop("price_cents", None)
                data["price"] = (float(cents) / 100.0) if cents is not None else None
                data["id"] = str(data["id"])
                products.append(data)
            return {"success": True, "data": products}
        except asyncpg.exceptions.UndefinedTableError:
            return {"success": True, "data": []}


@router.get("/workflows")
async def get_workflows(request: Request) -> Dict[str, Any]:
    """Get workflow definitions (DB-backed; returns empty list if table is missing)."""
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT id, name, description, category, trigger_type, trigger_config, conditions, actions, is_active, created_at
                FROM workflows
                ORDER BY created_at DESC
                LIMIT 200
                """
            )
        except asyncpg.exceptions.UndefinedTableError:
            return {"success": True, "data": []}

    workflows: List[Dict[str, Any]] = []
    for row in rows:
        workflow = dict(row)
        workflow["id"] = str(workflow["id"])
        for field in ("trigger_config", "conditions", "actions"):
            value = workflow.get(field)
            if isinstance(value, str):
                try:
                    workflow[field] = json.loads(value)
                except Exception:
                    workflow[field] = {} if field != "actions" else []
        workflows.append(workflow)

    return {"success": True, "data": workflows}


@router.get("/customers")
async def get_customers(
    request: Request,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get customers (DB-backed)."""
    pool = _get_pool(request)
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT id, name, email, phone, address, city, state, zip, created_at
                FROM customers
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        except asyncpg.exceptions.UndefinedTableError:
            return {"success": True, "data": []}

    customers: List[Dict[str, Any]] = []
    for row in rows:
        customer = dict(row)
        customer["id"] = str(customer["id"]) if customer.get("id") else None
        customer["created_at"] = customer["created_at"].isoformat() if customer.get("created_at") else None
        customers.append(customer)

    return {"success": True, "data": customers}
