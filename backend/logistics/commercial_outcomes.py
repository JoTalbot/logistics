from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID


ALLOWED_OUTCOMES = {"won", "lost", "cancelled", "unknown"}


@dataclass(frozen=True)
class CommercialOutcome:
    opportunity_id: UUID
    outcome: str
    currency: str
    operator_ref: str
    reason: str
    offered_price: Decimal | None = None
    actual_revenue: Decimal | None = None
    actual_cost: Decimal | None = None
    correlation_id: str | None = None


def _money(value: object | None, field: str) -> Decimal | None:
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if amount < 0:
        raise ValueError(f"{field} must be non-negative")
    return amount.quantize(Decimal("0.01"))


def validate_commercial_outcome(outcome: CommercialOutcome) -> CommercialOutcome:
    if outcome.outcome not in ALLOWED_OUTCOMES:
        raise ValueError("invalid commercial outcome")
    if not outcome.currency.strip() or len(outcome.currency.strip()) > 16:
        raise ValueError("currency is required")
    if not outcome.operator_ref.strip():
        raise ValueError("operator_ref is required")
    if not outcome.reason.strip():
        raise ValueError("reason is required")
    revenue = _money(outcome.actual_revenue, "actual_revenue")
    cost = _money(outcome.actual_cost, "actual_cost")
    offered = _money(outcome.offered_price, "offered_price")
    if revenue is not None and cost is not None and outcome.outcome in {"won", "lost"}:
        return CommercialOutcome(
            opportunity_id=outcome.opportunity_id,
            outcome=outcome.outcome,
            currency=outcome.currency.strip().upper(),
            operator_ref=outcome.operator_ref.strip(),
            reason=outcome.reason.strip(),
            offered_price=offered,
            actual_revenue=revenue,
            actual_cost=cost,
            correlation_id=outcome.correlation_id,
        )
    return CommercialOutcome(
        opportunity_id=outcome.opportunity_id,
        outcome=outcome.outcome,
        currency=outcome.currency.strip().upper(),
        operator_ref=outcome.operator_ref.strip(),
        reason=outcome.reason.strip(),
        offered_price=offered,
        actual_revenue=revenue,
        actual_cost=cost,
        correlation_id=outcome.correlation_id,
    )


def realized_margin(actual_revenue: Decimal | None, actual_cost: Decimal | None) -> Decimal | None:
    if actual_revenue is None or actual_cost is None:
        return None
    return (actual_revenue - actual_cost).quantize(Decimal("0.01"))


def record_commercial_outcome(conn: object, *, tenant_id: UUID, outcome: CommercialOutcome) -> dict[str, object]:
    outcome = validate_commercial_outcome(outcome)
    opportunity = conn.execute(
        """
        SELECT id, offered_price, currency, estimated_margin
          FROM opportunities o
          JOIN loads l ON l.id=o.load_id AND l.tenant_id=o.tenant_id
         WHERE o.tenant_id=%s AND o.id=%s
        """,
        (tenant_id, outcome.opportunity_id),
    ).fetchone()
    if opportunity is None:
        raise ValueError("opportunity not found")
    currency = outcome.currency or str(opportunity[2])
    if outcome.currency != str(opportunity[2]).upper():
        raise ValueError("currency does not match opportunity")
    margin = realized_margin(outcome.actual_revenue, outcome.actual_cost)
    row = conn.execute(
        """
        INSERT INTO commercial_outcome_history
          (tenant_id, opportunity_id, outcome, currency, offered_price,
           actual_revenue, actual_cost, actual_margin, operator_ref, reason, correlation_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id, recorded_at
        """,
        (tenant_id, outcome.opportunity_id, outcome.outcome, currency,
         outcome.offered_price if outcome.offered_price is not None else opportunity[1],
         outcome.actual_revenue, outcome.actual_cost, margin,
         outcome.operator_ref, outcome.reason, outcome.correlation_id),
    ).fetchone()
    return {
        "id": str(row[0]),
        "opportunity_id": str(outcome.opportunity_id),
        "outcome": outcome.outcome,
        "currency": currency,
        "offered_price": str(outcome.offered_price if outcome.offered_price is not None else opportunity[1]),
        "actual_revenue": str(outcome.actual_revenue) if outcome.actual_revenue is not None else None,
        "actual_cost": str(outcome.actual_cost) if outcome.actual_cost is not None else None,
        "actual_margin": str(margin) if margin is not None else None,
        "predicted_margin": str(opportunity[3]) if opportunity[3] is not None else None,
        "prediction_error": str(margin - opportunity[3]) if margin is not None and opportunity[3] is not None else None,
        "operator_ref": outcome.operator_ref,
        "reason": outcome.reason,
        "recorded_at": row[1].isoformat(),
    }


