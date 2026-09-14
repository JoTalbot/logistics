# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V30 — operational observability and production-readiness hardening
STATUS: v29_merged_v30_started
AGENT: logistics-commercial-batch-v30
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-14
UPDATED: 2026-09-14
SCOPE: V29 is merged. V30 continues with operational observability and production-readiness hardening while preserving the shadow-only commercial safety boundary.

## V29 delivered and merged

- Deterministic recommendation replay/evaluation.
- Later score observations and terminal wins/losses are measured.
- Mean score delta and mean absolute margin prediction error are calculated.
- Invalid score ranges are rejected.
- Evaluation remains pure and side-effect free.
- Focused tests and documentation are present.
- Incorrect sample test expectation was corrected to `0.0`.
- PR #7 merged to `main` with merge commit `d19674a9b9c17760aa309b293b136b765b42ebb8`.
- V29 CI on head commit `b4e9fa79bd948dcc1e42ffcaeabfaa3a1d436244` completed successfully (run `34842926022`).

## V30 target

- Strengthen operational observability around recommendation evaluation and commercial workflows.
- Keep metrics deterministic and side-effect free where possible.
- Improve production-readiness evidence without enabling autonomous publication, negotiation, contracts or financial mutations.
- Preserve tenant isolation, auditability and explicit operator authorization boundaries.

## Safety boundary

Commercial learning/evaluation remains evidence-only. No automatic mutation of production pricing, scoring, autonomy policy, publication, negotiation, contract or financial state is authorized by V30.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes and prediction-vs-actual measurement, V26 commercial calibration & feedback loop CI verification, V27 controlled calibration operations, V28 calibration learning loop implementation, V29 recommendation replay/evaluation implementation and CI verification.
IN_PROGRESS: V30 operational observability and production-readiness hardening.
NEXT: implement the smallest high-value observability/readiness increment, test it, update status, and verify CI.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for V30 foundation work.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
