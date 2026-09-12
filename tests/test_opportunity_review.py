from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from logistics.opportunity_review import OpportunityReview, apply_opportunity_review, list_opportunity_review_history, opportunity_review_metrics, validate_opportunity_review

TENANT = UUID('11111111-1111-1111-1111-111111111111')
OPP = UUID('22222222-2222-2222-2222-222222222222')

class FakeResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
    def fetchone(self): return self.row
    def fetchall(self): return self.rows

class FakeConn:
    def __init__(self):
        self.calls = []
        self.history = []
        self.status = 'candidate'
    def execute(self, sql, params):
        self.calls.append((sql, params))
        if sql.lstrip().startswith('SELECT id, priority_status'):
            return FakeResult((OPP, self.status))
        if sql.lstrip().startswith('UPDATE opportunities'):
            self.status = params[0]
            return FakeResult()
        if sql.lstrip().startswith('INSERT INTO opportunity_review_history'):
            self.history.append(params)
            return FakeResult()
        if 'SELECT priority_status, count(*)' in sql:
            return FakeResult(rows=[(self.status, 1)])
        if 'SELECT count(*), count(*) FILTER' in sql:
            return FakeResult((len(self.history), sum(x[3] == 'accepted' for x in self.history), sum(x[3] == 'rejected' for x in self.history), sum(x[3] == 'hold' for x in self.history)))
        if 'SELECT previous_status, new_status' in sql:
            now = datetime.now(timezone.utc)
            return FakeResult(rows=[(x[2], x[3], x[4], x[5], now) for x in reversed(self.history)])
        raise AssertionError(f'unexpected SQL: {sql}')

def test_validation_rejects_bad_status_and_empty_audit_fields():
    with pytest.raises(ValueError): validate_opportunity_review(OpportunityReview(OPP, 'bad', 'op', 'reason'))
    with pytest.raises(ValueError): validate_opportunity_review(OpportunityReview(OPP, 'accepted', '', 'reason'))
    with pytest.raises(ValueError): validate_opportunity_review(OpportunityReview(OPP, 'accepted', 'op', ''))

def test_apply_review_is_tenant_scoped_and_audited():
    conn = FakeConn()
    result = apply_opportunity_review(conn, tenant_id=TENANT, review=OpportunityReview(OPP, 'accepted', 'operator-1', 'margin verified'))
    assert result['previous_status'] == 'candidate'
    assert result['status'] == 'accepted'
    assert conn.history[0][0] == TENANT
    assert conn.history[0][1] == OPP
    assert conn.history[0][2] == 'candidate'
    assert conn.history[0][3] == 'accepted'
    assert conn.history[0][4:] == ('operator-1', 'margin verified')
    assert any('tenant_id=%s' in sql for sql, _ in conn.calls)

def test_review_metrics_exposes_terminal_acceptance_rate():
    conn = FakeConn()
    apply_opportunity_review(conn, tenant_id=TENANT, review=OpportunityReview(OPP, 'accepted', 'operator-1', 'won'))
    apply_opportunity_review(conn, tenant_id=TENANT, review=OpportunityReview(OPP, 'rejected', 'operator-1', 'lost'))
    metrics = opportunity_review_metrics(conn, tenant_id=TENANT)
    assert metrics['accepted_transitions'] == 1
    assert metrics['rejected_transitions'] == 1
    assert metrics['acceptance_rate_of_terminal_decisions'] == 0.5

def test_history_is_bounded_and_tenant_scoped():
    conn = FakeConn()
    apply_opportunity_review(conn, tenant_id=TENANT, review=OpportunityReview(OPP, 'hold', 'operator-1', 'waiting'))
    history = list_opportunity_review_history(conn, tenant_id=TENANT, opportunity_id=OPP, limit=10)
    assert history[0]['new_status'] == 'hold'
    with pytest.raises(ValueError): list_opportunity_review_history(conn, tenant_id=TENANT, opportunity_id=OPP, limit=0)
