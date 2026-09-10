from unittest.mock import MagicMock, patch
from uuid import uuid4

import psycopg
import pytest

from logistics.api import readiness, review_business_kpis, review_metrics, review_priority_metrics, review_summary


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


def test_review_business_kpis_requires_operator_token(monkeypatch):
    monkeypatch.delenv("REVIEW_OPERATOR_TOKEN", raising=False)
    with pytest.raises(Exception) as exc:
        review_business_kpis(uuid4(), None)
    assert getattr(exc.value, "status_code", None) == 503


def test_review_business_kpis_returns_tenant_scoped_snapshot(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "operator-secret")
    tenant_id = uuid4()
    expected = {
        "ingestion_volume": 120,
        "opportunities_created": 20,
        "high_priority_opportunities": 5,
        "open_priority_work": 8,
        "successful_deliveries": 9,
        "failed_deliveries": 1,
        "delivery_success_rate": 0.9,
        "recurring_demand_profiles": 7,
        "fresh_recurring_demand_profiles": 4,
        "provider_errors": 1,
    }
    conn = MagicMock()
    conn.__enter__.return_value = conn
    with patch("logistics.api.psycopg.connect", return_value=conn) as connect, patch(
        "logistics.api.snapshot_kpis",
        return_value=MagicMock(**expected),
    ) as snapshot:
        result = review_business_kpis(tenant_id, x_operator_token="operator-secret")

    assert result == {"tenant_id": str(tenant_id), "kpis": expected}
    connect.assert_called_once_with("postgresql://logistics:logistics@db/logistics", connect_timeout=3)
    snapshot.assert_called_once_with(conn.execute, str(tenant_id))


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
        result = review_priority_metrics(tenant_id, x_operator_token="operator-secret")

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
        review_priority_metrics(uuid4(), high_priority_threshold=1.1, x_operator_token="operator-secret")
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
        MagicMock(fetchall=lambda: []),
        MagicMock(fetchone=lambda: (0,)),
        MagicMock(fetchone=lambda: (0,)),
    ]
    with patch("logistics.api.psycopg.connect", return_value=conn), patch(
        "logistics.api.scheduler_health",
        return_value={"operational_status": "healthy", "status": "succeeded"},
    ), patch("logistics.api.find_duplicate_load_groups", return_value=[]):
        result = review_summary(tenant_id, x_operator_token="operator-secret")

    assert result["tenant_id"] == str(tenant_id)
    assert result["operational_status"] == "healthy"
    assert result["priority_queue"]["total"] == 0
    assert result["priority_queue"]["stale_open"] == 0


def test_readiness_returns_ready_when_database_is_reachable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://logistics:logistics@db/logistics")
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.return_value.fetchone.return_value = (1,)
    with patch("logistics.api.psycopg.connect", return_value=conn) as connect:
        result = readiness()
    assert result == {"status": "ready", "service": "logistics-api"}
    connect.assert_called_once_with("postgresql://logistics:logistics@db/logistics", connect_timeout=3)
    conn.execute.assert_called_once_with("SELECT 1")


def test_readiness_returns_503_when_database_is_unreachable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://logistics:logistics@db/logistics")
    with patch("logistics.api.psycopg.connect", side_effect=psycopg.OperationalError("connection refused")):
        with pytest.raises(Exception) as exc:
            readiness()
    assert getattr(exc.value, "status_code", None) == 503


def test_readiness_returns_503_when_database_configuration_is_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(Exception) as exc:
        readiness()
    assert getattr(exc.value, "status_code", None) == 503
