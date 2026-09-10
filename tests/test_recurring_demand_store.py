from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from logistics.recurring_demand import DemandPattern
from logistics.recurring_demand_store import list_patterns, record_evidence, upsert_pattern


def pattern() -> DemandPattern:
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    return DemandPattern("UA>PL|food|eur", 4, now, now, 168.0, 1.0, 0.4, ("observations=4", "regular_intervals"))


def test_upsert_pattern_persists():
    conn = MagicMock()
    pattern_id = uuid4()
    conn.execute.return_value.fetchone.return_value = (pattern_id,)
    result = upsert_pattern(conn, tenant_id=uuid4(), pattern=pattern(), freshness=0.9)
    assert result == pattern_id
    assert "recurring_demand_patterns" in conn.execute.call_args.args[0]


def test_upsert_pattern_rejects_invalid_freshness():
    with pytest.raises(ValueError):
        upsert_pattern(MagicMock(), tenant_id=uuid4(), pattern=pattern(), freshness=1.1)


def test_evidence_is_idempotent():
    conn = MagicMock()
    record_evidence(conn, tenant_id=uuid4(), pattern_id=uuid4(), load_id=uuid4(), observed_at=datetime.now(timezone.utc))
    assert "DO NOTHING" in conn.execute.call_args.args[0]


def test_list_patterns_validates_status_and_limit():
    with pytest.raises(ValueError):
        list_patterns(MagicMock(), tenant_id=uuid4(), status="bad")
    with pytest.raises(ValueError):
        list_patterns(MagicMock(), tenant_id=uuid4(), limit=0)
