# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V16 — operator control plane hardening
STATUS: v16_operator_control_plane
AGENT: logistics-commercial-batch-v16
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery. No autonomous external commitment or outreach is enabled.

## V16 completed

- Tenant-scoped priority queue SLA metrics: counts by status, oldest age, average age, high-priority open count and stale-open count.
- Configurable priority SLA threshold validation with safe defaults: high priority `0.8`, stale after `12h`.
- Authenticated `/api/v1/review/priorities/metrics` operator endpoint.
- `/api/v1/review/summary` now exposes priority queue health and a conservative tenant-scoped `operational_status`.
- Scheduler failure/staleness remains critical; stale open priority work marks the operator summary degraded.
- API unit coverage for priority metrics validation, tenant scoping and summary health behavior.
- No new migration was required; V16 uses existing durable priority fields from V15.

## Commercial chain

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → recurring demand → deterministic priority → operator queue → SLA/health visibility`

V14 priority formula:

`65% opportunity score + 20% carrier availability signal + 15% recurring-demand signal`

The commercial pipeline remains deterministic and explainable. It does not publish, contact or commit funds.

## Existing foundations

- Telegram collection, deterministic parsing, canonicalization, atomic persistence/checkpointing and transactional outbox.
- PostgreSQL baseline and migrations.
- Market observations, historical price intelligence, route economics and recommendation persistence.
- Demand graph, customer discovery, customer opportunity scoring and recurring-demand persistence/scheduler.
- Human review audit and authenticated operator APIs.
- Authorized contact intents with suppression and mandatory human approval.
- Tenant-scoped duplicate detection and scheduler health thresholds.
- Durable commercial priority queue with tenant isolation.

## Verification

- Hosted CI Run #101 `34520924164` passed on the prior persisted-recommendation/status head.
- Latest direct commits are present on `main`; GitHub connector currently returns no workflow runs/status checks for these direct commits, so latest CI is not claimed as green.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## Next batch

1. V17: reliability hardening: replay/idempotency/recovery checks around commercial priority recomputation and operator state.
2. Add real PostgreSQL tenant-isolation coverage for summary and priority metrics/queue.
3. Add duplicate replay telemetry before considering stronger DB identity materialization.
4. Add provider-specific canonical mappings only from verified Lardi samples after access is restored.
5. Keep contact adapters and external publication gated behind explicit provider permissions, terms, privacy and legal verification.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V16 operator control-plane hardening with priority SLA/age visibility, aggregate health and tenant-scoped tests.
PENDING: CI verification for latest direct commits; provider-side Lardi access; provider-specific mappings; deeper PostgreSQL isolation coverage.
REQUIRED HUMAN ACTION: Lardi provider/support action before another live smoke. No repository-secret change is required.
OPEN_ISSUES: provider access/mapping, CI visibility for direct commits, duplicate identity evidence, contact adapters and external publication permissions.
