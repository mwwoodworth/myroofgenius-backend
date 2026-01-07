"""
Credits API - internal billing/consumption endpoints.
Used by MyRoofGenius frontend server routes for credit checks and debits.
"""

import hashlib
import hmac
import logging
import os
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credits", tags=["Credits"])


def _get_signing_secret() -> str:
    secret = (
        os.getenv("CREDITS_SIGNING_SECRET")
        or os.getenv("BACKEND_INTERNAL_API_KEY")
        or os.getenv("INTERNAL_API_KEY")
    )
    if not secret:
        raise HTTPException(status_code=500, detail="Credits signing secret not configured")
    return secret


def _verify_signature(message: str, signature: str) -> None:
    secret = _get_signing_secret()
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid credit signature")


def _verify_nonce(nonce: int) -> None:
    now = int(time.time())
    if abs(now - nonce) > 300:
        raise HTTPException(status_code=401, detail="Credit nonce expired")


def _require_internal_key(request: Request) -> None:
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    internal_key = os.getenv("BACKEND_INTERNAL_API_KEY") or os.getenv("INTERNAL_API_KEY")
    if not internal_key:
        raise HTTPException(status_code=500, detail="Internal API key not configured")
    if not api_key or not hmac.compare_digest(api_key, internal_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")


async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool


def _resolve_tenant_id(request: Request) -> Optional[str]:
    return (
        request.headers.get("X-Tenant-ID")
        or os.getenv("DEFAULT_TENANT_ID")
        or os.getenv("TENANT_ID")
    )


class CreditBalanceRequest(BaseModel):
    user_email: str = Field(..., min_length=3)
    nonce: int
    signature: str


class CreditDebitRequest(BaseModel):
    user_email: str = Field(..., min_length=3)
    amount: int = Field(..., gt=0)
    reason: Optional[str] = None
    nonce: int
    signature: str


@router.post("/balance")
async def get_credit_balance(
    payload: CreditBalanceRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    _require_internal_key(request)
    _verify_nonce(payload.nonce)
    _verify_signature(f"{payload.user_email.lower()}:{payload.nonce}", payload.signature)

    tenant_id = _resolve_tenant_id(request)

    async with db_pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT id FROM auth.users WHERE lower(email) = lower($1)",
            payload.user_email,
        )
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_row["id"]

        credits_row = await conn.fetchrow(
            """
            SELECT credits_available, credits_used, credits_total, updated_at
            FROM user_credits
            WHERE user_id = $1
            """,
            user_id,
        )

        if not credits_row:
            await conn.execute(
                """
                INSERT INTO user_credits (user_id, credits_available, credits_used, credits_total)
                VALUES ($1, 0, 0, 0)
                """,
                user_id,
            )
            credits_available = 0
            credits_used = 0
            credits_total = 0
            last_updated = None
        else:
            credits_available = credits_row["credits_available"] or 0
            credits_used = credits_row["credits_used"] or 0
            credits_total = credits_row["credits_total"] or 0
            last_updated = credits_row["updated_at"]

    return {
        "credits": credits_available,
        "credits_used": credits_used,
        "credits_total": credits_total,
        "last_updated": last_updated.isoformat() if last_updated else None,
        "tenant_id": tenant_id,
    }


@router.post("/debit")
async def debit_credits(
    payload: CreditDebitRequest,
    request: Request,
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    _require_internal_key(request)
    _verify_nonce(payload.nonce)
    _verify_signature(
        f"{payload.user_email.lower()}:{payload.amount}:{payload.nonce}",
        payload.signature,
    )

    tenant_id = _resolve_tenant_id(request)

    async with db_pool.acquire() as conn:
        async with conn.transaction():
            user_row = await conn.fetchrow(
                "SELECT id FROM auth.users WHERE lower(email) = lower($1)",
                payload.user_email,
            )
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")

            user_id = user_row["id"]
            credits_row = await conn.fetchrow(
                """
                SELECT credits_available, credits_used, credits_total
                FROM user_credits
                WHERE user_id = $1
                FOR UPDATE
                """,
                user_id,
            )

            if not credits_row:
                await conn.execute(
                    """
                    INSERT INTO user_credits (user_id, credits_available, credits_used, credits_total)
                    VALUES ($1, 0, 0, 0)
                    """,
                    user_id,
                )
                credits_available = 0
                credits_used = 0
                credits_total = 0
            else:
                credits_available = credits_row["credits_available"] or 0
                credits_used = credits_row["credits_used"] or 0
                credits_total = credits_row["credits_total"] or 0

            if credits_available < payload.amount:
                raise HTTPException(status_code=402, detail="Insufficient credits")

            new_available = credits_available - payload.amount
            new_used = credits_used + payload.amount
            new_total = max(credits_total, new_available + new_used)

            await conn.execute(
                """
                UPDATE user_credits
                SET credits_available = $1,
                    credits_used = $2,
                    credits_total = $3,
                    updated_at = NOW()
                WHERE user_id = $4
                """,
                new_available,
                new_used,
                new_total,
                user_id,
            )

            await conn.execute(
                """
                INSERT INTO credit_transactions (
                    user_id, amount, balance_after, type, description, tenant_id
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id,
                -payload.amount,
                new_available,
                "usage",
                payload.reason or "credit_debit",
                tenant_id,
            )

    return {
        "status": "ok",
        "debited": payload.amount,
        "balance": new_available,
    }
