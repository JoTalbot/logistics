# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Market intelligence + commercial automation foundations V3
STATUS: ci_green_pending_provider_smoke
AGENT: logistics-commercial-batch-v3
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Outbox delivery worker, market observations, carrier matching, deterministic pricing/negotiation, demand scoring, price intelligence and authorized Lardi-Trans read-only API boundary. No autonomous external commitment is enabled.

## Completed

- Product vision, V1→V10 autonomy model, product specification, human workflow and distributed agent protocol.
- Technical architecture, roadmap and ecosystem/integration strategy.
- Routing/Geo/Optimization architecture and canonical geo pipeline.
- V1 backend skeleton, canonical domain, deterministic normalize→score→opportunity workflow.
- Policy/authorization and audit primitives.
- PostgreSQL baseline plus Telegram ingestion migrations.
- Telegram collection, deterministic parsing, canonicalization, atomic persistence/checkpointing and transactional outbox.
- Replay fixtures, PostgreSQL integration tests and optional OpenTelemetry.
- Hosted CI run `34502076880` green for the completed Telegram ingestion batch.
- Publication adapter contract and provider-neutral renderer.
- Publication policy gate for autonomy role, bounded markup, cancelled-load rejection and human approval for critical risk.
- Publication payload preserves source provenance and explicitly represents the role as `forwarder`.
- Durable outbox delivery state migration with attempts, availability time, leases and last-error metadata.
- Deterministic in-memory outbox lease/retry model and unit tests.
- PostgreSQL outbox claim/ack/failure worker with `FOR UPDATE SKIP LOCKED`, bounded retries and terminal quarantine timing.
- Market operations primitives: deterministic cost/price estimation, opportunity scoring, capacity matching and bounded negotiation policy.
- Commercial input validation now rejects negative cost components and invalid margin/negotiation boundaries.
- Market operations schema: observations, carrier profiles, opportunity matches, negotiation sessions and publication intents.
- Demand graph schema and deterministic customer-demand scoring/ranking tests.
- Demand geography bonus is awarded only when preferred countries are explicitly configured and matched.
- Official Lardi-Trans REST API client and read-only discovery adapter. Runtime secret is `LARDI_API_KEY`, with legacy `LARDI_TRANS_API_TOKEN` fallback.
- Lardi read-only manual smoke workflow and provider-neutral market-observation normalization/persistence service.
- Deterministic market price intelligence over normalized observations.
- Provider integration policy documents read-only discovery, provenance, idempotency and publication gating.

## Current implementation

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → bounded negotiation → PublicationRequest → PolicyEngine → PublicationAdapter → Outbox`

Market discovery now follows:

`Lardi API → provider boundary → MarketObservation → idempotent PostgreSQL persistence → price intelligence/demand analysis`

External provider network operations remain behind explicit adapters. No browser automation, anti-bot bypass or unsupported scraping is part of the core.

## Verification

- Hosted CI run `34502076880` passed the Telegram ingestion batch.
- Hosted CI runs `34518924173` (#72) and `34518944546` (#73) both passed package installation, PostgreSQL migrations and unit/integration tests.
- Latest demand test explicitly supplies `UA` when asserting the geography bonus; the test suite is green on the hosted PostgreSQL 17 workflow.
- Lardi smoke is intentionally `workflow_dispatch` only because it performs an external provider call.
- Lardi smoke is read-only, does not publish offers, negotiate or mutate provider data, and never prints the API key.
- Lardi-Trans official API documentation was reviewed: REST/JSON over HTTPS, token authorization, cargo/transport search, and Advanced API Access requirement for search.
- No claim is made that DELLA currently exposes an authorized automation interface.

## Next batch

1. Execute the manual Lardi read-only smoke workflow with `LARDI_API_KEY` and record whether Advanced API Access is enabled.
2. Add PostgreSQL integration tests for market-observation idempotency and freshness.
3. Extract canonical route/country/cargo/weight/price only from fields actually present in verified provider responses.
4. Add route economics and historical price trend analysis.
5. Add human review API/UI for negotiation and publication intents.
6. Activate external publication only after provider-specific permission and compliance verification.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed. Lardi credentials are read from `LARDI_API_KEY`, with `LARDI_TRANS_API_TOKEN` retained only as a compatibility fallback. The smoke workflow does not echo secrets.

## Compliance

Provider publication is gated and transport-neutral. No claim is made that any marketplace permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation. AI negotiation remains bounded and escalates critical risk to a human.

## Handoff

DONE: Commercial automation V3 implementation and hosted CI verification are green.
VERIFIED: Remote GitHub files, PostgreSQL migration/test execution and official PostgreSQL/Lardi documentation research.
NOT YET VERIFIED: Live Lardi provider permission/API response.
REQUIRED HUMAN ACTION: Run `Lardi read-only smoke` from GitHub Actions. If it returns an Advanced API Access/permission error, enable the required Lardi API package or provide the appropriate provider authorization before proceeding.
FILES: `migrations/0008_market_ops.sql`, `migrations/0009_demand_graph.sql`, `backend/logistics/market_ops.py`, `backend/logistics/lardi.py`, `backend/logistics/market_observations.py`, `backend/logistics/price_intelligence.py`, `backend/logistics/outbox_delivery.py`, `tests/test_market_ops.py`, `tests/test_lardi.py`, `tests/test_demand.py`, `tests/test_market_observations.py`, `scripts/lardi_smoke.py`, `.github/workflows/lardi-smoke.yml`, `docs/PROVIDER_INTEGRATIONS.md`.
COMMITS: latest implementation `bda9868e114a122a389eade1036b0cd2f4767f9c`; STATUS update follows this verification batch.
OPEN_ISSUES: Live Lardi provider permission validation remains open. DELLA transport remains intentionally unimplemented until an authorized current interface is verified.
