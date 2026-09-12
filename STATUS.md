# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V24 — operator opportunity workflow
STATUS: v24_operator_workflow_ci_pending
AGENT: logistics-commercial-batch-v24
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-12
UPDATED: 2026-09-12
SCOPE: Turn prioritized commercial opportunities into a controlled, auditable human review workflow. No autonomous external commitment or outreach is enabled.

## V23 verified

- PR #1 `feat(v23): commercial opportunity queue` merged to `main`.
- Merge commit: `8d9d0280054fed5284f6ecf31c39d401d2883a5c`.
- CI Run #329 `34707795550` passed successfully.
- Full CI, migrations, Compose validation, release smoke and production API image build passed.

## V24 implementation

- Added migration `0024_opportunity_review_history.sql` for immutable operator decision history.
- Added tenant-scoped `OpportunityReview` domain workflow with row locking and explicit status validation.
- Added authenticated operator endpoints for opportunity decisions, review metrics and per-opportunity history.
- Every status transition records previous status, new status, operator reference, reason and timestamp.
- Added focused unit tests covering validation, tenant scope, transitions, audit history and acceptance metrics.
- Added `docs/V24_OPERATOR_WORKFLOW.md`.
- Updated Compose to mount migration 0024.

## Safety boundary

V24 changes internal review state only. It does not publish listings, contact customers/carriers, negotiate, sign contracts, move money or bypass provider controls. Model confidence is never treated as authorization.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.

## Verification

- V24 implementation committed on branch `v24-operator-workflow`.
- Fresh CI verification is pending.
- Production release is **NOT declared**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification.
IN_PROGRESS: V24 operator opportunity workflow CI verification.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current V24 code batch.
OPEN_ISSUES: V24 CI verification, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
