from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


ALLOWED_OUTCOMES = {"won", "lost", "cancelled", "unknown"}


@dataclass(frozen=True)
class CommercialOutcome:
    opportunity_id: UUID
    outcome: str
    operator_ref: str
    reason: str
    offered_price: Decimal | None = None
    actual_revenue: Decimal | None = None
    actual_cost: Decimal | None = None
    currency: str | None = None


def realized_margin(actual_revenue: Decimal | None, actual_cost: Decimal | None) -> Decimal | None:
    if actual_revenue is None or actual_cost is None:
        return None
    return actual_revenue - actual_cost


def validate_commercial_outcome(outcome: CommercialOutcome) -> CommercialOutcome:
    if outcome.outcome not in ALLOWED_OUTCOMES:
        raise ValueError("invalid commercial outcome")
    if not outcome.operator_ref.strip():
        raise ValueError("operator_ref is required")
    if not outcome.reason.strip():
        raise ValueError("reason is required")
    for value, name in ((outcome.offered_price, "offered_price"), (outcome.actual_revenue, "actual_revenue"), (outcome.actual_cost, "actual_cost")):
        if value is not None and value < 0:
            raise ValueError(f"{name} must be non-negative")
    if outcome.outcome == "won" and outcome.actual_revenue is None:
        raise ValueError("won outcome requires actual_revenue")
    if outcome.actual_revenue is not None and outcome.currency is None:
        raise ValueError("currency is required when actual_revenue is provided")
    return outcome


def record_commercial_outcome(conn: object, *, tenant_id: UUID, outcome: CommercialOutcome) -> dict[str, object]:
    validate_commercial_outcome(outcome)
    margin = realized_margin(outcome.actual_revenue, outcome.actual_cost)
    row = conn.execute(
        """
        SELECT id, score, estimated_margin, risk_adjusted_margin, offered_price, currency
          FROM opportunities o
          JOIN loads l ON l.id=o.load_id AND l.tenant_id=o.tenant_id
         WHERE o.tenant_id=%s AND o.id=%s
         FOR UPDATE
        """,
        (tenant_id, outcome.opportunity_id),
    ).fetchone()
    if row is None:
        raise ValueError("opportunity not found")
    previous = conn.execute(
        """SELECT outcome FROM commercial_outcomes WHERE tenant_id=%s AND opportunity_id=%s""",
        (tenant_id, outcome.opportunity_id),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO commercial_outcomes
          (tenant_id, opportunity_id, outcome, offered_price, actual_revenue, actual_cost,
           actual_margin, currency, operator_ref, reason)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant_id, opportunity_id) DO UPDATE SET
          outcome=EXCLUDED.outcome, offered_price=EXCLUDED.offered_price,
          actual_revenue=EXCLUDED.actual_revenue, actual_cost=EXCLUDED.actual_cost,
          actual_margin=EXCLUDED.actual_margin, currency=EXCLUDED.currency,
          operator_ref=EXCLUDED.operator_ref, reason=EXCLUDED.reason,
          outcome_at=now()
        """,
        (tenant_id, outcome.opportunity_id, outcome.outcome,
         outcome.offered_price if outcome.offered_price is not None else row[4],
         outcome.actual_revenue, outcome.actual_cost, margin,
         outcome.currency if outcome.currency is not None else row[5],
         outcome.operator_ref, outcome.reason),
    )
    conn.execute(
        """
        INSERT INTO commercial_outcome_history
          (tenant_id, opportunity_id, previous_outcome, new_outcome, offered_price,
           actual_revenue, actual_cost, actual_margin, currency, operator_ref, reason, outcome_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
        """,
        (tenant_id, outcome.opportunity_id, previous[0] if previous else None,
         outcome.outcome, outcome.offered_price if outcome.offered_price is not None else row[4],
         outcome.actual_revenue, outcome.actual_cost, margin,
         outcome.currency if outcome.currency is not None else row[5], outcome.operator_ref, outcome.reason),
    )
    return {
        "opportunity_id": str(row[0]),
        "outcome": outcome.outcome,
        "predicted_margin": str(row[2]),
        "predicted_risk_adjusted_margin": str(row[3]),
        "actual_margin": str(margin) if margin is not None else None,
        "margin_error": str(margin - row[2]) if margin is not None and row[2] is not None else None,
        "previous_outcome": previous[0] if previous else None,
    }


def commercial_conversion_metrics(conn: object, *, tenant_id: UUID) -> dict[str, object]:
    status_rows = conn.execute(
        """
        SELECT priority_status, count(*) FROM opportunities
         WHERE tenant_id=%s AND priority_score IS NOT NULL
         GROUP BY priority_status ORDER BY priority_status
        """,
        (tenant_id,),
    ).fetchall()
    outcome = conn.execute(
        """
        SELECT count(*), count(*) FILTER (WHERE outcome='won'),
               count(*) FILTER (WHERE outcome='lost'),
               count(*) FILTER (WHERE outcome='cancelled'),
               coalesce(sum(actual_revenue),0), coalesce(sum(actual_margin),0),
               coalesce(avg(actual_margin),0)
          FROM commercial_outcomes WHERE tenant_id=%s
        """,
        (tenant_id,),
    ).fetchone()
    prediction = conn.execute(
        """
        SELECT count(*), coalesce(avg(c.actual_margin - o.estimated_margin),0),
               coalesce(avg(abs(c.actual_margin - o.estimated_margin)),0)
          FROM commercial_outcomes c
          JOIN opportunities o ON o.id=c.opportunity_id AND o.tenant_id=c.tenant_id
         WHERE c.tenant_id=%s AND c.actual_margin IS NOT NULL AND o.estimated_margin IS NOT NULL
        """,
        (tenant_id,),
    ).fetchone()
    total, won, lost, cancelled, revenue, margin, avg_margin = map(lambda x: int(x) if isinstance(x, int) else x, outcome)
    terminal = won + lost
    status = {row[0]: int(row[1]) for row in status_rows}
    return {
        "by_priority_status": status,
        "outcomes": {"total": total, "won": won, "lost": lost, "cancelled": cancelled},
        "accepted_to_won_rate": round(won / terminal, 4) if terminal else 0.0,
        "realized_revenue": str(revenue),
        "realized_margin": str(margin),
        "average_realized_margin": str(avg_margin),
        "prediction": {
            "cases": int(prediction[0]),
            "mean_margin_error": str(prediction[1]),
            "mean_absolute_margin_error": str(prediction[2]),
        },
    }


def list_commercial_outcome_history(conn: object, *, tenant_id: UUID, opportunity_id: UUID, limit: int = 50) -> list[dict[str, object]]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT previous_outcome, new_outcome, offered_price, actual_revenue, actual_cost,
               actual_margin, currency, operator_ref, reason, outcome_at, created_at
          FROM commercial_outcome_history
         WHERE tenant_id=%s AND opportunity_id=%s
         ORDER BY created_at DESC, id DESC LIMIT %s
        """,
        (tenant_id, opportunity_id, limit),
    ).fetchall()
    return [
        {"previous_outcome": r[0], "outcome": r[1], "offered_price": str(r[2]) if r[2] is not None else None,
         "actual_revenue": str(r[3]) if r[3] is not None else None,
         "actual_cost": str(r[4]) if r[4] is not None else None,
         "actual_margin": str(r[5]) if r[5] is not None else None, "currency": r[6],
         "operator_ref": r[7], "reason": r[8], "outcome_at": r[9].isoformat(), "created_at": r[10].isoformat()}
        for r in rows
    ]
