from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from .commercial_calibration import CalibrationBand, CalibrationReport


@dataclass(frozen=True)
class CalibrationSnapshot:
    snapshot_id: UUID
    tenant_id: UUID
    policy_version: str
    cases: int
    terminal_cases: int
    win_rate: float
    mean_prediction_error: Decimal | None
    mean_abs_prediction_error: Decimal | None
    drift_detected: bool
    drift_reason: str


@dataclass(frozen=True)
class ShadowRecommendation:
    recommendation_key: str
    band: str
    current_score: Decimal
    suggested_delta: Decimal
    suggested_score: Decimal
    rationale: str
    policy_mutation: bool = False


def _bounded_score(value: Decimal) -> Decimal:
    return max(Decimal("0.00"), min(Decimal("1.00"), value)).quantize(Decimal("0.01"))


def _band_reference_score(band: CalibrationBand) -> Decimal:
    return {
        "low": Decimal("0.25"),
        "medium": Decimal("0.625"),
        "high": Decimal("0.825"),
        "very_high": Decimal("0.95"),
    }[band.band]


def build_shadow_recommendations(
    report: CalibrationReport,
    *,
    snapshot_id: UUID,
    max_abs_delta: Decimal = Decimal("0.05"),
) -> tuple[ShadowRecommendation, ...]:
    """Build deterministic suggestions only; never changes live policy."""
    if max_abs_delta < 0:
        raise ValueError("max_abs_delta must be non-negative")
    if not report.drift_detected:
        return ()

    recommendations: list[ShadowRecommendation] = []
    for band in report.bands:
        if not band.sufficient_sample or band.mean_prediction_error is None:
            continue
        error = band.mean_prediction_error
        if error == 0:
            continue
        direction = Decimal("-1") if error > 0 else Decimal("1")
        magnitude = min(max_abs_delta, max(Decimal("0.01"), abs(error) / Decimal("1000")))
        delta = (direction * magnitude).quantize(Decimal("0.01"))
        current = _band_reference_score(band)
        suggested = _bounded_score(current + delta)
        rationale = (
            f"{band.band} band mean prediction error is {error}; "
            f"shadow adjustment is bounded to {max_abs_delta} and requires operator review"
        )
        recommendations.append(
            ShadowRecommendation(
                recommendation_key=f"{snapshot_id}:{band.band}",
                band=band.band,
                current_score=current,
                suggested_delta=delta,
                suggested_score=suggested,
                rationale=rationale,
            )
        )
    return tuple(recommendations)


def create_calibration_snapshot(conn: object, *, tenant_id: UUID, policy_version: str, report: CalibrationReport) -> CalibrationSnapshot:
    row = conn.execute(
        """
        INSERT INTO calibration_snapshots
          (tenant_id, policy_version, cases, terminal_cases, win_rate,
           mean_prediction_error, mean_abs_prediction_error, drift_detected, drift_reason)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id, created_at
        """,
        (
            tenant_id, policy_version, report.cases, report.terminal_cases, report.win_rate,
            report.mean_prediction_error, report.mean_abs_prediction_error,
            report.drift_detected, report.drift_reason,
        ),
    ).fetchone()
    return CalibrationSnapshot(
        snapshot_id=row[0], tenant_id=tenant_id, policy_version=policy_version,
        cases=report.cases, terminal_cases=report.terminal_cases, win_rate=report.win_rate,
        mean_prediction_error=report.mean_prediction_error,
        mean_abs_prediction_error=report.mean_abs_prediction_error,
        drift_detected=report.drift_detected, drift_reason=report.drift_reason,
    )


def persist_shadow_recommendations(conn: object, *, tenant_id: UUID, snapshot_id: UUID, recommendations: tuple[ShadowRecommendation, ...]) -> int:
    for item in recommendations:
        conn.execute(
            """
            INSERT INTO calibration_recommendations
              (tenant_id, snapshot_id, recommendation_key, band, current_score,
               suggested_delta, suggested_score, rationale, policy_mutation)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (tenant_id, recommendation_key) DO NOTHING
            """,
            (
                tenant_id, snapshot_id, item.recommendation_key, item.band,
                item.current_score, item.suggested_delta, item.suggested_score,
                item.rationale, item.policy_mutation,
            ),
        )
    return len(recommendations)


