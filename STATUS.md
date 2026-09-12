# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V25 — commercial outcomes & learning
STATUS: v25_commercial_outcomes_ci_pending
AGENT: logistics-commercial-batch-v25
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-12
UPDATED: 2026-09-12
SCOPE: Connect operator decisions to durable realized outcomes, actual margin and shadow-only learning metrics. No autonomous external commitment or outreach is enabled.

## V24 verified

- PR #2 `feat(v24): operator opportunity workflow` merged to `main`.
- Merge commit: `eedcabd9ca6f0a773f1dec003c0af47187d69020`.
- V24 adds tenant-scoped operator decisions, immutable review history, row locking and review metrics.
- Production release is not declared.

## V25 implementation

- Added `0025_commercial_outcomes.sql` with tenant-scoped append-only commercial outcome history.
- Added explicit outcomes: `won`, `lost`, `cancelled`, `unknown`.
- Persisted offered price, actual revenue, actual cost, realized margin, operator reference, reason and correlation ID.
- Added authenticated operator endpoints to record outcomes, inspect outcome history, view commercial outcome metrics and compare predicted versus actual margin.
- Added deterministic shadow-only learning evaluation by priority bands.
- Learning is evaluation only: it does not mutate pricing, scoring or autonomy policy.
- Added focused tests for validation, tenant scoping, realized margin, API registration and learning calibration.
- Updated Compose to mount migration 0025.

## Safety boundary

V25 changes and measures internal commercial state only. It does not publish listings, contact customers/carriers, negotiate, sign contracts, move money, bypass provider controls, or automatically rewrite business policy. Model confidence and learning metrics are never authorization.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Verification

- V25 implementation committed on branch `v25-commercial-outcomes-learning`.
- Fresh CI verification is pending.
- Production release is **NOT declared**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow.
IN_PROGRESS: V25 commercial outcomes, prediction-vs-actual measurement and shadow learning CI verification.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; real outcome telemetry.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current V25 code batch.
OPEN_ISSUES: V25 CI verification, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal and real commercial outcome telemetry.
