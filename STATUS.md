# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V37 — Telegram ingestion → commercial discovery contour
STATUS: v37_implemented_pending_ci
AGENT: logistics-commercial-batch-v37
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-15
SCOPE: V37 composes authenticated Telegram collection, transactional persistence, and deterministic commercial discovery into one bounded evidence-only batch operation.

## V37 delivered

- Added `run_ingestion_discovery_once()` for bounded Telegram collection → deterministic parsing → `TelegramIngestionStore` persistence → commercial discovery.
- Preserved PostgreSQL as the durable authority for source messages, canonical loads, outbox events, and checkpoints.
- Added structured `IngestionDiscoveryResult` exposing ingestion outcomes and the deterministic discovery report.
- Added orchestration tests for persisted-message ordering, ranking, and empty-batch behavior.
- Added V37 agent-skill documentation and explicit production activation boundary.
- No autonomous publication, negotiation, contracting, pricing mutation, booking, or financial action was enabled.

## V36 completion

- V36 Telegram commercial discovery integration is merged to `main` in PR #14.
- The review-found fixture defect around required `PricingInput.distance_km` was corrected.
- The digest uses the existing `PriceEstimate.target_price` field.
- The external Vercel account/integration block remains separate from Python correctness.

## V37 verification state

- V37 branch: `feat/v37-telegram-ingestion-discovery`.
- Focused tests were added but have not yet been independently executed in this connector session; CI remains the authoritative execution gate.
- Live Telegram execution is not claimed: authorized credentials and source access are external prerequisites.

## Safety boundary

V37 remains evidence-only. It does not enable autonomous publication, negotiation, contracting, pricing mutation or financial actions. Provider telemetry is not treated as proof of authorization or availability. Lardi/Cloudflare protections are not bypassed.

## External production gates

1. Backup/restore rehearsal: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; existing production deployment was previously observed as `READY`.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration, V37 Telegram ingestion → commercial discovery contour.
IN_PROGRESS: V37 CI verification and review gate.
NEXT: obtain a green authoritative CI result for V37, merge the contour, then activate live ingestion only when authorized Telegram credentials/source access are available.
PENDING: V37 CI; target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent rollout only after security review; real outcome telemetry; Vercel account/integration remediation.
REQUIRED HUMAN ACTION: target infrastructure rehearsal, Lardi provider/support action, explicit publication/contact authorization, authorized Telegram credentials/source access, and Vercel account remediation remain external blockers.
OPEN_ISSUES: provider access/mapping, Vercel account/integration block, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
