# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V43.3 — Remote-agent target-host cgroup readiness contract and gated rehearsal
STATUS: v43.3_verified_external_gates_blocked
AGENT: logistics-commercial-batch-v43.3
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-16
SCOPE: V43.3 формализует machine-readable target-host readiness contract (`READY` / `BLOCKED` / `UNSUPPORTED`), добавляет read-only systemd capability evidence и gated opt-in rehearsal; runtime per-task cgroup isolation по-прежнему не объявляется реализованным.

## V43.3 implementation

- Remote agent остаётся на версии `0.3.0`.
- V43/V43.1/V43.2 process-boundary механизмы сохранены без изменения runtime semantics.
- `deploy/remote-agent/cgroup_probe.py` является read-only capability probe: он определяет Linux/cgroup-v2/systemd contour, execution identity, доступность `systemd-run`, версию systemd и необходимые cgroup access flags без изменения host state.
- `target_host_readiness=READY` означает только наличие prerequisites для opt-in target-host rehearsal; это не означает, что runtime per-task cgroup isolation уже внедрена.
- `target_host_readiness=BLOCKED` означает поддерживаемый Linux/cgroup-v2/systemd contour с недостаточными правами/делегацией текущей identity.
- `target_host_readiness=UNSUPPORTED` означает отсутствие требуемого Linux/cgroup-v2/systemd backend.
- `deploy/remote-agent/cgroup_gate.py` запускает destructive rehearsal только при явном `LOGISTICS_CGROUP_REHEARSAL=1`, non-root identity и `READY` probe result.
- `deploy/remote-agent/cgroup_rehearsal.py` остаётся отдельной target-host проверкой: реальный task, detached-session descendant, общая task cgroup и fencing через `cgroup.kill`.
- Нормальный CI не выполняет destructive target-host rehearsal.
- `tests/test_remote_agent_cgroup_probe.py` и `tests/test_remote_agent_cgroup_gate.py` регрессируют readiness contract, fail-closed поведение, identity/permission semantics и отсутствие destructive systemd actions в probe.

## Security semantics

Credential generation остаётся server-side fencing token: stale credential/lease не может продвигать lifecycle task после revoke или re-enrollment. V43 добавляет локальную реакцию агента на потерю server authority, V43.1 исключает stale lifecycle writes, а V43.2 добавляет service-level containment.

`KillMode=control-group` является дополнительной operational boundary для всего remote-agent systemd service. Это не заменяет server-side lease fencing и не является доказательством фактического production deployment.

`Delegate=yes` не означает, что каждый task уже помещён в отдельный cgroup. Независимая session/process-group внутри task остаётся отдельным сценарным риском; его можно закрыть только отдельным per-task cgroup/systemd-scope механизмом после прохождения target-host decision gate.

Watchdog не является механизмом обхода provider protections и не расширяет operator permissions. Он действует только внутри уже выданного task lease и реагирует на server-authoritative 401/409.

Queued tasks не уничтожаются при credential revoke автоматически: revoke фехтует уже выданные running leases, после чего легитимный re-enrollment может продолжить очередь.

## Verification state

**SOFTWARE CONTOUR: VERIFIED GREEN** — current code head `da3f9d838f0344b317201beb5def6b94ae6c56f5` прошёл CI run `35114381963` / job `104855948355` с результатом `success`. Включая read-only cgroup capability probe, dependency consistency, pip-audit, migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract, local release smoke и hardened API image build.

**COMPOSE E2E: VERIFIED GREEN** — current head `da3f9d838f0344b317201beb5def6b94ae6c56f5` прошёл Compose E2E run `35114381911` / job `104855945159` с результатом `success`.

**BACKUP RESTORE E2E: VERIFIED GREEN** — current head `da3f9d838f0344b317201beb5def6b94ae6c56f5` прошёл Backup Restore E2E run `35114382078` / job `104855946682` с результатом `success`.

**CURRENT CODE HEAD:** `da3f9d838f0344b317201beb5def6b94ae6c56f5` — `test(remote-agent): correct subprocess call shape`.

**CURRENT DESIGN STATE:** readiness contract, capability probe и opt-in target-host rehearsal implemented; runtime per-task cgroup isolation не реализована. Design gate требует реального Linux rehearsal с detached descendant до включения enforcement.

**PRODUCTION ACTIVATION: BLOCKED EXTERNALLY** — кодовая готовность не используется как доказательство фактической готовности внешней инфраструктуры, провайдеров или операторских разрешений.

## External production gates

1. Backup/restore rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **GREEN IN CI / PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; retry/bypass не выполняется.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; current combined status on `da3f9d838f0344b317201beb5def6b94ae6c56f5` reports `Vercel=failure` and `Vercel Deployments=pending`; no successful Vercel deployment is claimed.
7. Authorized Telegram credentials/source access: **PENDING EXTERNAL AUTHORIZATION**.
8. Target-host cgroup rehearsal: **PENDING AUTHORIZED TARGET HOST**; CI validates the contract and gate logic, but normal CI does not constitute evidence of target-host delegation or detached-descendant fencing.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Provider telemetry is not treated as proof of authorization or availability.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour, V38 production verification confidence-gate fix, V39 production closure and external-gate readiness, V40 Control Plane AUTO-policy hardening, V41 per-agent credential lifecycle hardening, V42 agent-scoped idempotency and credential-generation lease fencing, V43 remote-agent local lease watchdog and process-tree fencing, V43.1 stale lifecycle-write fencing and CI verification, V43.2 systemd service-level process boundary hardening and regression verification, V43.2.1 cgroup documentation regression alignment and CI verification, V43.2.2 cgroup capability/design invariant verification and CI verification, V43.3 target-host readiness contract and gated rehearsal verification.
IN_PROGRESS: external production-readiness/activation gates and broader remote-agent operational hardening.
NEXT: authorized target-host cgroup rehearsal; target production backup/restore rehearsal; provider access/mapping; explicit publication/contact authorization; authorized Telegram source access; Vercel account remediation; real booked/delivered outcome telemetry; per-task cgroup runtime implementation only after architecture and target-host rehearsal gates pass; broader remote-agent rollout.
PENDING: target production backup/restore rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; real commercial outcome telemetry; Vercel account/integration remediation; authorized Telegram credentials/source access; target-host cgroup rehearsal; per-task cgroup isolation decision and runtime implementation; broader remote-agent rollout.
REQUIRED HUMAN ACTION: target infrastructure backup/restore rehearsal, authorized target-host cgroup rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_GATES: provider access/mapping; Vercel account/integration block; contact adapters; external publication permissions; production backup/restore rehearsal; real commercial outcome telemetry; calibration sample size; target-host cgroup rehearsal; per-task cgroup isolation decision/runtime implementation; broader remote-agent rollout.
