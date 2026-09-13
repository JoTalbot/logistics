# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V26 — commercial calibration & feedback loop
STATUS: v26_implementation_ci_pending
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

## V26 implementation

- Added deterministic calibration by priority bands: low, medium, high and very_high.
- Added win-rate, mean prediction error and mean absolute prediction error per band.
- Added minimum terminal-sample gating so thin data cannot trigger a calibration recommendation.
- Added material drift detection across sufficiently sampled adjacent priority bands.
- Added authenticated, tenant-scoped read-only endpoint `/api/v1/review/commercial-calibration`.
- Added explicit shadow recommendation and `policy_mutation: false` invariant.
- Added focused tests and documentation.
- No new database migration is required: V26 reads the durable V25 commercial outcome history.

## Safety boundary

V26 is an evaluation/calibration layer. It does not publish listings, contact customers/carriers, negotiate, sign contracts, move money, bypass provider controls, or automatically rewrite pricing, scoring or autonomy policy. Model confidence and learning metrics are never authorization.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Verification

- V26 implementation committed on branch `v26-commercial-calibration`.
- Fresh CI verification is pending.
- Production release is **NOT declared**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes, prediction-vs-actual measurement and shadow learning CI verification.
IN_PROGRESS: V26 commercial calibration & feedback loop CI verification.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the V26 evaluation foundation.
OPEN_ISSUES: V26 CI verification, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
