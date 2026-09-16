# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V43.1 — Remote-agent lease-loss lifecycle fencing
STATUS: v43.1_verified_external_gates_blocked
AGENT: logistics-commercial-batch-v43.1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-16
SCOPE: V43.1 завершает локальный lifecycle-контур V43: после потери lease authority remote agent завершает локальный process group и не отправляет устаревшие event/completion записи обратно в control plane.

## V43.1 implementation

- Remote agent остаётся на версии `0.3.0`.
- `execute_control_task()` использует lease-aware execution path.
- Во время leased task watchdog периодически отправляет heartbeat event в control plane.
- HTTP 401/409 от heartbeat трактуется как server-authoritative fencing-событие.
- При fencing локальный subprocess завершается вместе с POSIX process group непосредственного leased subprocess.
- `execute_control_task()` при `lease_lost=true` прекращает lifecycle writes и не отправляет stale stdout/stderr events или `/complete`.
- Обычный `/v1/exec` timeout также завершает POSIX process group перед возвратом HTTP 408.
- Регрессии process-tree fencing и stale lifecycle writes покрыты unit-тестами без зависимости от `pytest-asyncio`.

## Security semantics

Credential generation остаётся server-side fencing token: stale credential/lease не может продвигать lifecycle task после revoke или re-enrollment. V43 добавляет локальную реакцию агента на потерю server authority, а V43.1 исключает последующие stale lifecycle writes из уже fenced процесса.

Watchdog не является механизмом обхода provider protections и не расширяет operator permissions. Он действует только внутри уже выданного task lease и реагирует на server-authoritative 401/409.

Локальное завершение для POSIX запускается на уровне process group непосредственного leased subprocess; это закрывает обычный сценарий наследуемых descendants. Процессы, намеренно создающие независимые session/process groups, не получают абсолютной гарантии от этого механизма и требуют отдельного operational hardening, если такой сценарий станет обязательным для production.

Queued tasks не уничтожаются при credential revoke автоматически: revoke фехтует уже выданные running leases, после чего легитимный re-enrollment может продолжить очередь.

## Verification state

**SOFTWARE CONTOUR: VERIFIED GREEN** — V43.1 head `ef33d5c2a488d1647ef7445bf38ffd9ff3665db0` прошёл CI run `35106024315` / job `104827325864` (run #505): dependency consistency, pip-audit, migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract, local release smoke и hardened API image build завершены успешно.

**COMPOSE E2E: VERIFIED GREEN** — V43.1 head `ef33d5c2a488d1647ef7445bf38ffd9ff3665db0` прошёл Compose E2E run `35106024471` / job `104827325508` (run #77), включая hardened Compose stack rehearsal.

**BACKUP RESTORE E2E: VERIFIED GREEN** — V43.1 head `ef33d5c2a488d1647ef7445bf38ffd9ff3665db0` прошёл Backup Restore E2E run `35106024454` / job `104827325478` (run #75): migrations, disposable seed, logical backup, restore и restored schema/rehearsal marker verification завершены успешно.

**CURRENT CODE HEAD:** `ef33d5c2a488d1647ef7445bf38ffd9ff3665db0` — regression coverage for stale lifecycle fencing.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; current commit status reports Vercel account blocked and deployment check pending; no successful Vercel deployment is claimed for the current application head.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening, V42 agent-scoped idempotency and credential-generation lease fencing, V43 remote-agent local lease watchdog and process-tree fencing, V43.1 stale lifecycle-write fencing and CI verification.
IN_PROGRESS: external production-readiness/activation gates and broader remote-agent operational hardening.
NEXT: target production backup/restore rehearsal, provider access/mapping, explicit publication/contact authorization, authorized Telegram source access, Vercel account remediation, real booked/delivered outcome telemetry, independent-session process termination policy if required, and broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; independent-session process termination policy if required operationally; broader remote-agent rollout.
