from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.recurring_demand_pipeline import persist_recurring_demand


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self):
        self.pattern_id = uuid4()
        self.evidence = []
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        if "RETURNING id" in sql:
            return FakeResult((self.pattern_id,))
        if "recurring_demand_evidence" in sql:
            self.evidence.append(params)
        return FakeResult(None)


def _load(created_at):
    from logistics.domain import GeoPoint, Load
    return Load(
        id=uuid4(),
        external_ref=str(uuid4()),
        source="test",
        cargo_type="Food",
        weight_kg=Decimal("1000"),
        currency="EUR",
        stops=(
            GeoPoint(sequence=1, location="UA", country_code="UA"),
            GeoPoint(sequence=2, location="PL", country_code="PL"),
        ),
        created_at=created_at,
    )


def test_persist_recurring_demand_writes_pattern_and_evidence():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    loads = [_load(start + timedelta(days=7 * i)) for i in range(3)]
    conn = FakeConnection()

    persisted = persist_recurring_demand(
        conn,
        tenant_id=uuid4(),
        loads=loads,
        now=start + timedelta(days=7 * 2),
    )

    assert persisted == 1
    assert len(conn.evidence) == 3
    assert any("recurring_demand_patterns" in sql for sql, _ in conn.calls)
    assert any("recurring_demand_evidence" in sql for sql, _ in conn.calls)
