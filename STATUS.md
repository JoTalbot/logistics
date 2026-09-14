# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V31 — production observability integration
STATUS: v31_readiness_smoke_merged_ci_pending
AGENT: logistics-commercial-batch-v31
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-14
UPDATED: 2026-09-14
SCOPE: V31 integrates deterministic readiness evidence into the local release smoke path while preserving the shadow-only commercial safety boundary.

## V31 delivered and merged

- Release smoke records explicit readiness gates for API health, database fail-closed behavior, operator authentication and tenant-scoped audit reporting.
- The smoke path reuses the V30 deterministic readiness evaluator instead of duplicating release-gate logic.
- Machine-readable evidence is emitted with schema `logistics.release-readiness.v1`.
- Required unready gates fail closed rather than allowing a false release-ready result.
- Focused regression coverage verifies evidence structure and blocked-gate behavior.
- Documentation defines the operational evidence contract.
- PR #9 merged to `main` with merge commit `84d97249dfee6942884e54fb446a87d5db79a9ee`.
- Branch CI run `34845091251` completed green across all 13 repository stages after the readiness integration fix.

## CI / deployment state

- V31 PR CI passed dependency checks, security audit, all tests, migrations, V20 replay, hardened Compose validation, release smoke and API image build.
- The first V31 CI attempt failed only because the new test imported `scripts.release_smoke` as a package that does not exist in the repository packaging layout. This was corrected by moving the reusable readiness-evidence helper into `logistics.readiness` and importing it from there.
- The corrected CI run passed the full pipeline.
- The Vercel integration/account condition remains external: the previous status reported `Account is blocked`. An existing production deployment was previously observed in `READY` state. V31 does not bypass or modify that external condition.

## V31 next target

- Verify the post-merge `main` CI and commit status.
- Continue operational observability hardening with structured evidence, provider latency and route-quality regression telemetry where existing architecture supports it.
- Keep provider connectivity separate from authorization for publication, negotiation, contracts or financial actions.

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

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening and CI verification, V23 commercial opportunity queue and CI verification, V24 operator opportunity workflow, V25 commercial outcomes and prediction-vs-actual measurement, V26 commercial calibration & feedback loop CI verification, V27 controlled calibration operations, V28 calibration learning loop implementation, V29 recommendation replay/evaluation implementation and CI verification, V30 deterministic readiness-gate evaluation and CI verification, V31 readiness evidence integration and PR CI verification.
IN_PROGRESS: post-merge V31 CI verification and next observability hardening.
NEXT: verify the post-merge main pipeline, then implement the next bounded observability/reliability improvement.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review; sufficient real outcome telemetry for calibration; Vercel account/integration remediation.
REQUIRED HUMAN ACTION: target infrastructure rehearsal, Lardi provider/support action, and Vercel account remediation before those external gates can be cleared. No repository-secret change is required for V31 work.
OPEN_ISSUES: provider access/mapping, Vercel account/integration block, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
