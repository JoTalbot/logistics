# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V43 — Remote-agent local lease watchdog and process-tree fencing
STATUS: v43_verified_external_gates_blocked
AGENT: logistics-commercial-batch-v43
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-16
SCOPE: V43 закрывает локальный пробел V42: server-side credential-generation fencing дополнен watchdog на remote agent, который периодически подтверждает lease через control plane и завершает локальный subprocess вместе с его process group при потере lease authority.

## V43 implementation

- Remote agent поднят до версии `0.3.0`.
- `execute_control_task()` использует lease-aware execution path вместо прямого `run_command()`.
- Во время выполнения leased task агент периодически отправляет heartbeat event в control plane.
- Потеря lease authority по HTTP 401/409 считается fencing-событием, после чего локальный subprocess принудительно завершается.
- Для POSIX-воркера leased subprocess запускается с отдельной session/process group, а fencing завершает process group, чтобы обычные дочерние процессы не переживали потерю lease.
- Результат выполнения содержит `lease_lost`, что позволяет отличать нормальное завершение от локального fencing.
- Watchdog имеет bounded polling interval: не чаще заданного heartbeat и не реже одного раза в 30 секунд для контроля длительного процесса.
- Ошибочный execution path покрыт тестом через актуальный `run_leased_command()`, а watchdog fencing покрыт отдельным unit-тестом без зависимости от `pytest-asyncio`.

## Security semantics

Credential generation остаётся server-side fencing token: stale credential/lease не может продвигать lifecycle task после revoke или re-enrollment. V43 добавляет локальную реакцию агента на потерю server authority, поэтому уже запущенный subprocess больше не обязан ждать естественного завершения команды.

Watchdog не является механизмом обхода provider protections и не расширяет operator permissions. Он действует только внутри уже выданного task lease и реагирует на server-authoritative 401/409.

Локальное завершение для POSIX запускается на уровне process group непосредственного leased subprocess; это закрывает обычный сценарий наследуемых descendants. Процессы, намеренно создающие независимые session/process groups, не получают абсолютной гарантии от этого механизма и требуют отдельного operational hardening, если такой сценарий станет обязательным для production.

Queued tasks не уничтожаются при credential revoke автоматически: revoke фехтует уже выданные running leases, после чего легитимный re-enrollment может продолжить очередь.

## Verification state

**SOFTWARE CONTOUR: VERIFIED GREEN** — V43 process-tree fencing head `84b92ce64682b024b70374563901137015c85203` прошёл CI run `35103934319` / job `104820131728` (run #498): dependency consistency, pip-audit, migrations, unit/integration tests, V20 replay, hardened Compose contract, release smoke и hardened API image build завершены успешно.

**COMPOSE E2E: VERIFIED GREEN** — V43 process-tree fencing head `84b92ce64682b024b70374563901137015c85203` прошёл Compose E2E run `35103934225` / job `104820130709` (run #70), включая hardened Compose stack rehearsal.

**BACKUP RESTORE E2E: VERIFIED GREEN** — V43 process-tree fencing head `84b92ce64682b024b70374563901137015c85203` прошёл Backup Restore E2E run `35103934618` (run #68): migrations, disposable seed, logical backup, restore и restored schema/rehearsal marker verification завершены успешно.

Previous verified application baseline: V42 `ca56a6194bc9502bb29cdaf1b449c985d31338db` прошёл CI, Compose E2E и Backup Restore E2E.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; no successful Vercel deployment is claimed for the current application head.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening, V42 agent-scoped idempotency and credential-generation lease fencing, V43 remote-agent local lease watchdog and process-tree fencing implementation and CI verification.
IN_PROGRESS: external production-readiness/activation gates and broader remote-agent operational hardening.
NEXT: target production backup/restore rehearsal, provider access/mapping, explicit publication/contact authorization, authorized Telegram source access, Vercel account remediation, real booked/delivered outcome telemetry, independent-session process termination policy if required, and broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; independent-session process termination policy if required operationally; broader remote-agent rollout.
