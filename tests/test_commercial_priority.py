from datetime import datetime, timezone
from uuid import uuid4

import pytest

from logistics.commercial_priority import PriorityDecision, persist_priority_decision, to_priority_decision


class FakeConn:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))


def test_priority_decision_validates_status_and_score():
    conn = FakeConn()
    decision = PriorityDecision(uuid4(), 0.8, ("positive_margin",))
    persist_priority_decision(conn, tenant_id=uuid4(), decision=decision, updated_at=datetime.now(timezone.utc))
    assert "priority_score" in conn.calls[0][0]
    assert conn.calls[0][1][0] == 0.8


def test_priority_decision_rejects_invalid_score():
    with pytest.raises(ValueError):
        persist_priority_decision(
            FakeConn(), tenant_id=uuid4(),
            decision=PriorityDecision(uuid4(), 1.1, ()),
            updated_at=datetime.now(timezone.utc),
        )


def test_priority_decision_rejects_invalid_status():
    with pytest.raises(ValueError):
        persist_priority_decision(
            FakeConn(), tenant_id=uuid4(),
            decision=PriorityDecision(uuid4(), 0.5, (), status="sent"),
            updated_at=datetime.now(timezone.utc),
        )
