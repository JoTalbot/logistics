from datetime import datetime, timezone
from uuid import UUID

from logistics.autonomy_policy import ApprovalTier
from logistics.autonomy_store import (
    classify_and_save_shadow_decision,
    list_exception_decisions,
    save_shadow_decision,
)
from logistics.shadow_decisions import DecisionMode, ShadowDecision


class FakeConn:
    def __init__(self, rows=()):
        self.calls = []
        self.rows = list(rows)

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self

    def fetchall(self):
        return self.rows


def _decision(tier=ApprovalTier.REVIEW):
    return ShadowDecision(
        decision_id="d-1",
        tenant_id="11111111-1111-1111-1111-111111111111",
        action="publish_listing",
        confidence=0.82,
        tier=tier,
        mode=DecisionMode.SHADOW,
        policy_version="v21.1",
        classification_reason="REVIEW: confidence 0.8200 is within review band",
        created_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )


def test_save_is_tenant_scoped_and_idempotent_sql():
    conn = FakeConn()
    save_shadow_decision(conn, _decision(), correlation_id="corr-1")
    sql, params = conn.calls[0]
    assert "autonomy_decisions" in sql
    assert "ON CONFLICT (tenant_id, decision_id) DO NOTHING" in sql
    assert params[0] == UUID("11111111-1111-1111-1111-111111111111")
    assert params[1] == "d-1"
    assert params[2] == "corr-1"
    assert params[6] == "SHADOW"


def test_classify_and_save_connects_policy_to_durable_record():
    conn = FakeConn()
    decision = classify_and_save_shadow_decision(
        conn,
        decision_id="d-2",
        tenant_id="11111111-1111-1111-1111-111111111111",
        action="contact_customer",
        confidence=0.95,
        authorized=False,
        correlation_id="corr-2",
    )
    assert decision.tier is ApprovalTier.BLOCK
    assert decision.policy_version == "v21.1"
    assert "not authorized" in decision.classification_reason
    assert conn.calls[0][1][1] == "d-2"


def test_exception_queue_is_tenant_scoped_and_oldest_first():
    created = datetime(2026, 9, 11, tzinfo=timezone.utc)
    conn = FakeConn([
        ("d-1", "c-1", "publish_listing", 0.82, "REVIEW", "SHADOW", "v21.1", "needs review", created),
    ])
    result = list_exception_decisions(
        conn,
        tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
        limit=10,
    )
    sql, params = conn.calls[0]
    assert "tenant_id=%s" in sql
    assert "tier IN ('REVIEW','HIGH_RISK','BLOCK')" in sql
    assert "ORDER BY created_at ASC" in sql
    assert params == (UUID("11111111-1111-1111-1111-111111111111"), 10)
    assert result[0]["decision_id"] == "d-1"
    assert result[0]["tier"] == "REVIEW"


def test_exception_queue_rejects_invalid_limit():
    try:
        list_exception_decisions(FakeConn(), tenant_id=UUID(int=1), limit=0)
    except ValueError as exc:
        assert "between 1 and 500" in str(exc)
    else:
        raise AssertionError("invalid limit must fail")
