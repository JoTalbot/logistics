from uuid import UUID


def test_review_extensions_registers_commercial_outcome_routes(monkeypatch):
    import backend.logistics.review_extensions as review_extensions

    paths = {route.path for route in review_extensions.app.routes}
    assert "/api/v1/review/opportunities/outcome" in paths
    assert "/api/v1/review/commercial-outcomes/metrics" in paths
    assert "/api/v1/review/opportunities/{opportunity_id}/outcomes" in paths


def test_outcome_request_types_are_uuid_and_decimal():
    from backend.logistics.commercial_outcomes_api import CommercialOutcomeRequest
    from decimal import Decimal

    request = CommercialOutcomeRequest(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        opportunity_id=UUID("00000000-0000-0000-0000-000000000002"),
        outcome="won", operator_ref="op-1", reason="delivered",
        actual_revenue=Decimal("1000"), actual_cost=Decimal("700"), currency="UAH",
    )
    assert request.actual_revenue == Decimal("1000")
