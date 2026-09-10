from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from logistics.customer_opportunities import CustomerOpportunity
from logistics.customer_opportunity_store import list_customer_opportunities, upsert_customer_opportunity


def opportunity(observed_at=None):
    return CustomerOpportunity(
        customer_id="customer-1",
        load_id="load-1",
        demand_score=0.8,
        commercial_score=0.7,
        freshness_score=0.9,
        total_score=0.81,
        reasons=("cargo_match", "fresh_signal"),
        observed_at=observed_at or datetime(2026, 9, 10, tzinfo=timezone.utc),
    )


def test_upsert_customer_opportunity_is_tenant_scoped():
    opportunity_id = uuid4()
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (opportunity_id,)

    result = upsert_customer_opportunity(conn, tenant_id=uuid4(), opportunity=opportunity())

    assert result == opportunity_id
    query, params = conn.execute.call_args.args
    assert "customer_opportunities" in query
    assert "tenant_id" in query
    assert params[1] == "customer-1"


def test_list_customer_opportunities_rejects_invalid_status():
    with pytest.raises(ValueError):
        list_customer_opportunities(MagicMock(), tenant_id=uuid4(), status="unknown")


def test_list_customer_opportunities_rejects_invalid_limit():
    with pytest.raises(ValueError):
        list_customer_opportunities(MagicMock(), tenant_id=uuid4(), limit=0)
