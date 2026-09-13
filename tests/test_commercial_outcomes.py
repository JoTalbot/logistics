from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID

import pytest

import logistics.commercial_outcomes as outcomes

TENANT = UUID("11111111-1111-1111-1111-111111111111")
OPP = UUID("22222222-2222-2222-2222-222222222222")


class FakeResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeConn:
    def __init__(self):
        self.calls = []
        self.results = [
            FakeResult((OPP, "150000.00", "UAH", "30000.00")),
            FakeResult((UUID("33333333-3333-3333-3333-333333333333"), datetime(2026, 9, 12, tzinfo=timezone.utc))),
        ]

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self.results.pop(0)


def test_realized_margin_is_deterministic():
    assert outcomes.realized_margin(Decimal("150000"), Decimal("120000")) == Decimal("30000.00")
    assert outcomes.realized_margin(None, Decimal("120000")) is None


def test_outcome_validation_normalizes_money_and_text():
    value = outcomes.validate_commercial_outcome(
        outcomes.CommercialOutcome(OPP, "won", " uah ", " op-1 ", " completed ", actual_revenue="150000", actual_cost="120000")
    )
    assert value.currency == "UAH"
    assert value.operator_ref == "op-1"
    assert value.actual_revenue == Decimal("150000.00")
    assert value.actual_cost == Decimal("120000.00")


def test_outcome_validation_rejects_invalid_data():
    with pytest.raises(ValueError):
        outcomes.validate_commercial_outcome(outcomes.CommercialOutcome(OPP, "bad", "UAH", "op", "reason"))
    with pytest.raises(ValueError):
        outcomes.validate_commercial_outcome(outcomes.CommercialOutcome(OPP, "won", "UAH", "", "reason"))
    with pytest.raises(ValueError):
        outcomes.validate_commercial_outcome(outcomes.CommercialOutcome(OPP, "won", "UAH", "op", "reason", actual_cost="-1"))


def test_record_outcome_is_tenant_scoped_and_returns_prediction_error():
    conn = FakeConn()
    result = outcomes.record_commercial_outcome(
        conn,
        tenant_id=TENANT,
        outcome=outcomes.CommercialOutcome(OPP, "won", "UAH", "operator-1", "delivered", actual_revenue="150000", actual_cost="120000"),
    )
    assert conn.calls[0][1] == (TENANT, OPP)
    assert "o.tenant_id=%s" in conn.calls[0][0]
    assert result["actual_margin"] == "30000.00"
    assert result["predicted_margin"] == "30000.00"
    assert result["prediction_error"] == "0.00"


def test_outcome_history_limit_is_bounded():
    with pytest.raises(ValueError):
        outcomes.list_commercial_outcomes(object(), tenant_id=TENANT, opportunity_id=OPP, limit=0)
    with pytest.raises(ValueError):
        outcomes.prediction_actual_report(object(), tenant_id=TENANT, limit=1001)


def test_routes_are_registered():
    import logistics.commercial_outcomes_api as api_module
    routes = {route.path for route in api_module.app.routes if hasattr(route, "methods")}
    assert "/api/v1/review/opportunities/outcome" in routes
    assert "/api/v1/review/commercial-outcomes/metrics" in routes
    assert "/api/v1/review/commercial-outcomes/prediction-vs-actual" in routes
