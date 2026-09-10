from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.recurring_demand_db import load_persisted_telegram_loads


def test_rehydrates_only_telegram_loads_and_preserves_tenant():
    tenant_id = uuid4()
    load_id = uuid4()
    created_at = datetime(2026, 9, 1, tzinfo=timezone.utc)

    class Result:
        def __init__(self, rows):
            self.rows = rows
        def fetchall(self):
            return self.rows

    class Conn:
        def __init__(self):
            self.calls = []
        def execute(self, sql, params=()):
            self.calls.append((sql, params))
            if "FROM loads" in sql:
                return Result([(load_id, "tg-1", "food", 1000, Decimal("1200.00"), "EUR", "new", created_at)])
            return Result([(load_id, 0, "pickup", "UA Kyiv", "Kyiv", None, None, 0.9, "deterministic", None, None),
                           (load_id, 1, "delivery", "PL Warsaw", "Warsaw", None, None, 0.9, "deterministic", None, None)])

    loads = load_persisted_telegram_loads(Conn(), tenant_id=tenant_id)
    assert len(loads) == 1
    assert loads[0].tenant_id == tenant_id
    assert loads[0].id == load_id
    assert loads[0].currency == "EUR"
    assert len(loads[0].stops) == 2


def test_invalid_limit_rejected():
    class Conn:
        def execute(self, *args, **kwargs):
            raise AssertionError("database must not be queried")
    import pytest
    with pytest.raises(ValueError, match="limit"):
        load_persisted_telegram_loads(Conn(), tenant_id=uuid4(), limit=0)
