import importlib
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class DummyExec:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class DummyDB:
    def __init__(self, rows):
        self._rows = rows
        self._index = 0

    def execute(self, *_args, **_kwargs):
        if self._index >= len(self._rows):
            raise RuntimeError("No more rows configured")
        row = self._rows[self._index]
        self._index += 1
        if isinstance(row, Exception):
            raise row
        return DummyExec(row)


@pytest.mark.asyncio
async def test_revenue_metrics_computation(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    revenue_module = importlib.import_module("routers.revenue_automation")
    importlib.reload(revenue_module)

    payments_row = SimpleNamespace(
        today=100,
        month=1000,
        year=5000,
        total_revenue=10000,
        month_count=4,
        unique_customers=2,
    )
    prev_month_row = SimpleNamespace(prev_month=800)
    subs_row = SimpleNamespace(active=3, cancelled_total=1, cancelled_recent=1, mrr=300)
    leads_row = SimpleNamespace(total=10, converted=2)

    db = DummyDB([payments_row, prev_month_row, subs_row, leads_row])
    result = await revenue_module.get_revenue_metrics(db=db)

    assert result.today == 100.0
    assert result.month == 1000.0
    assert result.mrr == 300.0
    assert result.arr == 3600.0
    assert result.conversionRate == 20.0
    assert result.aov == 250.0
    assert result.ltv == 5000.0
    assert result.churn == 25.0


@pytest.mark.asyncio
async def test_revenue_metrics_schema_missing(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    revenue_module = importlib.import_module("routers.revenue_automation")
    importlib.reload(revenue_module)

    db = DummyDB([SQLAlchemyError("relation does not exist")])

    with pytest.raises(HTTPException) as exc:
        await revenue_module.get_revenue_metrics(db=db)

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_revenue_metrics_generic_error(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    revenue_module = importlib.import_module("routers.revenue_automation")
    importlib.reload(revenue_module)

    db = DummyDB([SQLAlchemyError("boom")])

    with pytest.raises(HTTPException) as exc:
        await revenue_module.get_revenue_metrics(db=db)

    assert exc.value.status_code == 500
