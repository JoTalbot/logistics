# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V26 — commercial calibration & feedback loop
STATUS: v25_verified_merged_v26_planning
AGENT: logistics-commercial-batch-v26
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-13
UPDATED: 2026-09-13
SCOPE: Use realized commercial outcomes to measure calibration, drift and segment-level scoring quality in shadow mode. No automatic pricing, scoring or autonomy-policy mutation is enabled.

## V25 verified

- PR #3 `feat(v25): commercial outcomes and shadow learning` merged to `main`.
- Merge commit: `c8af1fd0a8a1e2f98427b8225dca876311f16116`.
- CI Run #336 completed successfully.
- V25 adds tenant-scoped append-only commercial outcome history, realized margin, conversion metrics, prediction-vs-actual reporting and deterministic shadow-only learning evaluation.
- Production release is not declared.

## V26 next stage

- Calibrate commercial priority/scoring against realized outcomes.
- Measure prediction error and outcome quality by priority bands and relevant commercial segments.
- Detect score drift and insufficient sample sizes before proposing any policy change.
- Produce deterministic shadow recommendations only; never mutate pricing, scoring or autonomy policy automatically.
- Keep external publication, outreach, negotiation, contracts and financial actions outside the learning loop unless separately authorized and audited.

## Safety boundary

V26 is an evaluation/calibration layer. It does not publish listings, contact customers/carriers, negotiate, sign contracts, move money, bypass provider controls, or automatically rewrite business policy. Model confidence and learning metrics are never authorization.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Verification

- V25 branch `v25-commercial-outcomes-learning` merged to `main` at `c8af1fd0a8a1e2f98427b8225dca876311f16116`.
- CI Run #336 / `34769443372`: **SUCCESS**.
- Production release is **NOT declared**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes, prediction-vs-actual measurement and shadow learning CI verification.
IN_PROGRESS: V26 commercial calibration & feedback loop.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the V26 evaluation foundation.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
