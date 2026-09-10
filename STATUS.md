# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V18 — integration adapters and production deployment hardening
STATUS: v18_integration_production_hardening
AGENT: logistics-commercial-batch-v18
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-11
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery. No autonomous external commitment or outreach is enabled.

## V17 completed

- Added durable `outbox_delivery_attempts` telemetry keyed by `(event_id, attempt_number)`.
- Delivery-attempt recording is idempotent with `ON CONFLICT DO NOTHING`.
- Telemetry captures tenant, worker, start/finish timestamps, outcome and bounded error text.
- Added validation and unit coverage for replay-attempt identity, successful completion and bounded failure details.
- The telemetry layer is observational: it does not create a second event identity or silently mutate commercial state.
- Existing tenant-scoped priority/review APIs remain unchanged and gated by the operator token.

## V18 in progress

- Added `/health` liveness and `/ready` database readiness probes.
- Readiness uses a bounded three-second PostgreSQL connection timeout and returns HTTP 503 when configuration or database connectivity is unavailable.
- Added API container healthcheck against `/ready` and a 30-second graceful shutdown window in Compose.
- Added missing migrations `0020_commercial_priority.sql` and `0021_outbox_delivery_telemetry.sql` to the PostgreSQL bootstrap mounts so a fresh Compose database receives the complete schema.
- Added unit coverage for readiness success, database failure, missing configuration and tenant-scoped review metrics.
- Latest hosted CI Run #214 `34532139807` on commit `eaf0b3d...` passed migrations and the complete test suite.
- New V18 commits are expected to trigger another hosted CI run; V18 is not marked complete until that run is green and remaining recovery/deployment verification is finished.

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

## Verification

- Hosted CI Run #214 `34532139807` passed on PostgreSQL 17 after the latest fixture alignment; migrations and the complete test job succeeded.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## Next batch

1. Finish V18 PostgreSQL recovery/replay integration coverage for outbox telemetry.
2. Verify configuration validation, container startup/readiness and graceful recovery paths in hosted CI.
3. Reconcile provider adapter contracts and production deployment documentation.
4. Add provider-specific canonical mappings only from verified Lardi samples after access is restored.
5. Keep contact adapters and external publication gated behind explicit provider permissions, terms, privacy and legal verification.
6. After V18 is actually green and verified, execute V19 security/compliance and release-gate hardening.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V17 reliability/replay hardening foundation; initial V18 readiness and Compose production-hardening layer.
PENDING: V18 hosted CI after latest changes; deeper PostgreSQL recovery/isolation verification; provider-side Lardi access; provider-specific mappings.
REQUIRED HUMAN ACTION: Lardi provider/support action before another live smoke. No repository-secret change is required.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters and external publication permissions.
