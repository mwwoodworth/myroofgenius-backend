"""
Analytics API Module - Task 100
Unified analytics API for all data needs (no mock/sample responses).
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics API"])

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception  # type: ignore


_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
ALLOWED_TABLES = {value.strip().lower() for value in os.getenv("ANALYTICS_ALLOWED_TABLES", "").split(",") if value.strip()}
ALLOWED_COLUMNS = {value.strip().lower() for value in os.getenv("ANALYTICS_ALLOWED_COLUMNS", "").split(",") if value.strip()}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return value
    return value


def _normalize_row(row: asyncpg.Record) -> Dict[str, Any]:
    return {key: _normalize_value(row[key]) for key in row.keys()}


def _validate_identifier(value: str, label: str) -> str:
    if not value or not _IDENTIFIER_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value


def _quote_identifier(value: str) -> str:
    value = _validate_identifier(value, "identifier")
    return f"\"{value}\""


async def _table_exists(conn: asyncpg.Connection, table: str) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = $1
            )
            """,
            table,
        )
    )


async def _get_table_columns(conn: asyncpg.Connection, table: str) -> Sequence[str]:
    if ALLOWED_TABLES and table.lower() not in ALLOWED_TABLES:
        raise HTTPException(status_code=403, detail="Dataset not allowed")
    if not await _table_exists(conn, table):
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {table}")
    rows = await conn.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = $1
        """,
        table,
    )
    columns = [row["column_name"] for row in rows]
    if "tenant_id" not in columns:
        raise HTTPException(status_code=403, detail="Dataset missing tenant_id")
    if not ALLOWED_COLUMNS:
        return columns
    filtered = [col for col in columns if col.lower() in ALLOWED_COLUMNS or col.lower() == "tenant_id"]
    if not filtered:
        raise HTTPException(status_code=403, detail="No allowed columns for dataset")
    return filtered


def _metric_expression(metric: str, columns: Sequence[str]) -> Tuple[str, str]:
    metric = (metric or "").strip().lower()
    if metric == "count":
        return "COUNT(*)", "count"

    def require_column(col: str) -> str:
        col = _validate_identifier(col, "metric column")
        if col not in columns:
            raise HTTPException(status_code=400, detail=f"Unknown metric column: {col}")
        return col

    for prefix, sql_func, alias_prefix in (
        ("sum:", "SUM", "sum"),
        ("avg:", "AVG", "avg"),
        ("min:", "MIN", "min"),
        ("max:", "MAX", "max"),
    ):
        if metric.startswith(prefix):
            col = require_column(metric[len(prefix) :])
            return f"{sql_func}({_quote_identifier(col)})", f"{alias_prefix}_{col}"

    raise HTTPException(status_code=400, detail="Unsupported metric")


def _build_where_clause(
    filters: Dict[str, Any],
    columns: Sequence[str],
    date_range: Dict[str, str],
    tenant_id: Optional[str] = None,
) -> Tuple[str, List[Any]]:
    clauses: List[str] = []
    params: List[Any] = []

    # SECURITY: Always apply tenant isolation first if tenant_id column exists
    if tenant_id and "tenant_id" in columns:
        params.append(tenant_id)
        clauses.append(f"{_quote_identifier('tenant_id')} = ${len(params)}")

    for key, value in filters.items():
        column = _validate_identifier(key, "filter")
        if column not in columns:
            raise HTTPException(status_code=400, detail=f"Unknown filter column: {column}")
        params.append(value)
        clauses.append(f"{_quote_identifier(column)} = ${len(params)}")

    start = date_range.get("start") or date_range.get("from")
    end = date_range.get("end") or date_range.get("to")
    if start and end and "created_at" in columns:
        params.extend([start, end])
        created_at = _quote_identifier("created_at")
        clauses.append(f"{created_at} >= ${len(params) - 1}::timestamptz")
        clauses.append(f"{created_at} <= ${len(params)}::timestamptz")

    return (f" WHERE {' AND '.join(clauses)}" if clauses else ""), params


async def get_db(request: Request):
    """Yield an asyncpg connection from the shared pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    async with pool.acquire() as conn:
        yield conn