def list_commercial_outcomes(conn: object, *, tenant_id: UUID, opportunity_id: UUID, limit: int = 50) -> list[dict[str, object]]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT outcome, currency, offered_price, actual_revenue, actual_cost,
               actual_margin, operator_ref, reason, correlation_id, recorded_at
          FROM commercial_outcome_history
         WHERE tenant_id=%s AND opportunity_id=%s
         ORDER BY recorded_at DESC, id DESC
         LIMIT %s
        """,
        (tenant_id, opportunity_id, limit),
    ).fetchall()
    return [
        {
            "outcome": r[0], "currency": r[1], "offered_price": str(r[2]) if r[2] is not None else None,
            "actual_revenue": str(r[3]) if r[3] is not None else None,
            "actual_cost": str(r[4]) if r[4] is not None else None,
            "actual_margin": str(r[5]) if r[5] is not None else None,
            "operator_ref": r[6], "reason": r[7], "correlation_id": r[8],
            "recorded_at": r[9].isoformat(),
        }
        for r in rows
    ]


def commercial_outcome_metrics(conn: object, *, tenant_id: UUID) -> dict[str, object]:
    row = conn.execute(
        """
        WITH latest AS (
          SELECT DISTINCT ON (h.opportunity_id)
                 h.opportunity_id, h.outcome, h.actual_revenue, h.actual_margin,
                 o.estimated_margin
            FROM commercial_outcome_history h
            JOIN opportunities o ON o.id=h.opportunity_id AND o.tenant_id=h.tenant_id
           WHERE h.tenant_id=%s
           ORDER BY h.opportunity_id, h.recorded_at DESC, h.id DESC
        )
        SELECT count(*),
               count(*) FILTER (WHERE outcome='won'),
               count(*) FILTER (WHERE outcome='lost'),
               count(*) FILTER (WHERE outcome='cancelled'),
               count(*) FILTER (WHERE outcome='unknown'),
               coalesce(sum(actual_revenue) FILTER (WHERE outcome='won'),0),
               coalesce(sum(actual_margin) FILTER (WHERE outcome='won'),0),
               avg(actual_margin - estimated_margin) FILTER (WHERE actual_margin IS NOT NULL AND estimated_margin IS NOT NULL)
          FROM latest
        """,
        (tenant_id,),
    ).fetchone()
    total, won, lost, cancelled, unknown, revenue, margin, error = map(lambda x: x, row)
    terminal = int(won) + int(lost)
    return {
        "outcomes_recorded": int(total),
        "won": int(won), "lost": int(lost), "cancelled": int(cancelled), "unknown": int(unknown),
        "won_rate_of_terminal": round(int(won) / terminal, 4) if terminal else 0.0,
        "realized_revenue_won": str(revenue),
        "realized_margin_won": str(margin),
        "average_prediction_error": str(error.quantize(Decimal("0.01"))) if error is not None else None,
    }


def prediction_actual_report(conn: object, *, tenant_id: UUID, limit: int = 500) -> list[dict[str, object]]:
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    rows = conn.execute(
        """
        SELECT DISTINCT ON (h.opportunity_id)
               h.opportunity_id, h.outcome, o.priority_score, o.estimated_margin,
               h.actual_margin, h.currency, h.recorded_at
          FROM commercial_outcome_history h
          JOIN opportunities o ON o.id=h.opportunity_id AND o.tenant_id=h.tenant_id
         WHERE h.tenant_id=%s AND h.actual_margin IS NOT NULL
         ORDER BY h.opportunity_id, h.recorded_at DESC, h.id DESC
         LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()
    return [
        {
            "opportunity_id": str(r[0]), "outcome": r[1],
            "priority_score": float(r[2]) if r[2] is not None else None,
            "predicted_margin": str(r[3]) if r[3] is not None else None,
            "actual_margin": str(r[4]),
            "prediction_error": str(r[4] - r[3]) if r[3] is not None else None,
            "currency": r[5], "recorded_at": r[6].isoformat(),
        }
        for r in rows
    ]
