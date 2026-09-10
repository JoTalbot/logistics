# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Customer discovery V1 — commercial chain and operator control plane
STATUS: v13_operator_control_plane
AGENT: logistics-commercial-batch-v13
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery. No autonomous external commitment or outreach is enabled.

## Completed

- Product vision, V1→V10 autonomy model, product specification, human workflow and distributed agent protocol.
- Technical architecture, roadmap and ecosystem/integration strategy.
- Routing/Geo/Optimization architecture and canonical geo pipeline.
- V1 backend skeleton, canonical domain, deterministic normalize→score→opportunity workflow.
- Policy/authorization and audit primitives.
- PostgreSQL baseline plus Telegram ingestion migrations.
- Telegram collection, deterministic parsing, canonicalization, atomic persistence/checkpointing and transactional outbox.
- Replay fixtures, PostgreSQL integration tests and optional OpenTelemetry.
- Publication adapter contract and provider-neutral renderer.
- Publication policy gate for autonomy role, bounded markup, cancelled-load rejection and human approval for critical risk.
- Durable outbox delivery state and PostgreSQL lease/retry worker.
- Market operations primitives: deterministic cost/price estimation, opportunity scoring, capacity matching and bounded negotiation policy.
- Demand graph and deterministic customer-demand scoring/ranking.
- Official Lardi-Trans REST API client and read-only discovery adapter.
- Lardi read-only manual smoke workflow with masked credentials.
- Append-only market observation history and stale-observation protection.
- Explicit verified-field allowlist for provider-to-canonical extraction.
- Deterministic route economics, historical price trends and conservative recommended-price floor.
- Durable human review audit, approve/reject/hold transitions and authenticated review API.
- Review queue metrics endpoint for pending publication/negotiation work and review-decision totals.
- Lardi smoke diagnostics distinguish provider-edge blocks from credential, permission and rate-limit failures.
- Deterministic opportunity recommendation service combining route economics with compatible recent market evidence, with explainable reasons and currency-mismatch safety.
- Persisted recommendation fields and tenant-scoped recommendation store.
- Authenticated operator recommendation endpoint and audit reporting with decision trends and queue age.
- Provenance-first customer discovery core with explicit permitted-source validation and no-fetch/no-scrape boundary.
- Durable tenant-scoped customer prospects with provenance, freshness, qualification and suppression state.
- Prospect observation history schema, identity key, stale-update protection and sticky suppression controls.
- Deterministic customer-opportunity scoring combining demand fit, commercial value and signal freshness.
- Persisted tenant-scoped CustomerOpportunity records and authenticated operator queue endpoint.
- Authenticated prospect suppression/unsuppression endpoint with required reason.
- Deterministic recurring-demand detection from historical canonical loads, with route/cargo pattern keys, observation count, median interval, regularity, recurrence and freshness signals.
- Persisted recurring-demand patterns and load evidence with tenant-scoped uniqueness and idempotent evidence writes.
- Authenticated operator endpoint for recurring-demand review.
- Authorized contact-channel contracts for email, Telegram, phone and web form, with authorization, suppression and mandatory human approval gates.
- Durable contact-intent outbox that persists reviewable contact intents but never sends them.
- Audited contact-intent review transitions: approve, reject and hold, with tenant scoping and operator reason.
- Authenticated contact-intent review queue and decision API.
- Canonical Telegram load rehydration for recurring-demand analysis directly from persisted `loads` and `load_stops`.
- Multi-tenant recurring-demand recomputation with bounded 90-day history and six-hour scheduler.
- Docker Compose scheduler service with restart policy and PostgreSQL health dependency.
- Tenant-scoped likely duplicate-load detection using normalized route/cargo/weight/currency signatures and bounded creation-time windows.
- Connected duplicate-load grouping so transitively related duplicate pairs are presented as one group.
- Real PostgreSQL integration coverage for tenant isolation of review/discovery stores and duplicate detection.
- Durable recurring-demand scheduler run history with running/succeeded/failed state, tenant/pattern counts and bounded error text.
- Authenticated operator endpoint for recurring-demand scheduler health.
- Authenticated operator endpoint for tenant-scoped duplicate-load groups.
- Compact authenticated tenant-safe operator summary aggregating publication/negotiation/contact queues, candidate customer opportunities, duplicate groups and scheduler health.
- Scheduler operational thresholds: 12-hour stale-success threshold and 2-hour running timeout, with explicit healthy/running/stale/failed/critical states and run age.
- Unit coverage for scheduler threshold validation and stale/failed operational states.

