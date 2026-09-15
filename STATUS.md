# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V36 — Telegram commercial discovery integration
STATUS: v36_implemented_review_fix_pending_ci
AGENT: logistics-commercial-batch-v36
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-15
UPDATED: 2026-09-15
SCOPE: V36 connects the existing deterministic Telegram parser/validation contour to commercial candidate ranking without enabling autonomous external actions.

## V36 delivered

- Added safe orchestration: Telegram source messages → deterministic parsing → fail-closed validation → canonical `Load` → commercial candidate ranking.
- Added `candidate_digest()` with stable business evidence fields for API/dashboard use.
- Added focused acceptance/rejection tests.
- Added the V36 agent-skill documentation and explicit safety boundary.
- Review found a real test-fixture defect: `PricingInput.distance_km` is required. Fixed both fixtures to provide deterministic distance input.
- Review also exposed an incorrect `PriceEstimate` field reference in the digest. Fixed `candidate.price.amount` to the existing `target_price` field.
- No autonomous publication, negotiation, contracting, pricing mutation or financial action was enabled.

## V36 verification state

- PR #14: open, currently mergeable after the review fixes.
- Latest V36 head: `ea910042436d6cec10a9dde803f60fb7d08804bb`.
- Repository workflow-run lookup currently exposes no PR-triggered run for the latest head through the connected GitHub interface.
- Combined commit status currently reports only the existing Vercel integration failure; this is an external account/provider gate, not evidence of a Python test failure.
- The focused tests were corrected from review findings but have not been independently executed in this connector session; CI must remain the authoritative execution gate before merge.

## Safety boundary

V36 remains evidence-only. It does not enable autonomous publication, negotiation, contracting, pricing mutation or financial actions. Provider telemetry is not treated as proof of authorization or availability. Lardi/Cloudflare protections are not bypassed.

## External production gates

1. Backup/restore rehearsal: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping: **BLOCKED BY PROVIDER**; previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. Publication/contact permissions: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.
5. Real booked/delivered outcomes: **PENDING OPERATIONAL DATA**.
6. Vercel main deployment integration: **BLOCKED BY VERCEL ACCOUNT STATUS**; existing production deployment was previously observed as `READY`.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, V22 bounded remote control, V23 commercial opportunity queue, V24 operator opportunity workflow, V25 commercial outcomes, V26 commercial calibration, V27 controlled calibration operations, V28 calibration learning loop, V29 recommendation replay/evaluation, V30 deterministic readiness-gate evaluation, V31 readiness evidence integration, V32 operational observability, V33 observability/KPI integration, V34 production evidence hardening, V35 final production-readiness audit, V36 Telegram commercial discovery integration.
IN_PROGRESS: PR #14 CI verification and merge gate.
NEXT: obtain a green authoritative CI result for PR #14, merge V36, then execute the authorized Telegram ingestion/persistence contour when credentials and target access are available.
PENDING: PR #14 CI; target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent rollout only after security review; real outcome telemetry; Vercel account/integration remediation.
REQUIRED HUMAN ACTION: target infrastructure rehearsal, Lardi provider/support action, explicit publication/contact authorization, and Vercel account remediation remain external blockers.
OPEN_ISSUES: provider access/mapping, Vercel account/integration block, duplicate identity evidence, contact adapters, external publication permissions, production-infrastructure rehearsal, real commercial outcome telemetry, calibration sample size.
