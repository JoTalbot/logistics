"""Read-only aggregation of durable autonomy decisions against delivery outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .autonomy_policy import ApprovalTier
from .policy_replay import HistoricalOutcome, PolicyReplayCase, PolicyReplayReport, evaluate_policy_replay


@dataclass(frozen=True)
class PolicyVersionReplay:
    policy_version: str
    report: PolicyReplayReport


@dataclass(frozen=True)
class HistoricalPolicyReplay:
    tenant_id: UUID
    reports: tuple[PolicyVersionReplay, ...]


def load_historical_policy_cases(
    conn: object,
    *,
    tenant_id: UUID,
    limit: int = 10_000,
) -> list[tuple[str, PolicyReplayCase]]:
    """Load durable decisions and derive outcomes from durable outbox delivery telemetry.

    A decision with any successful delivery is SUCCESS. Otherwise a decision with a
    failed delivery is FAILURE. Decisions without a matching delivery attempt remain
    UNKNOWN. The query is tenant-scoped and read-only.
    """
    if not 1 <= limit <= 100_000:
        raise ValueError("limit must be between 1 and 100000")

    rows = conn.execute(
        """
        SELECT d.policy_version, d.tier,
               CASE
                 WHEN bool_or(a.outcome = 'succeeded') THEN 'SUCCESS'
                 WHEN bool_or(a.outcome = 'failed') THEN 'FAILURE'
                 ELSE 'UNKNOWN'
               END AS historical_outcome
          FROM autonomy_decisions d
          LEFT JOIN outbox_events e
            ON e.tenant_id = d.tenant_id
           AND e.correlation_id::text = d.correlation_id
          LEFT JOIN outbox_delivery_attempts a
            ON a.event_id = e.event_id
         WHERE d.tenant_id = %s
         GROUP BY d.decision_id, d.policy_version, d.tier, d.created_at
         ORDER BY d.created_at ASC
         LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()

    return [
        (
            row[0],
            PolicyReplayCase(
                tier=ApprovalTier(row[1]),
                outcome=HistoricalOutcome(row[2]),
            ),
        )
        for row in rows
    ]


def aggregate_historical_policy_replay(
    conn: object,
    *,
    tenant_id: UUID,
    limit: int = 10_000,
) -> HistoricalPolicyReplay:
    """Aggregate durable historical outcomes by policy version without side effects."""
    grouped: dict[str, list[PolicyReplayCase]] = {}
    for policy_version, case in load_historical_policy_cases(
        conn, tenant_id=tenant_id, limit=limit
    ):
        grouped.setdefault(policy_version, []).append(case)

    reports = tuple(
        PolicyVersionReplay(
            policy_version=policy_version,
            report=evaluate_policy_replay(grouped[policy_version]),
        )
        for policy_version in sorted(grouped)
    )
    return HistoricalPolicyReplay(tenant_id=tenant_id, reports=reports)
