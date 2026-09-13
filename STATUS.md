# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V27 — commercial calibration operations & controlled learning
STATUS: v26_verified_v27_ready
AGENT: logistics-commercial-batch-v27
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-13
UPDATED: 2026-09-13
SCOPE: V26 verified. Commercial calibration is now available in shadow mode; V27 focuses on operationalizing calibration evidence without automatic pricing, scoring or autonomy-policy mutation.

## V26 verified

- PR #5 `feat(v26): commercial calibration and feedback loop` merged to `main`.
- Merge commit: `b9efbdf0c314707b99dcb836f19c3409c32b5ad6`.
- Fresh CI Run #341 completed successfully.
- V26 adds deterministic calibration by priority bands: low, medium, high and very_high.
- Reports win rate, mean prediction error and mean absolute prediction error per band.
- Gates drift signals on minimum terminal sample size.
- Uses the latest commercial outcome per opportunity to prevent duplicate outcome-history rows from distorting calibration.
- Provides authenticated, tenant-scoped, read-only calibration reporting.
- Recommendations remain shadow-only with explicit `policy_mutation: false`.
- No automatic pricing, scoring or autonomy-policy mutation is enabled.

## Safety boundary

V26 is an evaluation/calibration layer. It does not publish listings, contact customers/carriers, negotiate, sign contracts, move money, bypass provider controls, or automatically rewrite pricing, scoring or autonomy policy. Model confidence and learning metrics are never authorization.

## V27 direction

- Turn calibration evidence into durable operator-facing learning reports and review queues.
- Track calibration/drift snapshots over time without mutating live policy.
- Add deterministic recommendation history and explicit operator acknowledgement.
- Preserve tenant isolation, append-only auditability and shadow-only behavior.
- Require sufficient real commercial outcome telemetry before any policy-change proposal can be considered.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes, prediction-vs-actual measurement and shadow learning CI verification, V26 commercial calibration & feedback loop CI verification.
IN_PROGRESS: none.
NEXT: V27 commercial calibration operations & controlled learning.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the V26 evaluation foundation.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
