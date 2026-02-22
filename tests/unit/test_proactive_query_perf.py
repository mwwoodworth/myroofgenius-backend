"""
Unit Tests - Proactive Engine Query Performance
Validates that get_opportunities and get_predictions build dynamic
WHERE clauses without the IS-NULL-OR anti-pattern that defeats indexes.
"""

import asyncio
import json
import re
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


# Regex matching the parameter-null anti-pattern: ($N::type IS NULL OR col = $N)
_PARAM_NULL_OR_RE = re.compile(r"\$\d+\S*\s+IS\s+NULL\s+OR", re.IGNORECASE)


def _has_param_null_anti_pattern(sql: str) -> bool:
    """Return True if SQL contains the ($N IS NULL OR col = $N) anti-pattern."""
    return bool(_PARAM_NULL_OR_RE.search(sql))


def _make_engine():
    """Create a ProactiveIntelligenceEngine with a mock controller."""
    from brainops_ai_os.proactive_engine import ProactiveIntelligenceEngine

    controller = MagicMock()
    engine = ProactiveIntelligenceEngine(controller)
    engine.db_pool = MagicMock()
    return engine


def _opp_row(**overrides):
    """Build a fake asyncpg-like Record for an opportunity row."""
    base = {
        "opportunity_id": "opp-1",
        "opportunity_type": "revenue",
        "title": "Test",
        "description": "desc",
        "potential_value": 100.0,
        "confidence": 0.8,
        "urgency": 0.9,
        "recommended_actions": json.dumps([]),
        "context": json.dumps({}),
        "created_at": datetime(2026, 1, 1),
        "expires_at": datetime(2026, 12, 31),
        "acted_upon": False,
    }
    base.update(overrides)
    # asyncpg Records support dict-style access; a plain dict works for tests.
    return base


def _pred_row(**overrides):
    """Build a fake asyncpg-like Record for a prediction row."""
    base = {
        "prediction_id": "pred-1",
        "prediction_type": "churn",
        "target": "customer:123",
        "probability": 0.7,
        "timeframe": "30 days",
        "impact": 500.0,
        "preventive_actions": json.dumps([]),
        "verified": None,
        "created_at": datetime(2026, 1, 1),
        "verified_at": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Opportunity query tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_no_type_omits_type_predicate():
    """When opportunity_type is None, SQL must NOT contain IS NULL OR."""
    engine = _make_engine()
    captured_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        return [_opp_row()]

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities(opportunity_type=None, min_score=0.5, limit=10)

    assert len(captured_queries) == 1
    sql = captured_queries[0]
    assert not _has_param_null_anti_pattern(
        sql
    ), "Dynamic query must not use parameter-IS-NULL-OR pattern"
    where_clause = sql.split("WHERE")[1].split("ORDER BY")[0]
    assert (
        "opportunity_type" not in where_clause
    ), "Should omit type predicate when None"
    assert "acted_upon IS NOT TRUE" in sql
    assert "NULLS LAST" in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_with_type_includes_exact_predicate():
    """When opportunity_type is provided, SQL must include an exact equality predicate."""
    engine = _make_engine()
    captured_queries: list[str] = []
    captured_args: list[tuple] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        captured_args.append(args)
        return [_opp_row()]

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities(opportunity_type="revenue", min_score=0.6, limit=5)

    sql = captured_queries[0]
    assert "opportunity_type = $1" in sql
    assert not _has_param_null_anti_pattern(sql)
    assert captured_args[0][0] == "revenue"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_min_score_filter():
    """min_score filter is always present and uses correct parameter."""
    engine = _make_engine()
    captured_args: list[tuple] = []

    async def _capture(query, *args, **kwargs):
        captured_args.append(args)
        return []

    engine._db_fetch_with_retry = _capture

    # Without type: min_score should be $1
    await engine.get_opportunities(opportunity_type=None, min_score=0.7)
    assert captured_args[0][0] == 0.7

    # With type: min_score should be $2
    await engine.get_opportunities(opportunity_type="risk", min_score=0.3)
    assert captured_args[1][1] == 0.3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_acted_upon_filter():
    """acted_upon filter uses IS NOT TRUE (not COALESCE wrapper)."""
    engine = _make_engine()
    captured_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        return []

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities()

    sql = captured_queries[0]
    assert "acted_upon IS NOT TRUE" in sql
    assert "COALESCE(acted_upon" not in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_expires_filter_preserved():
    """The expires_at IS NULL OR expires_at > NOW() filter remains."""
    engine = _make_engine()
    captured_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        return []

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities()

    sql = captured_queries[0]
    assert "expires_at IS NULL OR expires_at > NOW()" in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_order_no_coalesce():
    """ORDER BY must use NULLS LAST instead of COALESCE wrappers."""
    engine = _make_engine()
    captured_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        return []

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities()

    sql = captured_queries[0]
    assert "COALESCE(urgency" not in sql
    assert "COALESCE(confidence" not in sql.split("ORDER BY")[1]
    assert "urgency DESC NULLS LAST" in sql
    assert "confidence DESC NULLS LAST" in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_limit_bounds():
    """Limit is clamped to [1, 100]."""
    engine = _make_engine()
    captured_args: list[tuple] = []

    async def _capture(query, *args, **kwargs):
        captured_args.append(args)
        return []

    engine._db_fetch_with_retry = _capture

    await engine.get_opportunities(limit=0)
    assert captured_args[0][-1] == 1  # clamped from 0 to 1

    await engine.get_opportunities(limit=999)
    assert captured_args[1][-1] == 100  # clamped from 999 to 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_opportunities_fallback_on_db_error():
    """On DB error, falls back to in-memory cache."""
    engine = _make_engine()

    async def _fail(query, *args, **kwargs):
        raise Exception("connection refused")

    engine._db_fetch_with_retry = _fail

    # Should not raise — returns cached (empty) list
    result = await engine.get_opportunities()
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Prediction query tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_predictions_no_type_omits_where():
    """When prediction_type is None, SQL has no WHERE clause."""
    engine = _make_engine()
    captured_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        return [_pred_row()]

    engine._db_fetch_with_retry = _capture

    await engine.get_predictions(prediction_type=None)

    sql = captured_queries[0]
    assert not _has_param_null_anti_pattern(sql)
    assert "WHERE" not in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_predictions_with_type_includes_exact_predicate():
    """When prediction_type is provided, SQL must include exact equality."""
    engine = _make_engine()
    captured_queries: list[str] = []
    captured_args: list[tuple] = []

    async def _capture(query, *args, **kwargs):
        captured_queries.append(query)
        captured_args.append(args)
        return [_pred_row()]

    engine._db_fetch_with_retry = _capture

    await engine.get_predictions(prediction_type="churn")

    sql = captured_queries[0]
    assert "prediction_type = $1" in sql
    assert not _has_param_null_anti_pattern(sql)
    assert captured_args[0][0] == "churn"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_is_null_or_pattern_anywhere():
    """Comprehensive check: no parameter-IS-NULL-OR anti-pattern in any SQL."""
    engine = _make_engine()
    all_queries: list[str] = []

    async def _capture(query, *args, **kwargs):
        all_queries.append(query)
        return []

    engine._db_fetch_with_retry = _capture

    # Exercise all combinations
    await engine.get_opportunities(opportunity_type=None)
    await engine.get_opportunities(opportunity_type="revenue")
    await engine.get_predictions(prediction_type=None)
    await engine.get_predictions(prediction_type="churn")

    for sql in all_queries:
        assert not _has_param_null_anti_pattern(
            sql
        ), f"Parameter-null anti-pattern found in: {sql[:120]}"
