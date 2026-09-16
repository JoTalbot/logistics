# Project Status — AI Logistics OS

CURRENT_STEP: V43.3 — Remote-agent target-host cgroup readiness contract and gated rehearsal
STATUS: v43.3_verified_external_gates_blocked
UPDATED: 2026-09-16

## Verification state

**SOFTWARE CONTOUR: GREEN** — repository head `38e1c329868e99b50d784ec9ef506fa6ed0b44e9` passed CI #582 (`35131552215`) successfully, including dependency consistency, dependency audit, SQL migrations, unit/integration tests, V20 baseline replay, hardened Compose contract, local release smoke checks, hardened API image build, and the read-only cgroup capability probe. The suite reported 314 tests passed with 10 warnings; the pytest integration marker warning is resolved, while the remaining warnings are the FastAPI `on_event("startup")` deprecation. The previous implementation head `0d18f75f484b90ef1ff4549c664dc8ecc438a959` and documentation head `9a92ef149f20d490e7c688442743ff61d419e757` remain validated by earlier green CI runs.

**COMPOSE E2E: GREEN** — repository head `38e1c329868e99b50d784ec9ef506fa6ed0b44e9` passed Compose E2E #154 (`35131552162`) successfully.

**BACKUP RESTORE E2E: GREEN** — repository head `38e1c329868e99b50d784ec9ef506fa6ed0b44e9` passed Backup Restore E2E #152 (`35131552208`) successfully.

**REPOSITORY HEAD:** `38e1c329868e99b50d784ec9ef506fa6ed0b44e9` — `test: register integration pytest marker`. This is test/CI configuration only and does not change application runtime behavior.

**CURRENT FUNCTIONAL IMPLEMENTATION HEAD:** `0d18f75f484b90ef1ff4549c664dc8ecc438a959` — credential-generation lease fencing and deterministic lock regression coverage remain the latest functional runtime contour.

**CURRENT DESIGN STATE:** readiness contract, capability probe и opt-in target-host rehearsal implemented; runtime per-task cgroup isolation не реализована. Design gate требует реального Linux rehearsal с detached descendant до включения enforcement.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; current commit status still reports Vercel failure and no successful Vercel deployment is claimed.
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
