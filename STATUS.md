# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V28 — calibration learning loop
STATUS: v28_implementation_complete_ci_pending
AGENT: logistics-commercial-batch-v28
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-14
UPDATED: 2026-09-14
SCOPE: V28 makes commercial calibration durable and operator-auditable while keeping production pricing, scoring and autonomy policy immutable.

## V27 verified

- V27 controlled commercial calibration operations is merged to `main`.
- Main merge commit: `ee859bda20ea2bf8efb53013183c26a497646ffe`.
- V27 requires drift, sufficient terminal sample and explicit operator approval before a shadow adjustment is considered eligible.
- Suggested score changes are bounded.
- Production policy remains unchanged.

## V28 delivered

- Durable tenant-scoped calibration snapshots.
- Deterministic shadow recommendations derived from sampled drift evidence.
- Recommendation identity includes the snapshot, preserving history across runs.
- Append-only operator acknowledgement/rejection events.
- Tenant-scoped recommendation and event reads.
- Learning metrics for snapshots, drift, recommendations and operator decisions.
- Authenticated operator API for snapshot creation, review and acknowledgement.
- Migration `0026_calibration_learning_loop.sql` wired into Compose.
- No automatic pricing, scoring, autonomy-policy, publication, negotiation, contract or financial mutation.

## Safety boundary

V28 is a controlled learning/evaluation layer. An operator acknowledgement records a decision but does not mutate production policy. Recommendations remain shadow artifacts and require a separate authorized release process before any production policy change.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes and prediction-vs-actual measurement, V26 commercial calibration & feedback loop CI verification, V27 controlled calibration operations, V28 calibration learning loop implementation.
IN_PROGRESS: V28 CI verification.
NEXT: V29 replay/evaluation of recommendation effectiveness and stronger operational observability, still shadow-only.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the V28 evaluation foundation.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
