from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from logistics.api import review_metrics, review_priority_metrics, review_summary


def test_review_metrics_requires_operator_token(monkeypatch):
    monkeypatch.delenv("REVIEW_OPERATOR_TOKEN", raising=False)
    with pytest.raises(Exception) as exc:
        review_metrics(uuid4(), None)
    assert getattr(exc.value, "status_code", None) == 503


def test_review_metrics_returns_operational_counts(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "operator-secret")
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.side_effect = [
        MagicMock(fetchone=lambda: (2,)),
        MagicMock(fetchone=lambda: (3,)),
        MagicMock(fetchone=lambda: (7,)),
    ]
    with patch("logistics.api.psycopg.connect", return_value=conn):
        result = review_metrics(uuid4(), "operator-secret")
    assert result == {
        "publication_pending": 2,
        "negotiation_pending": 3,
        "pending_total": 5,
        "review_decisions_total": 7,
    }


def test_review_priority_metrics_is_tenant_scoped_and_exposes_sla(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "operator-secret")
    tenant_id = uuid4()
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.side_effect = [
        MagicMock(fetchall=lambda: [
            ("candidate", 2, 7200, 3600),
            ("accepted", 1, 1800, 1800),
        ]),
        MagicMock(fetchone=lambda: (1,)),
        MagicMock(fetchone=lambda: (1,)),
    ]
    with patch("logistics.api.psycopg.connect", return_value=conn):
        result = review_priority_metrics(tenant_id, "operator-secret")

    assert result == {
        "tenant_id": str(tenant_id),
        "total": 3,
        "by_status": {"candidate": 2, "accepted": 1},
        "high_priority_open": 1,
        "stale_open": 1,
        "oldest_age_seconds": 7200,
        "average_age_seconds": 3600,
        "sla": {"stale_after_hours": 12, "high_priority_threshold": 0.8},
    }
    first_query_params = conn.execute.call_args_list[0].args[1]
    assert first_query_params == (tenant_id,)


def test_review_priority_metrics_validates_thresholds(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "operator-secret")
    with pytest.raises(Exception) as exc:
        review_priority_metrics(uuid4(), "operator-secret", high_priority_threshold=1.1)
    assert getattr(exc.value, "status_code", None) == 422


def test_review_summary_keeps_priority_metrics_tenant_scoped(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "operator-secret")
    tenant_id = uuid4()
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.side_effect = [
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchall=lambda: []),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
    ]
    with patch("logistics.api.psycopg.connect", return_value=conn), patch(
        "logistics.api.scheduler_health",
        return_value={"operational_status": "healthy", "status": "succeeded"},
    ):
        result = review_summary(tenant_id, x_operator_token="operator-secret")

    assert result["tenant_id"] == str(tenant_id)
    assert result["operational_status"] == "healthy"
    assert result["priority_queue"]["total"] == 0
    assert result["priority_queue"]["stale_open"] == 0
