"""
Predictive Analytics Module - Task 94
ML-based predictions and forecasting
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json
import math

from core.supabase_auth import get_authenticated_user

router = APIRouter()

async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool

@router.get("/forecast/revenue")
async def forecast_revenue(
    months: int = 6,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Forecast revenue using predictive models"""
    if months < 1 or months > 36:
        raise HTTPException(status_code=400, detail="months must be between 1 and 36")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    async with pool.acquire() as conn:
        historical_rows = await conn.fetch(
            """
            SELECT
                DATE_TRUNC('month', created_at) as month,
                COALESCE(SUM(COALESCE(total_amount, 0)), 0) as revenue
            FROM invoices
            WHERE tenant_id = $1
              AND (status = 'paid' OR payment_status = 'paid')
              AND created_at >= NOW() - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month
            """,
            tenant_id,
        )

    historical = [{"month": r["month"], "revenue": float(r["revenue"] or 0)} for r in historical_rows]

    if len(historical) < 2:
        return {
            "historical_months": len(historical),
            "forecast_months": months,
            "predictions": [],
            "model": "trend",
            "available": False,
        }

    # Compute average month-over-month growth rate from historical series.
    growth_rates: List[float] = []
    for prev, cur in zip(historical[:-1], historical[1:]):
        prev_rev = prev["revenue"]
        cur_rev = cur["revenue"]
        if prev_rev > 0:
            growth_rates.append((cur_rev - prev_rev) / prev_rev)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
    last_month = historical[-1]["month"]
    last_revenue = historical[-1]["revenue"]

    # Confidence based on observed volatility.
    mean = sum(h["revenue"] for h in historical) / len(historical)
    variance = sum((h["revenue"] - mean) ** 2 for h in historical) / max(len(historical) - 1, 1)
    stdev = math.sqrt(variance) if variance > 0 else 0.0

    predictions: List[Dict[str, Any]] = []
    for i in range(1, months + 1):
        month_start = (last_month + timedelta(days=32 * i)).replace(day=1)
        predicted = last_revenue * ((1 + avg_growth) ** i)
        # Very simple interval based on historical stdev.
        lower = max(0.0, predicted - stdev)
        upper = predicted + stdev
        confidence = max(0.0, min(1.0, 1.0 - (i / (months + 1))))
        predictions.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "predicted_revenue": round(predicted, 2),
                "confidence_interval": {"lower": round(lower, 2), "upper": round(upper, 2)},
                "confidence": round(confidence, 3),
            }
        )

    return {
        "historical_months": len(historical),
        "forecast_months": months,
        "historical": [{"month": h["month"].strftime("%Y-%m"), "revenue": h["revenue"]} for h in historical],
        "predictions": predictions,
        "model": "trend",
        "avg_monthly_growth_rate": round(avg_growth, 4),
    }