def acknowledge_recommendation(
    conn: object,
    *,
    tenant_id: UUID,
    recommendation_id: UUID,
    decision: str,
    operator_ref: str,
    reason: str,
) -> None:
    if decision not in {"acknowledged", "rejected"}:
        raise ValueError("decision must be acknowledged or rejected")
    if not operator_ref.strip():
        raise ValueError("operator_ref is required")
    if not reason.strip():
        raise ValueError("reason is required")
    exists = conn.execute(
        "SELECT 1 FROM calibration_recommendations WHERE tenant_id=%s AND id=%s",
        (tenant_id, recommendation_id),
    ).fetchone()
    if exists is None:
        raise LookupError("recommendation not found")
    conn.execute(
        """
        INSERT INTO calibration_recommendation_events
          (tenant_id, recommendation_id, event, operator_ref, reason)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (tenant_id, recommendation_id, decision, operator_ref.strip(), reason.strip()),
    )


def list_recommendations(conn: object, *, tenant_id: UUID, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")
    params: list[object] = [tenant_id]
    status_sql = ""
    if status is not None:
        if status not in {"pending", "acknowledged", "rejected"}:
            raise ValueError("invalid recommendation status")
        status_sql = "AND COALESCE(e.event, 'pending') = %s"
        params.append(status)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT r.id, r.snapshot_id, r.recommendation_key, r.band,
               r.current_score, r.suggested_delta, r.suggested_score,
               r.rationale, r.created_at,
               COALESCE(e.event, 'pending') AS status,
               e.operator_ref, e.reason, e.created_at
          FROM calibration_recommendations r
          LEFT JOIN LATERAL (
            SELECT event, operator_ref, reason, created_at
              FROM calibration_recommendation_events e
             WHERE e.tenant_id=r.tenant_id AND e.recommendation_id=r.id
             ORDER BY e.created_at DESC, e.id DESC
             LIMIT 1
          ) e ON true
         WHERE r.tenant_id=%s {status_sql}
         ORDER BY r.created_at DESC
         LIMIT %s
        """,
        tuple(params),
    ).fetchall()
    return [
        {
            "id": str(row[0]), "snapshot_id": str(row[1]), "recommendation_key": row[2],
            "band": row[3], "current_score": str(row[4]), "suggested_delta": str(row[5]),
            "suggested_score": str(row[6]), "rationale": row[7], "created_at": row[8].isoformat(),
            "status": row[9], "operator_ref": row[10], "acknowledgement_reason": row[11],
            "acknowledged_at": row[12].isoformat() if row[12] else None,
            "policy_mutation": False,
        }
        for row in rows
    ]


def list_recommendation_events(conn: object, *, tenant_id: UUID, recommendation_id: UUID) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT id, event, operator_ref, reason, created_at
          FROM calibration_recommendation_events
         WHERE tenant_id=%s AND recommendation_id=%s
         ORDER BY created_at ASC, id ASC
        """,
        (tenant_id, recommendation_id),
    ).fetchall()
    return [
        {"id": row[0], "event": row[1], "operator_ref": row[2], "reason": row[3], "created_at": row[4].isoformat()}
        for row in rows
    ]


def learning_metrics(conn: object, *, tenant_id: UUID) -> dict[str, int]:
    row = conn.execute(
        """
        SELECT
          (SELECT count(*) FROM calibration_snapshots WHERE tenant_id=%s) AS snapshots,
          (SELECT count(*) FROM calibration_snapshots WHERE tenant_id=%s AND drift_detected) AS drift_snapshots,
          (SELECT count(*) FROM calibration_recommendations WHERE tenant_id=%s) AS recommendations,
          (SELECT count(*) FROM calibration_recommendations r
             WHERE r.tenant_id=%s AND NOT EXISTS (
               SELECT 1 FROM calibration_recommendation_events e
                WHERE e.tenant_id=r.tenant_id AND e.recommendation_id=r.id)) AS pending_recommendations,
          (SELECT count(*) FROM calibration_recommendation_events WHERE tenant_id=%s AND event='acknowledged') AS acknowledged,
          (SELECT count(*) FROM calibration_recommendation_events WHERE tenant_id=%s AND event='rejected') AS rejected
        """,
        (tenant_id, tenant_id, tenant_id, tenant_id, tenant_id, tenant_id),
    ).fetchone()
    return {
        "snapshots": row[0], "drift_snapshots": row[1], "recommendations": row[2],
        "pending_recommendations": row[3], "acknowledged": row[4], "rejected": row[5],
    }
