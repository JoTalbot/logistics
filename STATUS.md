# Project Status — AI Logistics OS

CURRENT_STEP: V43.10 — Verified remote-agent authentication hardening and external readiness gates
STATUS: v43.10_verified_external_gates_blocked
UPDATED: 2026-09-16

## Verification state

**SOFTWARE CONTOUR: GREEN** — the latest verified application-bearing change is `bb9bb7f449eb73af0b376fe23d34162c9e98d5fd` (`fix(remote-control): cancel active leases on credential reenrollment`). Subsequent commits add regression coverage for direct reenrollment and bearer authentication. The current verified test head is `b881ecce78896fc2b20770d40e99e671bd8d5ba8`.

**CURRENT TEST HEAD: GREEN** — GitHub Actions completed successfully for `b881ecce78896fc2b20770d40e99e671bd8d5ba8`: `test` run `35159690286`, `compose-e2e` run `35159690256`, and `backup-restore-e2e` run `35159690279`. The three checks all completed with conclusion `success`.

**COMPOSE E2E: GREEN** — the current test head passed the hardened Compose E2E workflow. Target infrastructure rehearsal remains separate evidence from CI.

**BACKUP RESTORE E2E: GREEN** — the current test head passed the Backup Restore E2E workflow. CI restore rehearsal is not treated as proof of target production backup/restore readiness.

**LATEST VERIFIED APPLICATION/TEST HEAD:** `b881ecce78896fc2b20770d40e99e671bd8d5ba8` — this head has successful CI, Compose E2E, and Backup Restore E2E verification. It adds explicit regression coverage that agent credentials require the `Bearer` scheme and preserves the accepted bearer path.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is runtime-correct and covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases so credential rotation does not leave stale tasks marked `running`; agent credential authentication requires an explicit `Bearer` scheme.

**CURRENT DESIGN STATE:** readiness contract, capability probe and opt-in target-host rehearsal implemented; runtime per-task cgroup isolation не реализована. The design gate requires a real Linux rehearsal with a detached descendant before enforcement is enabled.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — repository CI green status is not treated as evidence of target infrastructure, provider access, operator authorization, or production readiness.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; the last verified main status reported `Vercel = failure` with `Account is blocked.` and `Vercel Deployments – fgfgggg = pending`; no successful Vercel deployment is claimed.
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