@router.get("/predict/churn")
async def predict_customer_churn(
    customer_id: Optional[str] = None,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Predict customer churn probability"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    async with pool.acquire() as conn:
        if customer_id:
            row = await conn.fetchrow(
                """
                SELECT
                    c.id,
                    EXTRACT(DAY FROM NOW() - MAX(s.created_at))::int AS days_since_login,
                    COUNT(DISTINCT CASE WHEN i.status = 'overdue' THEN i.id END)::int AS overdue_invoices,
                    COUNT(s.id)::int AS session_count
                FROM customers c
                LEFT JOIN user_sessions s ON s.user_id = c.id
                LEFT JOIN invoices i ON i.customer_id = c.id AND i.tenant_id = c.tenant_id
                WHERE c.tenant_id = $1 AND c.id = $2::uuid
                GROUP BY c.id
                """,
                tenant_id,
                customer_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")

            days_since_login = row["days_since_login"] if row["days_since_login"] is not None else 999
            overdue_invoices = row["overdue_invoices"] or 0
            session_count = row["session_count"] or 0

            risk_score = 0
            risk_factors: List[Dict[str, Any]] = []

            if days_since_login >= 30:
                risk_score += 40
                risk_factors.append({"factor": "no_recent_login", "impact": 0.4})
            elif days_since_login >= 14:
                risk_score += 20
                risk_factors.append({"factor": "low_recent_login", "impact": 0.2})

            if session_count < 3:
                risk_score += 15
                risk_factors.append({"factor": "low_engagement", "impact": 0.15})

            if overdue_invoices > 0:
                risk_score += min(30, overdue_invoices * 10)
                risk_factors.append({"factor": "payment_issues", "impact": 0.3})

            risk_score = max(0, min(100, risk_score))
            churn_probability = round(risk_score / 100, 3)

            if churn_probability >= 0.7:
                risk_level = "high"
            elif churn_probability >= 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"

            actions = []
            if risk_level == "high":
                actions = ["Contact customer", "Offer retention incentive", "Schedule review call"]
            elif risk_level == "medium":
                actions = ["Send engagement email", "Share product tips", "Check in on satisfaction"]

            return {
                "customer_id": customer_id,
                "churn_probability": churn_probability,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommended_actions": actions,
            }

        # Batch: score all customers for tenant.
        rows = await conn.fetch(
            """
            SELECT
                c.id,
                EXTRACT(DAY FROM NOW() - MAX(s.created_at))::int AS days_since_login,
                COUNT(DISTINCT CASE WHEN i.status = 'overdue' THEN i.id END)::int AS overdue_invoices,
                COUNT(s.id)::int AS session_count
            FROM customers c
            LEFT JOIN user_sessions s ON s.user_id = c.id
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.tenant_id = c.tenant_id
            WHERE c.tenant_id = $1
            GROUP BY c.id
            """,
            tenant_id,
        )

    probabilities: List[float] = []
    high = medium = low = 0
    for row in rows:
        days_since_login = row["days_since_login"] if row["days_since_login"] is not None else 999
        overdue_invoices = row["overdue_invoices"] or 0
        session_count = row["session_count"] or 0

        score = 0
        if days_since_login >= 30:
            score += 40
        elif days_since_login >= 14:
            score += 20
        if session_count < 3:
            score += 15
        if overdue_invoices > 0:
            score += min(30, overdue_invoices * 10)
        score = max(0, min(100, score))
        prob = score / 100
        probabilities.append(prob)
        if prob >= 0.7:
            high += 1
        elif prob >= 0.4:
            medium += 1
        else:
            low += 1

    avg_prob = round(sum(probabilities) / len(probabilities), 3) if probabilities else None
    return {
        "total_customers_analyzed": len(rows),
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "avg_churn_probability": avg_prob,
    }

@router.get("/predict/demand")
async def predict_demand(
    product_category: Optional[str] = None,
    days_ahead: int = 30,
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Predict demand for products/services"""
    if days_ahead < 1 or days_ahead > 365:
        raise HTTPException(status_code=400, detail="days_ahead must be between 1 and 365")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    async with pool.acquire() as conn:
        # Use jobs created per week as a demand proxy.
        try:
            rows = await conn.fetch(
                """
                SELECT date_trunc('week', created_at) AS week,
                       COUNT(*)::int AS jobs
                FROM jobs
                WHERE tenant_id = $1
                  AND created_at >= NOW() - INTERVAL '26 weeks'
                GROUP BY 1
                ORDER BY 1
                """,
                tenant_id,
            )
        except Exception:
            rows = []

    series = [int(r["jobs"]) for r in rows]
    baseline = sum(series[-4:]) / 4 if len(series) >= 4 else (sum(series) / len(series) if series else None)

    predictions: List[Dict[str, Any]] = []
    if baseline is not None:
        for i in range(0, days_ahead, 7):
            date = datetime.now() + timedelta(days=i)
            predictions.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "predicted_demand": int(round(baseline)),
                    "confidence": 0.75,
                }
            )

    return {
        "product_category": product_category or "all",
        "forecast_period": f"{days_ahead} days",
        "predictions": predictions,
        "available": baseline is not None,
    }

@router.get("/anomalies")
async def detect_anomalies(
    metric: str = Query("revenue"),
    sensitivity: float = Query(0.95),
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Detect anomalies in business metrics"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    if metric != "revenue":
        raise HTTPException(status_code=400, detail="Only 'revenue' anomaly detection is supported")

    # Convert sensitivity to a rough z-score threshold (95% ~ 2.0).
    z_threshold = 2.0
    if sensitivity >= 0.99:
        z_threshold = 2.6
    elif sensitivity >= 0.975:
        z_threshold = 2.2

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DATE_TRUNC('day', created_at) AS day,
                   COALESCE(SUM(COALESCE(total_amount, 0)), 0) AS revenue
            FROM invoices
            WHERE tenant_id = $1
              AND (status = 'paid' OR payment_status = 'paid')
              AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY 1
            ORDER BY 1
            """,
            tenant_id,
        )

    values = [float(r["revenue"] or 0) for r in rows]
    if len(values) < 5:
        return {"metric": metric, "sensitivity": sensitivity, "anomalies_detected": 0, "anomalies": []}

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)
    stdev = math.sqrt(variance) if variance > 0 else 0.0

    anomalies: List[Dict[str, Any]] = []
    if stdev > 0:
        for row in rows:
            actual = float(row["revenue"] or 0)
            z = (actual - mean) / stdev
            if abs(z) >= z_threshold:
                anomalies.append(
                    {
                        "timestamp": row["day"].isoformat(),
                        "metric": metric,
                        "expected_value": round(mean, 2),
                        "actual_value": round(actual, 2),
                        "z_score": round(z, 3),
                        "severity": "high" if abs(z) >= z_threshold + 0.5 else "medium",
                    }
                )

    return {"metric": metric, "sensitivity": sensitivity, "anomalies_detected": len(anomalies), "anomalies": anomalies}
