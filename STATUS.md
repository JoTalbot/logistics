# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V43.2.1 — Remote-agent cgroup-boundary regression verification
STATUS: v43.2.1_verified_external_gates_blocked
AGENT: logistics-commercial-batch-v43.2.1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-16
SCOPE: V43.2.1 синхронизирует regression coverage с фактической семантикой systemd/cgroup документации; runtime per-task cgroup isolation по-прежнему не объявляется реализованным.

## V43.2.1 implementation

- Remote agent остаётся на версии `0.3.0`.
- V43/V43.1/V43.2 process-boundary механизмы сохранены без изменения runtime semantics.
- Regression test теперь проверяет именно фактические формулировки README о будущем per-task supervisor и отсутствии абсолютной гарантии без такого механизма.
- Это test/documentation alignment, а не расширение operator permissions и не обход provider protections.

## Security semantics

Credential generation остаётся server-side fencing token: stale credential/lease не может продвигать lifecycle task после revoke или re-enrollment. V43 добавляет локальную реакцию агента на потерю server authority, V43.1 исключает stale lifecycle writes, а V43.2 добавляет service-level containment.

`KillMode=control-group` является дополнительной operational boundary для всего remote-agent systemd service. Это не заменяет server-side lease fencing и не является доказательством фактического production deployment.

`Delegate=yes` не означает, что каждый task уже помещён в отдельный cgroup. Независимая session/process-group внутри task остаётся отдельным сценарным риском; его можно закрыть только отдельным per-task cgroup/systemd-scope механизмом, если такой уровень изоляции станет обязательным.

Watchdog не является механизмом обхода provider protections и не расширяет operator permissions. Он действует только внутри уже выданного task lease и реагирует на server-authoritative 401/409.

Queued tasks не уничтожаются при credential revoke автоматически: revoke фехтует уже выданные running leases, после чего легитимный re-enrollment может продолжить очередь.

## Verification state

**SOFTWARE CONTOUR: VERIFIED GREEN** — cgroup documentation regression fix commit `bc9be7b57d30802ee55b6684642acd067678479c` прошёл CI run `35108572827` / job `104836051316` (run #512): dependency consistency, pip-audit, migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract, local release smoke и hardened API image build завершены успешно.

**COMPOSE E2E: VERIFIED GREEN** — commit `bc9be7b57d30802ee55b6684642acd067678479c` прошёл Compose E2E run `35108572823` / job `104836050716` (run #84), включая hardened Compose stack rehearsal.

**BACKUP RESTORE E2E: VERIFIED GREEN** — commit `bc9be7b57d30802ee55b6684642acd067678479c` прошёл Backup Restore E2E run `35108572889` / job `104836051150`: migrations, disposable seed, logical backup, restore и restored schema/rehearsal marker verification завершены успешно.

**CURRENT CODE HEAD:** `bc9be7b57d30802ee55b6684642acd067678479c` — cgroup documentation regression alignment.

**CURRENT TEST FILE:** `tests/test_remote_agent_systemd.py` содержит отдельную проверку, что документация не выдаёт `Delegate=yes` за уже реализованную per-task cgroup isolation.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; no successful Vercel deployment is claimed.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening, V42 agent-scoped idempotency and credential-generation lease fencing, V43 remote-agent local lease watchdog and process-tree fencing, V43.1 stale lifecycle-write fencing and CI verification, V43.2 systemd service-level process boundary hardening and regression verification, V43.2.1 cgroup documentation regression alignment and CI verification.
IN_PROGRESS: external production-readiness/activation gates and broader remote-agent operational hardening.
NEXT: target production backup/restore rehearsal, provider access/mapping, explicit publication/contact authorization, authorized Telegram source access, Vercel account remediation, real booked/delivered outcome telemetry, per-task cgroup termination policy if required operationally, and broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; per-task cgroup isolation decision; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; per-task cgroup isolation decision if required operationally; broader remote-agent rollout.
