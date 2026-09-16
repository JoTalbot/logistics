# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V42 — Agent-scoped idempotency and credential-generation lease fencing
STATUS: v42_verified_external_gates_blocked
AGENT: logistics-commercial-batch-v42
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-16
SCOPE: V42 усиливает две выявленные границы Control Plane: idempotency теперь scoped по agent identity, а активные task leases получают credential generation и немедленно fencing-ятся при revoke/re-enrollment.

## V42 implementation

- Task idempotency lookup выполняется по `(agent_id, idempotency_key)`, а не только по tenant; одинаковый ключ у разных agents больше не возвращает чужой `task_id`.
- Добавлена миграция `0028_remote_task_idempotency_agent_scope.sql` с agent-scoped уникальностью idempotency key.
- Добавлена миграция `0029_remote_agent_credential_generation.sql`: `remote_agents.credential_generation` и `remote_tasks.lease_credential_generation`.
- При re-enrollment credential generation увеличивается, поэтому новый credential не наследует generation старого credential.
- При operator revoke generation увеличивается, credential очищается, агент переводится offline, а все его текущие running leases переводятся в `cancelled`.
- При выдаче lease в `tasks/next` в task сохраняется текущая credential generation.
- `events` и `complete` требуют совпадения lease generation с текущей generation агента; stale lease после revoke/re-enrollment не может продлить lease или завершить task.
- Expired running leases очищают `lease_credential_generation` при возврате в queue.

## Security semantics

Credential generation является server-side fencing token. Он не убивает уже запущенный локальный процесс на remote machine, но исключает его дальнейшее server-authoritative продвижение task lifecycle после revoke. Process-level termination по-прежнему требует локального cancellation/watchdog механизма на самом агенте.

Queued tasks не уничтожаются при credential revoke автоматически: revoke фехтует только уже выданные running leases. Это позволяет после легитимного re-enrollment продолжить безопасную обработку очереди без переноса старого lease authority.

Global `REMOTE_AGENT_TOKEN` остаётся enrollment trust boundary. Изменение этой модели требует отдельного operator-issued bootstrap policy и не должно смешиваться с lease fencing.

## Verification state

**SOFTWARE CONTOUR: VERIFIED GREEN** — V42 application/schema changes on `db61e37bed8ba61c4469bde9c562ca580fe9f950` прошли основной CI run `35101338522` / job `104811255393`: 282 tests passed, dependency/security/replay/Compose/release-smoke/image-build stages completed successfully.

**BACKUP RESTORE E2E: VERIFIED GREEN** — run `35101338414` / job `104811254906` успешно применил SQL migrations, создал disposable rehearsal backup, восстановил его и проверил restored schema и rehearsal marker.

Previous verified baseline: V41 application head `835746bfdac888c3c76763329a5f11861df245a8` прошёл Backup Restore E2E #42 и Compose E2E #44.

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

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening, V42 agent-scoped idempotency and credential-generation lease fencing implementation and CI verification.
IN_PROGRESS: external production-readiness/activation gates.
NEXT: target production backup/restore rehearsal, provider access/mapping, explicit publication/contact authorization, authorized Telegram source access, Vercel account remediation, real booked/delivered outcome telemetry, and broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; local process-level cancellation if required operationally.
