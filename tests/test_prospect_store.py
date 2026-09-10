from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from logistics.customer_discovery import DiscoverySource, Prospect, QualificationResult
from logistics.prospect_store import list_prospects, upsert_prospect


def prospect(*, permitted=True):
    return Prospect(
        organization_name="Example Logistics",
        country="UA",
        city="Kropyvnytskyi",
        website="https://example.com",
        contact="ops@example.com",
        signal="recurring outbound freight",
        source=DiscoverySource(
            source="public_business_catalog",
            url="https://example.com/public",
            captured_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            permitted=permitted,
        ),
    )


def test_upsert_rejects_unpermitted_prospect():
    with pytest.raises(PermissionError):
        upsert_prospect(MagicMock(), tenant_id=uuid4(), prospect=prospect(permitted=False))


def test_upsert_persists_qualified_status_and_returns_id():
    prospect_id = uuid4()
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (prospect_id,)
    qualification = QualificationResult(0.85, "A", ("lane_fit", "economic_fit"))

    result = upsert_prospect(conn, tenant_id=uuid4(), prospect=prospect(), qualification=qualification)

    assert result == prospect_id
    args = conn.execute.call_args.args
    assert "customer_prospects" in args[0]
    assert "qualified" in args[0]
    assert args[1][11] is False
    assert args[1][12] == 0.85
    assert args[1][13] == "A"


def test_upsert_suppression_forces_suppressed_status():
    prospect_id = uuid4()
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (prospect_id,)

    upsert_prospect(conn, tenant_id=uuid4(), prospect=prospect(), suppressed=True)

    query, params = conn.execute.call_args.args
    assert "suppressed" in query
    assert params[11] is True
    assert params[15] == "suppressed"


def test_list_prospects_enforces_limit():
    with pytest.raises(ValueError):
        list_prospects(MagicMock(), tenant_id=uuid4(), limit=0)
