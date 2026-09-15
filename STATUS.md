# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V41 — Per-agent credential lifecycle hardening
STATUS: v41_verified_pending_latest_ci
AGENT: logistics-commercial-batch-v41
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-15
SCOPE: V41 завершён на уровне репозитория; per-agent credentials, immutable agent identity, tenant binding, credential revocation и recovery remote-agent после отзыва усилены. Последний кодовый head требует завершения свежих CI/E2E прогонов.

## V41 completion

- Remote Control операции агента привязаны к per-agent credential; глобальный bootstrap token используется только для enrollment/re-enrollment.
- Credential хранится только как SHA-256 hash; plaintext выдаётся только при bootstrap/re-enrollment.
- Добавлен operator-only endpoint `POST /api/v1/control/agents/{agent_id}/credential/revoke`, который очищает активный credential, фиксирует `credential_revoked_at` и переводит агента в `offline`.
- Добавлена отдельная идемпотентная миграция `0027_remote_agent_credential_revocation.sql` для `credential_revoked_at`, не изменяя уже применявшуюся миграцию V41.
- После отзыва старый credential перестаёт проходить agent-auth; повторный enrollment через bootstrap token выдаёт новый credential для того же agent identity.
- Исправлен remote-agent lifecycle: при revoked/invalid agent credential агент сбрасывает локальное состояние enrollment и автоматически возвращается к bootstrap на следующем heartbeat, вместо зависания на отозванном token.
- Исправлен bootstrap path: при отсутствии `agent_id` используется именно global bootstrap token, даже если в окружении остался `CONTROL_AGENT_TOKEN`.
- Исправлен heartbeat для tenant-bound agents: сохранённый `tenant_id` возвращается в последующий heartbeat и проверяется сервером без возможности смены identity.
- Сохранены предыдущие V40 гарантии: argv-strict AUTO-policy, запрет shell composition, tenant isolation, атомарные lease/event проверки, корректная cancellation и terminal completion.
- Security boundary не изменён: никаких provider protection bypass, autonomous publication, contact/messaging, negotiation, contracting, pricing mutation, booking или financial action.

## Verification state

**SOFTWARE CONTOUR: GREEN BASELINE / FRESH V41 RUNS IN PROGRESS** — предыдущий verified head `539b91515ce59ec3fc9e666f2a899153db3f16f8` имел успешные CI #466, Backup Restore E2E #36 и Compose E2E #38. Текущий application head `bde17c4a3beebe3c1dd616129b9ff25e91821912` содержит lifecycle-recovery fix и проходит свежие GitHub Actions проверки.

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

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening.
IN_PROGRESS: fresh verification for V41 lifecycle-recovery fix plus external production-readiness/activation gates.
NEXT: finish fresh V41 CI/E2E verification, then resolve external production gates. Avoid decorative application changes while external blockers remain unchanged.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; broader remote-agent rollout after security review.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping, Vercel account/integration block, contact adapters, external publication permissions, production backup/restore rehearsal, real commercial outcome telemetry, calibration sample size.