## Current implementation

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → bounded negotiation → PublicationRequest → PolicyEngine → PublicationAdapter → Outbox`

Market discovery:

`Lardi API → provider boundary → MarketObservation → current state + immutable history → price intelligence → route economics → explainable recommendation → persisted Opportunity → operator review`

Customer discovery:

`Permitted source adapter → provenance-first Prospect → durable persistence → qualification → CustomerOpportunity scoring → recurring-demand evidence → authenticated operator queue → authorized contact intent → authenticated human review → first load → recurring customer`

Operator control plane:

`summary → review queue + customer opportunities + contact intents + duplicate groups + scheduler health + audit/recommendations`

Customer opportunity score:

`55% demand fit + 30% commercial fit + 15% signal freshness`

Freshness currently decays linearly to zero over 72 hours. Scoring is deterministic and explainable.

Recurring demand:

`persisted Telegram loads → tenant-scoped rehydration → route/cargo/currency pattern → ≥3 observations → median interval → median absolute deviation → regularity + recurrence + freshness → persisted pattern/evidence → operator review`

Contact safety boundary:

`authorized target + human-reviewed draft + no suppression → pending intent → operator approve/reject/hold → audit`

Approval never implies sending. There is deliberately no send endpoint or autonomous outreach adapter.

The discovery core deliberately does not fetch websites, scrape pages, harvest contact lists, send messages or perform opaque third-party enrichment.

External provider network operations remain behind explicit adapters. No browser automation, anti-bot bypass or unsupported scraping is part of the core.

## Verification

- Hosted CI Run #101 `34520924164` passed on the prior persisted-recommendation/status head.
- Latest direct commits are present on `main`; GitHub connector currently returns no workflow runs/status checks for these direct commits, so latest CI is not claimed as green.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`; they skip cleanly when PostgreSQL is unavailable.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical route/country/cargo/weight/price mapping remains blocked until a verified provider response is obtained. No field semantics are inferred from guessed JSON names.

## Next batch

1. Wire the commercial chain into a single deterministic orchestration boundary: Telegram → market observation → recurring demand → carrier matching → route economics → margin → priority → operator queue.
2. Add operator summary tests, including tenant-isolation coverage for aggregated counts and duplicate groups.
3. Add safe duplicate replay telemetry before considering stronger DB identity materialization; do not convert probabilistic duplicate signatures into a hard UNIQUE constraint without evidence.
4. Add provider-specific canonical mappings from verified Lardi response samples after provider access is restored.
5. Add provider-specific contact adapters only where permissions are verified, while keeping autonomous sending disabled.
6. Re-run Lardi read-only smoke only after provider support confirms the edge block or supplies an authorized API path.
7. Activate external publication only after provider-specific permission, commercial terms, privacy/retention and legal compliance are explicitly verified.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed. Lardi credentials are read from `LARDI_API_KEY`, with `LARDI_TRANS_API_TOKEN` retained only as a compatibility fallback. The smoke workflow does not echo secrets. Review API access requires `REVIEW_OPERATOR_TOKEN` and is disabled when it is not configured.

## Compliance

Provider publication is gated and transport-neutral. Customer discovery uses only explicitly permitted source workflows and preserves provenance. Contact is a separate authorized stage with suppression/opt-out controls. No claim is made that any marketplace or source permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation.

## Handoff

DONE: Market-intelligence foundations, recommendation persistence, operator reporting, durable prospect persistence, deterministic customer-opportunity scoring, recurring-demand persistence and scheduled recomputation, authorized contact contracts, audited contact review queue, duplicate grouping, scheduler health thresholds and compact operator control plane.
VERIFIED: Hosted CI Run #101 `34520924164` for the prior head; PostgreSQL integration path is wired into CI.
PENDING: CI verification for the latest direct commits.
REQUIRED HUMAN ACTION: Lardi provider/support action is required before another live smoke. No repository-secret change is required.
OPEN_ISSUES: Live Lardi provider permission/API response; provider-specific field mapping; CI visibility for direct commits; stronger DB duplicate identity only if evidence supports it; provider-specific contact adapters; external publication remains gated.
