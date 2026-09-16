# Project Status — AI Logistics OS

CURRENT_STEP: V43.8 — Current test-head CI verification and external readiness gates
STATUS: v43.8_verified_external_gates_blocked
UPDATED: 2026-09-16

## Verification state

**SOFTWARE CONTOUR: GREEN** — the latest application-bearing software head remains `362968477c368f4efd1b263715f86109c957bb37` (`fix(compose-e2e): apply remote-control migrations before verification`). The subsequent test-only commit `9a9f7f064000e21521bd2eeac7a3dbbb91f4c6f7` changes only `tests/test_remote_agent_install.py` and was verified by the current GitHub Actions CI/Compose/Backup Restore checks.

**CURRENT TEST HEAD: GREEN** — `main` is currently at `9a9f7f064000e21521bd2eeac7a3dbbb91f4c6f7` (`test(remote-agent): assert cgroup rehearsal stays opt-in`). Its GitHub Actions checks completed successfully: CI run `35145045520`, Compose E2E run `35145045527`, and Backup Restore E2E run `35145045536`. The CI job executed the repository pytest suite, including the remote-agent install regression, and completed dependency audit, migrations, baseline replay, hardened Compose validation, release smoke checks, API image build, and cleanup successfully.

**COMPOSE E2E: GREEN** — the current test-head Compose E2E contour is green. Target infrastructure rehearsal remains separate evidence from CI.

**BACKUP RESTORE E2E: GREEN** — the current test-head Backup Restore E2E contour is green. CI restore rehearsal is not treated as proof of target production backup/restore readiness.

**LATEST VERIFIED APPLICATION-BEARING SOFTWARE HEAD:** `362968477c368f4efd1b263715f86109c957bb37` — latest functional implementation point. The newer `9a9f7f064000e21521bd2eeac7a3dbbb91f4c6f7` commit is test-only and does not change application behavior.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is runtime-correct and covered by the lifecycle regression test; credential-generation lease fencing and deterministic lock regression coverage remain validated. The latest functional change remains the Compose E2E migration-order fix at `362968477c368f4efd1b263715f86109c957bb37`.

**CURRENT DESIGN STATE:** readiness contract, capability probe and opt-in target-host rehearsal implemented; runtime per-task cgroup isolation не реализована. The design gate requires a real Linux rehearsal with a detached descendant before enforcement is enabled.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — repository CI green status is not treated as evidence of target infrastructure, provider access, operator authorization, or production readiness.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; current `main` commit status reports `Vercel = failure` with `Account is blocked.` and `Vercel Deployments – fgfgggg = pending`; no successful Vercel deployment is claimed.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.
8. Target-host cgroup rehearsal: **PENDING AUTHORIZED TARGET HOST**; CI validates the contract and gate logic, but normal CI does not constitute evidence of target-host delegation or detached-descendant fencing.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

IN_PROGRESS: external production-readiness/activation gates and broader remote-agent operational hardening.
NEXT: authorized target-host cgroup rehearsal; target production backup/restore rehearsal; provider access/mapping; explicit publication/contact authorization; authorized Telegram source access; Vercel account remediation; real booked/delivered outcome telemetry; per-task cgroup runtime implementation only after architecture and target-host rehearsal gates pass; broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; target-host cgroup rehearsal; per-task cgroup isolation decision and runtime implementation; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, authorized target-host cgroup rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; target-host cgroup rehearsal; per-task cgroup isolation decision/runtime implementation; broader remote-agent rollout.
