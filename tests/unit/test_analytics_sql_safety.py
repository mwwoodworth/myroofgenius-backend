import pytest
from fastapi import HTTPException

from routes import analytics_api


def test_quote_identifier_valid():
    assert analytics_api._quote_identifier("created_at") == '"created_at"'


def test_quote_identifier_rejects_invalid():
    with pytest.raises(HTTPException):
        analytics_api._quote_identifier("bad;drop")


def test_metric_expression_quotes_columns():
    expr, alias = analytics_api._metric_expression("sum:amount", ["amount"])
    assert expr == 'SUM("amount")'
    assert alias == "sum_amount"


def test_build_where_clause_quotes_identifiers():
    clause, params = analytics_api._build_where_clause(
        {"status": "open"},
        ["tenant_id", "status", "created_at"],
        {"start": "2024-01-01", "end": "2024-01-02"},
        "tenant-123",
    )
    assert '"tenant_id"' in clause
    assert '"status"' in clause
    assert '"created_at"' in clause
    assert params == ["tenant-123", "open", "2024-01-01", "2024-01-02"]


def test_require_allowlists_in_production_requires_both_lists():
    with pytest.raises(HTTPException):
        analytics_api._require_allowlists(set(), set(), environment="production")

    with pytest.raises(HTTPException):
        analytics_api._require_allowlists({"analytics_events"}, set(), environment="production")

    with pytest.raises(HTTPException):
        analytics_api._require_allowlists(set(), {"tenant_id"}, environment="production")


def test_require_allowlists_allows_non_production():
    analytics_api._require_allowlists(set(), set(), environment="development")
