# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V19 — security, compliance and release-gate hardening
STATUS: v19_release_gate_hardening
AGENT: logistics-commercial-batch-v19
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery. No autonomous external commitment or outreach is enabled.

## V18 completed

- Added `/health` liveness and `/ready` database readiness probes.
- Readiness uses a bounded three-second PostgreSQL connection timeout and returns HTTP 503 when configuration or database connectivity is unavailable.
- Added API container healthcheck against `/ready` and a 30-second graceful shutdown window in Compose.
- Added missing migrations `0020_commercial_priority.sql` and `0021_outbox_delivery_telemetry.sql` to the PostgreSQL bootstrap mounts so a fresh Compose database receives the complete schema.
- Added unit coverage for readiness success, database failure, missing configuration and tenant-scoped review metrics.
- Added PostgreSQL outbox recovery/replay integration coverage for durable delivery telemetry.
- Restored the authenticated `/api/v1/review/audit/report` endpoint with tenant-scoped decision totals, daily trend and queue-age reporting plus bounds validation.
- Hosted CI Run #221 `34535526756` on commit `a0b002f...` passed: PostgreSQL migrations and the complete unit/integration test job succeeded.
- Run #220 `34534205706` exposed the missing audit-report endpoint; the follow-up commit restored it and Run #221 verified the fix.

## Reliability boundary

The outbox event UUID remains the canonical idempotency identity. A retry/replay creates a new attempt record, not a new business event. This preserves safe recovery semantics while making repeated delivery observable before any stronger database identity constraints are considered.

## Commercial chain

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → recurring demand → deterministic priority → operator queue → SLA/health visibility → observable delivery/recovery`

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
- Operator priority SLA metrics, age visibility and conservative aggregate health.
- Outbox delivery leases, bounded retries and durable replay telemetry.
- Production readiness probes and Compose graceful-shutdown hardening.

## Verification

- Hosted CI Run #221 `34535526756` passed on PostgreSQL 17; migration, unit and integration test steps all succeeded.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## V19 release gate

1. Audit security boundaries and tenant isolation across authenticated review/operator APIs.
2. Verify secret/configuration handling, startup failure modes and production Compose defaults.
3. Review migration ordering, fresh-database bootstrap and rollback/recovery assumptions.
4. Add release smoke checks for liveness/readiness, review auth, tenant isolation and outbox recovery without enabling external publication or outreach.
5. Reconcile provider adapter contracts and production deployment documentation.
6. Keep Lardi provider-specific canonical mappings blocked until verified samples/access are restored.
7. Keep contact adapters and external publication gated behind explicit provider permissions, terms, privacy and legal verification.
8. Perform final documentation, threat-model, dependency and release-gate audit before tagging a release.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V17 reliability/replay foundation and V18 integration/deployment hardening, including PostgreSQL recovery coverage and green hosted CI.
PENDING: V19 security/compliance/release-gate audit; provider-side Lardi access/mapping; duplicate identity evidence; contact adapters and external publication permissions.
REQUIRED HUMAN ACTION: Lardi provider/support action before another live smoke. No repository-secret change is required.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters and external publication permissions.
