# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V39 — Production closure and external-gate readiness
STATUS: v39_completed
AGENT: logistics-commercial-batch-v39
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-15
SCOPE: V39 завершён на уровне репозитория; программные доказательства отделены от внешних production activation gates.

## V39 completion

- Добавлен интеграционный тест транзакционного rollback при отказе `commit()` в Telegram ingestion store.
- При сбое транзакции подтверждено отсутствие частично сохранённых source message, canonical load, outbox event и Telegram checkpoint.
- Существующие replay/rejection/idempotency проверки сохранены.
- Application-bearing V39 baseline ранее подтверждён GitHub Actions CI #414.
- Добавлен отдельный `.github/workflows/compose-e2e.yml` для безопасной CI-проверки полного hardened Compose стека.
- Compose E2E run `34975509229` успешно завершён: чистый PostgreSQL + API + recurring-demand-scheduler подняты, API `/ready` и `/health` проверены, scheduler подтвердил соединение с PostgreSQL, после теста стек очищен.
- Основной CI run `34975509243` успешно завершён на предыдущем application/documentation head: зависимости, audit, миграции, unit/integration tests, V20 baseline replay, Compose contract, release smoke и hardened API image build прошли.
- Добавлен отдельный `.github/workflows/backup-restore-e2e.yml` для disposable CI backup/restore rehearsal.
- Backup Restore E2E run `34976673543` успешно завершён после исправления несовместимости клиента PostgreSQL 16 с сервером PostgreSQL 17: backup создан, восстановлен в отдельную БД, schema и rehearsal marker проверены.
- Основной CI run `34976673729` успешно завершён на commit `e58378c4624a0e794e3a6cd30462c26b7454cde7`: зависимости, audit, миграции, unit/integration tests, V20 baseline replay, Compose contract, release smoke и hardened API image build прошли.
- Для backup/restore workflow `pg_dump` и `pg_restore` выполняются matching PostgreSQL 17 client из `postgres:17-alpine`, а runner-side `psql/createdb` используются для миграций и проверки.
- Исправлено рассогласование между Control Plane AUTO-policy и `deploy/remote-agent/agent.py`: команда `date`, разрешённая серверной AUTO-policy, теперь присутствует в agent allowlist.
- Добавлен регрессионный тест, который извлекает `ALLOWED` remote-agent и проверяет поддержку всех root-команд из AUTO-policy, включая `date`.
- Исправлен reliability-дефект remote-agent: исключение во время выполнения leased control-plane task больше не оставляет задачу навсегда в `running`; ошибка преобразуется в failed result, события отправляются best-effort, после чего выполняется попытка `/complete`.
- Добавлен регрессионный тест `tests/test_remote_agent.py`, проверяющий completion leased task после ошибки выполнения команды.
- Последний application-bearing commit `8c7ebd4633de66cd75ff674ac8c598bb2398e9de` прошёл обязательные проверки GitHub Actions: CI #439 и disposable Backup Restore E2E #9 зелёные.
- Граница безопасности не изменена: никаких provider protection bypass, autonomous publication, contact/messaging, negotiation, contracting, pricing mutation, booking или financial action.

## Verification state

**SOFTWARE CONTOUR: GREEN** — application-bearing baseline, hardened Compose E2E, disposable backup/restore E2E, remote-agent AUTO-policy consistency и leased-task error completion verified by GitHub Actions. Current verified head is `8c7ebd4633de66cd75ff674ac8c598bb2398e9de`.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE** — disposable PostgreSQL 17 rehearsal passed in GitHub Actions; target production infrastructure rehearsal remains required.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI**; target production-infrastructure rehearsal remains pending.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; current head reports `Vercel` = `failure` with the account-blocked target and `Vercel Deployments – fgfgggg` = `pending`. No successful Vercel deployment is claimed for the current application head.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness.
IN_PROGRESS: external production-readiness/activation gates; internal remote-agent lease-error completion defect is fixed and verified.
NEXT: resolve external production gates, then rerun the affected verification contours. No decorative application changes are justified while external blockers remain unchanged.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout after security review.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping, Vercel account/integration block, contact adapters, external publication permissions, production backup/restore rehearsal, real commercial outcome telemetry, calibration sample size.
