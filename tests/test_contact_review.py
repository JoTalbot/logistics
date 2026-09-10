from uuid import uuid4

import pytest

from logistics.contact_review import decide_contact_intent


def _conn(rows):
    class Result:
        def __init__(self, row=None): self.row = row
        def fetchone(self): return self.row
        def fetchall(self): return []

    class Conn:
        def __init__(self): self.calls = []
        def execute(self, sql, params=()):
            self.calls.append((sql, params))
            if "SELECT status" in sql:
                return Result(rows)
            return Result()
    return Conn()


def test_approve_requires_authorization():
    conn = _conn(("pending", False, False, True))
    with pytest.raises(ValueError, match="unauthorized"):
        decide_contact_intent(conn, tenant_id=uuid4(), contact_intent_id=uuid4(), action="approve", operator_ref="op", reason="reviewed")


def test_approve_rejects_suppressed():
    conn = _conn(("pending", True, True, True))
    with pytest.raises(ValueError, match="suppressed"):
        decide_contact_intent(conn, tenant_id=uuid4(), contact_intent_id=uuid4(), action="approve", operator_ref="op", reason="reviewed")


def test_approve_updates_and_audits():
    conn = _conn(("pending", True, False, True))
    tenant_id, intent_id = uuid4(), uuid4()
    result = decide_contact_intent(conn, tenant_id=tenant_id, contact_intent_id=intent_id, action="approve", operator_ref="op", reason="verified authorization")
    assert result == "approved"
    assert any("UPDATE contact_intents" in sql for sql, _ in conn.calls)
    assert any("INSERT INTO contact_intent_audit" in sql for sql, _ in conn.calls)


def test_hold_is_audited_without_send():
    conn = _conn(("pending", True, False, True))
    result = decide_contact_intent(conn, tenant_id=uuid4(), contact_intent_id=uuid4(), action="hold", operator_ref="op", reason="needs review")
    assert result == "pending"
    assert not any("sent" in sql.lower() for sql, _ in conn.calls)


def test_invalid_transition_is_rejected():
    conn = _conn(("sent", True, False, False))
    with pytest.raises(ValueError, match="current state"):
        decide_contact_intent(conn, tenant_id=uuid4(), contact_intent_id=uuid4(), action="reject", operator_ref="op", reason="too late")
