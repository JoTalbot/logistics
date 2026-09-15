# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V40 — Control Plane AUTO-policy hardening
STATUS: v40_completed
AGENT: logistics-commercial-batch-v40
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-15
SCOPE: V40 завершён на уровне репозитория; Control Plane AUTO-классификация усилена, проверки CI и backup/restore E2E зелёные.

## V40 completion

- Исправлена слабая граница Control Plane `_approval()`: строковой `startswith` больше не позволяет составному shell-командному вводу ошибочно попасть в AUTO-policy.
- AUTO-классификация теперь выполняется по `shlex`-разобранному argv и отклоняет shell composition (`&&`, `||`, `;`, `|`, redirection, backticks, `$(`), parse errors и небезопасные дополнительные аргументы.
- Сохранены разрешённые AUTO-команды: `pwd`, `whoami`, `date`, `uname`, `uname -a`, `git status`, `git diff`, `git log`, а также `python -m pytest` и `python -m compileall` с допустимыми аргументами.
- Добавлен регрессионный тест, подтверждающий, что `git status; rm -rf ...`, `git status && whoami`, `git status --output=...` и `python -c ...` не классифицируются как AUTO, тогда как `git status`, `uname -a` и `python -m pytest -q` остаются AUTO.
- Application fix commit: `82478d09a5ba11bf18d810166de3a7278e0ab282`.
- Regression test commit: `2e49f1cbbd6ce94fa375bc2712ec2c1bcde8c6f5`.
- CI run `34980919203` успешно завершён: зависимости, audit, миграции, unit/integration tests, V20 replay, hardened Compose contract, release smoke и hardened API image прошли.
- Backup Restore E2E run `34980919219` успешно завершён: disposable PostgreSQL 17 backup/restore, schema и rehearsal marker verification прошли.
- Текущий application-bearing verified head: `2e49f1cbbd6ce94fa375bc2712ec2c1bcde8c6f5`.
- Граница безопасности не изменена: никаких provider protection bypass, autonomous publication, contact/messaging, negotiation, contracting, pricing mutation, booking или financial action.

## Verification state

**SOFTWARE CONTOUR: GREEN** — V39 production closure baseline, remote-agent lease-error completion, V40 strict AUTO-policy classification, hardened Compose E2E и disposable backup/restore E2E verified by GitHub Actions. Current verified head is `2e49f1cbbd6ce94fa375bc2712ec2c1bcde8c6f5`.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE** — disposable PostgreSQL 17 rehearsal passed; target production infrastructure rehearsal remains required.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI**; target production-infrastructure rehearsal remains pending.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; no successful Vercel deployment is claimed for the current application head.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening.
IN_PROGRESS: external production-readiness/activation gates; no demonstrated internal blocker remains from V40.
NEXT: resolve external production gates, then rerun affected verification contours. Avoid decorative application changes while external blockers remain unchanged.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout after security review.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping, Vercel account/integration block, contact adapters, external publication permissions, production backup/restore rehearsal, real commercial outcome telemetry, calibration sample size.
