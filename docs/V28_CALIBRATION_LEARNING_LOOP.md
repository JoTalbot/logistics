# V28 — Calibration Learning Loop

V28 makes calibration evidence durable and operator-auditable while keeping production policy immutable.

## Delivered

- Durable tenant-scoped calibration snapshots.
- Deterministic shadow recommendations derived from sampled drift evidence.
- Recommendation identity includes the snapshot, preserving history across runs.
- Append-only operator acknowledgement/rejection events.
- Tenant-scoped recommendation and event reads.
- Learning metrics for snapshots, drift, recommendations and operator decisions.
- Authenticated operator API for snapshot creation, review and acknowledgement.
- Docker Compose migration wiring through `0026_calibration_learning_loop.sql`.

## Safety boundary

V28 does not change live pricing, opportunity scoring, autonomy policy, publication, negotiation, contracts or financial state. Acknowledging a recommendation records an operator decision only. It is not an authorization to mutate production policy.

Recommendations are deliberately bounded and remain shadow artifacts suitable for replay/evaluation before any separately authorized release.

## Operational flow

1. Operator requests a calibration snapshot for a tenant.
2. The current V26 calibration report is persisted as an immutable snapshot.
3. If material drift and sufficient samples exist, bounded deterministic shadow recommendations are created.
4. Operator reviews recommendations and may append an `acknowledged` or `rejected` event.
5. Future replay/evaluation can compare recommendations with later outcomes without rewriting historical evidence.

## Production gates still external

Target infrastructure backup/restore rehearsal, Lardi provider access/mapping, external publication permissions, contact adapters and sufficient real booked/delivered outcomes remain separate release gates.