class QueryRequest(BaseModel):
    query_type: str  # aggregate, timeseries
    dataset: str
    filters: Optional[Dict[str, Any]] = {}
    group_by: Optional[List[str]] = []
    metrics: Optional[List[str]] = []
    date_range: Optional[Dict[str, str]] = {}
    limit: Optional[int] = 1000


@router.post("/query")
async def execute_analytics_query(
    request: QueryRequest,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    start = time.perf_counter()

    if request.query_type == "aggregate":
        result = await execute_aggregate(request, conn, tenant_id)
    elif request.query_type == "timeseries":
        result = await execute_timeseries(request, conn, tenant_id)
    elif request.query_type == "funnel":
        result = await execute_funnel(request, conn, tenant_id)
    else:
        raise HTTPException(status_code=400, detail="Unsupported query_type")

    execution_ms = int((time.perf_counter() - start) * 1000)
    return {
        "query_id": str(uuid.uuid4())[:8],
        "query_type": request.query_type,
        "dataset": request.dataset,
        "rows_returned": len(result) if isinstance(result, list) else 1,
        "data": result,
        "cached": False,
        "execution_time_ms": execution_ms,
    }


@router.get("/datasets")
async def list_datasets(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    tables = await conn.fetch(
        """
        SELECT DISTINCT t.tablename
        FROM pg_tables t
        JOIN information_schema.columns c
          ON c.table_schema = 'public'
         AND c.table_name = t.tablename
         AND c.column_name = 'tenant_id'
        WHERE t.schemaname = 'public'
        ORDER BY t.tablename
        """
    )

    table_names = [row["tablename"] for row in tables]
    if ALLOWED_TABLES:
        table_names = [table for table in table_names if table.lower() in ALLOWED_TABLES]

    if not table_names:
        return {"datasets": [], "total": 0}

    column_counts = {
        row["table_name"]: int(row["column_count"])
        for row in await conn.fetch(
            """
            SELECT table_name, COUNT(*) AS column_count
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ANY($1)
            GROUP BY table_name
            """,
            table_names,
        )
    }

    table_stats = {
        row["table_name"]: {
            "row_estimate": int(row["row_estimate"] or 0),
            "last_updated": (row["last_analyze"] or row["last_autoanalyze"]),
        }
        for row in await conn.fetch(
            """
            SELECT
                relname AS table_name,
                n_live_tup AS row_estimate,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE relname = ANY($1)
            """,
            table_names,
        )
    }

    datasets = []
    for table_name in table_names:
        stats = table_stats.get(table_name, {})
        last_updated = stats.get("last_updated")
        datasets.append(
            {
                "id": table_name,
                "name": table_name,
                "description": None,
                "row_count_estimate": stats.get("row_estimate"),
                "columns": column_counts.get(table_name),
                "last_updated": last_updated.isoformat() if hasattr(last_updated, "isoformat") else None,
            }
        )

    return {"datasets": datasets, "total": len(datasets)}


@router.get("/metrics/catalog")
async def get_metrics_catalog(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    return {
        "revenue_metrics": [
            {"id": "mrr", "name": "Monthly Recurring Revenue", "type": "currency"},
            {"id": "arr", "name": "Annual Recurring Revenue", "type": "currency"},
            {"id": "arpu", "name": "Average Revenue Per User", "type": "currency"},
        ],
        "customer_metrics": [
            {"id": "cac", "name": "Customer Acquisition Cost", "type": "currency"},
            {"id": "ltv", "name": "Customer Lifetime Value", "type": "currency"},
            {"id": "churn_rate", "name": "Churn Rate", "type": "percentage"},
        ],
        "operational_metrics": [
            {"id": "efficiency", "name": "Operational Efficiency", "type": "percentage"},
            {"id": "utilization", "name": "Resource Utilization", "type": "percentage"},
            {"id": "throughput", "name": "System Throughput", "type": "number"},
        ],
    }


@router.post("/export")
async def export_data(
    format: str = "csv",
    query: Optional[str] = None,
    dataset: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")
    format = (format or "csv").lower()
    rows: List[Dict[str, Any]]

    if query:
        try:
            payload = json.loads(query)
            request = QueryRequest(**payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid query payload: {exc}") from exc

        if request.query_type == "aggregate":
            rows = await execute_aggregate(request, conn, tenant_id)
        elif request.query_type == "timeseries":
            rows = await execute_timeseries(request, conn, tenant_id)
        elif request.query_type == "funnel":
            rows = await execute_funnel(request, conn, tenant_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported query_type for export")
    else:
        if not dataset:
            raise HTTPException(status_code=400, detail="dataset is required for export")
        table = _validate_identifier(dataset, "dataset")
        columns = await _get_table_columns(conn, table)
        where_sql, params = _build_where_clause({}, columns, {}, tenant_id)
        table_quoted = _quote_identifier(table)
        select_columns = [_quote_identifier(col) for col in columns]
        sql = f"SELECT {', '.join(select_columns)} FROM {table_quoted}{where_sql} LIMIT ${len(params) + 1}"
        params.append(10000)
        records = await conn.fetch(sql, *params)
        rows = [_normalize_row(row) for row in records]

    if format == "json":
        return {"rows": rows, "row_count": len(rows)}
    if format != "csv":
        raise HTTPException(status_code=400, detail="Unsupported export format")

    if not rows:
        return Response(content="", media_type="text/csv")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return Response(content=output.getvalue(), media_type="text/csv")


@router.get("/insights/automated")
async def get_automated_insights(
    focus_area: Optional[str] = Query(None),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI service not available on this server")

    metrics: Dict[str, Any] = {}

    if await _table_exists(conn, "invoices"):
        try:
            metrics["revenue_last_30_days"] = _normalize_value(
                await conn.fetchval(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, amount, 0)), 0)
                    FROM invoices
                    WHERE tenant_id = $1
                      AND (status = 'paid' OR LOWER(COALESCE(payment_status, '')) = 'paid')
                      AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """,
                    tenant_id,
                )
            )
            metrics["revenue_prior_30_days"] = _normalize_value(
                await conn.fetchval(
                    """
                    SELECT COALESCE(SUM(COALESCE(total_amount, amount, 0)), 0)
                    FROM invoices
                    WHERE tenant_id = $1
                      AND (status = 'paid' OR LOWER(COALESCE(payment_status, '')) = 'paid')
                      AND created_at >= CURRENT_DATE - INTERVAL '60 days'
                      AND created_at < CURRENT_DATE - INTERVAL '30 days'
                    """,
                    tenant_id,
                )
            )
        except Exception:
            metrics["revenue_last_30_days"] = None
            metrics["revenue_prior_30_days"] = None

    if await _table_exists(conn, "tickets"):
        try:
            metrics["tickets_last_24_hours"] = int(
                await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM tickets
                    WHERE tenant_id = $1
                      AND created_at >= NOW() - INTERVAL '24 hours'
                    """,
                    tenant_id,
                )
            )
            metrics["tickets_prior_24_hours"] = int(
                await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM tickets
                    WHERE tenant_id = $1
                      AND created_at >= NOW() - INTERVAL '48 hours'
                      AND created_at < NOW() - INTERVAL '24 hours'
                    """,
                    tenant_id,
                )
            )
        except Exception:
            metrics["tickets_last_24_hours"] = None
            metrics["tickets_prior_24_hours"] = None

    prompt = (
        "You are an analytics assistant for a roofing ERP/SaaS.\n\n"
        f"Metrics (JSON): {json.dumps(metrics)}\n\n"
        "Return JSON with key 'insights' as a list.\n"
        "Each insight must include: type (trend|anomaly|opportunity), severity (info|warning|success), "
        "title, description, impact, recommendations (list).\n"
        "Rules:\n"
        "- Do NOT invent numeric values not present in the metrics.\n"
        "- If metrics are insufficient, return {\"insights\": []}.\n"
    )

    try:
        result = await ai_service.generate_json(prompt)
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    insights = result.get("insights") if isinstance(result, dict) else None
    if not isinstance(insights, list):
        insights = []

    if focus_area:
        focus = focus_area.lower()
        insights = [i for i in insights if focus in json.dumps(i).lower()]

    now = datetime.now(timezone.utc)
    return {
        "generated_at": now.isoformat(),
        "total_insights": len(insights),
        "insights": insights,
        "ai_provider": result.get("ai_provider") if isinstance(result, dict) else None,
        "next_refresh": (now + timedelta(hours=1)).isoformat(),
    }


async def execute_aggregate(request: QueryRequest, conn: asyncpg.Connection, tenant_id: str) -> List[Dict[str, Any]]:
    table = _validate_identifier(request.dataset, "dataset")
    columns = await _get_table_columns(conn, table)

    group_by = []
    for col in request.group_by or []:
        col = _validate_identifier(col, "group_by")
        if col not in columns:
            raise HTTPException(status_code=400, detail=f"Unknown group_by column: {col}")
        group_by.append(col)

    metrics = request.metrics or ["count"]
    metric_exprs = []
    for metric in metrics:
        expr, alias = _metric_expression(metric, columns)
        metric_exprs.append(f"{expr} AS {alias}")

    if not metric_exprs:
        metric_exprs = ["COUNT(*) AS count"]

    # SECURITY: Pass tenant_id to _build_where_clause for tenant isolation
    where_sql, params = _build_where_clause(request.filters or {}, columns, request.date_range or {}, tenant_id)
    table_quoted = _quote_identifier(table)
    group_by_quoted = [_quote_identifier(col) for col in group_by]
    select_cols = group_by_quoted + metric_exprs
    sql = f"SELECT {', '.join(select_cols)} FROM {table_quoted}{where_sql}"
    if group_by:
        sql += f" GROUP BY {', '.join(group_by_quoted)}"
    sql += f" LIMIT ${len(params) + 1}"
    params.append(int(request.limit or 1000))

    rows = await conn.fetch(sql, *params)
    return [_normalize_row(row) for row in rows]


async def execute_timeseries(request: QueryRequest, conn: asyncpg.Connection, tenant_id: str) -> List[Dict[str, Any]]:
    table = _validate_identifier(request.dataset, "dataset")
    columns = await _get_table_columns(conn, table)
    if "created_at" not in columns:
        raise HTTPException(status_code=400, detail="Timeseries requires a created_at column")

    metric = (request.metrics or ["count"])[0]
    expr, alias = _metric_expression(metric, columns)

    # SECURITY: Pass tenant_id to _build_where_clause for tenant isolation
    where_sql, params = _build_where_clause(request.filters or {}, columns, request.date_range or {}, tenant_id)
    table_quoted = _quote_identifier(table)
    created_at = _quote_identifier("created_at")
    sql = (
        f"""
        SELECT DATE_TRUNC('day', {created_at}) AS bucket, {expr} AS {alias}
        FROM {table_quoted}{where_sql}
        GROUP BY bucket
        ORDER BY bucket
        LIMIT ${len(params) + 1}
        """.strip()
    )
    params.append(int(request.limit or 1000))

    rows = await conn.fetch(sql, *params)
    series: List[Dict[str, Any]] = []
    for row in rows:
        bucket = row["bucket"]
        series.append(
            {
                "date": bucket.isoformat() if hasattr(bucket, "isoformat") else bucket,
                "value": _normalize_value(row[alias]),
            }
        )
    return series


async def execute_funnel(request: QueryRequest, conn: asyncpg.Connection, tenant_id: str) -> List[Dict[str, Any]]:
    table = _validate_identifier(request.dataset, "dataset")
    columns = await _get_table_columns(conn, table)
    if not request.group_by:
        raise HTTPException(status_code=400, detail="Funnel requires group_by for stage column")

    stage_column = _validate_identifier(request.group_by[0], "group_by")
    if stage_column not in columns:
        raise HTTPException(status_code=400, detail=f"Unknown funnel stage column: {stage_column}")

    where_sql, params = _build_where_clause(request.filters or {}, columns, request.date_range or {}, tenant_id)
    table_quoted = _quote_identifier(table)
    stage_column_quoted = _quote_identifier(stage_column)
    sql = (
        f"""
        SELECT {stage_column_quoted} AS stage, COUNT(*) AS count
        FROM {table_quoted}{where_sql}
        GROUP BY {stage_column_quoted}
        ORDER BY {stage_column_quoted}
        LIMIT ${len(params) + 1}
        """.strip()
    )
    params.append(int(request.limit or 1000))

    rows = await conn.fetch(sql, *params)
    return [{"stage": row["stage"], "count": int(row["count"])} for row in rows]
