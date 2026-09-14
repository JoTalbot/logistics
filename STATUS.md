# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V31 — production observability integration
STATUS: v31_readiness_smoke_implemented_ci_pending
AGENT: logistics-commercial-batch-v31
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-14
UPDATED: 2026-09-14
SCOPE: V31 integrates deterministic readiness evidence into the local release smoke path while preserving the shadow-only commercial safety boundary.

## V31 delivered in branch

- Release smoke now records explicit readiness gates for API health, database fail-closed behavior, operator authentication and tenant-scoped audit reporting.
- The smoke path reuses the V30 deterministic readiness evaluator instead of duplicating release-gate logic.
- Machine-readable evidence is emitted with schema `logistics.release-readiness.v1`.
- Required unready gates fail closed rather than allowing a false release-ready result.
- Focused regression coverage verifies evidence structure and readiness semantics.
- Documentation updated with the operational evidence contract.

## V30 delivered and merged

- Pure deterministic readiness-gate evaluator.
- Explicit `ready`, `pending`, and `blocked` gate states.
- Required vs informational gates.
- Deterministic aggregate release-readiness report.
- Duplicate-name and missing-evidence validation.
- No provider, policy, publication, negotiation, contract or financial side effects.
- Focused V30 tests and documentation.
- PR #8 merged to `main` with merge commit `d0617832a8f2d361acce84a03066f4e33e481809`.
- V30 PR CI run `34843365739` completed successfully before merge.

## Current CI / deployment state

- V30 repository CI was green across all required stages before merge.
- Post-merge GitHub status reported an external Vercel failure: `Account is blocked`, with a deployment status pending at that time.
- An existing Vercel production deployment for `logistics` was previously observed in `READY` state, so repository code was not treated as the cause of that provider/account block.
- V31 changes are repository-local and do not attempt to bypass or repair the external Vercel account condition.

## V31 target / next gate

- Verify the new release-readiness evidence path in GitHub CI.
- Merge only after the branch CI is green.
- Then verify post-merge CI and commit status.
- Continue observability hardening with structured operational evidence, without enabling autonomous commercial actions.

## Safety boundary

Commercial learning/evaluation remains evidence-only. No automatic mutation of production pricing, scoring, autonomy policy, publication, negotiation, contract or financial state is authorized by V31.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcome data: **PENDING OPERATIONAL DATA**.
6. Vercel deployment integration for the `main` commit: **BLOCKED BY VERCEL ACCOUNT STATUS**; existing production deployment was previously observed as `READY`.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes and prediction-vs-actual measurement, V26 commercial calibration & feedback loop CI verification, V27 controlled calibration operations, V28 calibration learning loop implementation, V29 recommendation replay/evaluation implementation and CI verification, V30 deterministic readiness-gate evaluation and CI verification.
IN_PROGRESS: V31 release-readiness evidence integration and CI verification.
NEXT: verify/merge V31, then continue operational observability and production-readiness hardening.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration; Vercel account/integration remediation.
REQUIRED HUMAN ACTION: target infrastructure rehearsal, Lardi provider/support action, and Vercel account remediation before those external gates can be cleared. No repository-secret change is required for V31 foundation work.
OPEN_ISSUES: provider access/mapping, Vercel account/integration block, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
