from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from logistics.api import review_metrics


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
