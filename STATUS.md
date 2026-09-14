# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V29 — recommendation replay/evaluation
STATUS: v29_implementation_complete_ci_pending
AGENT: logistics-commercial-batch-v29
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-14
UPDATED: 2026-09-14
SCOPE: V29 adds deterministic, read-only replay/evaluation of shadow commercial recommendations without mutating production pricing, scoring, autonomy policy, publication, negotiation, contract or financial state.

## V29 delivered

- Deterministic recommendation replay/evaluation.
- Later score observations and terminal wins/losses are measured.
- Mean score delta is calculated from suggested vs later observed scores.
- Mean absolute margin prediction error is calculated when both margins exist.
- Invalid score ranges are rejected.
- Evaluation remains pure and side-effect free.
- Focused V29 tests and documentation are present.
- Corrected the V29 test expectation for the sample score delta: `0.0`.

## CI status

- Latest V29 CI run before the test correction: **FAILED** at the unit/integration test step.
- Dependency consistency, dependency audit and SQL migration stages passed.
- Failure was caused by an incorrect test assertion, not the V29 evaluation implementation.
- Test correction committed on `v29-recommendation-evaluation` as `2230ffeac78a435d11c4d1f3b4e21ff3fcc66bc6`.
- **NEXT GATE: rerun CI and require green before merge.**

## Safety boundary

V29 is evaluation-only. Results are evidence for an operator/release process and do not authorize or perform production policy mutation.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes and prediction-vs-actual measurement, V26 commercial calibration & feedback loop CI verification, V27 controlled calibration operations, V28 calibration learning loop implementation, V29 recommendation replay/evaluation implementation.
IN_PROGRESS: V29 CI verification.
NEXT: after green CI, review/merge V29 and continue operational observability and production-readiness gates.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the V29 evaluation foundation.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
