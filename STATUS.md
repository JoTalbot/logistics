# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Market intelligence V4 — historical prices, route economics and human review
STATUS: ci_green_pending_lardi_smoke
AGENT: logistics-commercial-batch-v4
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Historical market observations, freshness, verified provider-field extraction, route economics, price trends and authenticated human review. No autonomous external commitment is enabled.

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
- Commercial input validation rejects negative cost components and invalid margin/negotiation boundaries.
- Market operations schema: observations, carrier profiles, opportunity matches, negotiation sessions and publication intents.
- Demand graph schema and deterministic customer-demand scoring/ranking tests.
- Demand geography bonus is awarded only when preferred countries are explicitly configured and matched.
- Official Lardi-Trans REST API client and read-only discovery adapter. Runtime secret is `LARDI_API_KEY`, with legacy `LARDI_TRANS_API_TOKEN` fallback.
- Lardi read-only manual smoke workflow and provider-neutral market-observation normalization/persistence service.
- Deterministic market price intelligence over normalized observations.
- Provider integration policy documents read-only discovery, provenance, idempotency and publication gating.
- Append-only `market_observation_history` with timestamped provider snapshots.
- Stale market observations cannot overwrite a newer current observation.
- Explicit verified-field allowlist for provider-to-canonical extraction.
- Deterministic route economics with direct cost, risk reserve, clean profit and risk-adjusted profit.
- Historical price trend bucketing and conservative recommended-price floor.
- Durable `review_audit` records and explicit approve/reject/hold review service.
- Authenticated human review API protected by `REVIEW_OPERATOR_TOKEN`; approval changes internal state only and never calls a provider.
- Docker Compose fresh-database initialization now includes the complete migration chain, including legacy duplicate migration sequence numbers through ordered destination aliases.
- Unit and PostgreSQL integration coverage for V4 market-intelligence and review controls.

## Current implementation

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → bounded negotiation → PublicationRequest → PolicyEngine → PublicationAdapter → Outbox`

Market discovery now follows:

`Lardi API → provider boundary → MarketObservation → current state + immutable history → price intelligence → route economics → explainable recommendation`

Human exception path:

`Negotiation/Publication intent → authenticated review queue → approve/reject/hold → durable review audit`

External provider network operations remain behind explicit adapters. No browser automation, anti-bot bypass or unsupported scraping is part of the core.

## Verification

- Hosted CI Run #88 `34519826715` passed after the complete V4 batch: package installation, PostgreSQL migrations including `0010_market_intelligence.sql`, unit tests and integration tests.
- Job `103014265836` completed successfully; migration and test steps both passed.
- V4 route-economics, freshness/history, verified-field and review tests are included in the green run.
- Lardi smoke is intentionally `workflow_dispatch` only because it performs an external provider call.
- Lardi smoke is read-only, does not publish offers, negotiate or mutate provider data, and never prints the API key.
- Lardi-Trans official API documentation was reviewed: REST/JSON over HTTPS, token authorization, cargo/transport search, and Advanced API Access requirement for search.
- No claim is made that DELLA currently exposes an authorized automation interface.

## Next batch

1. Execute the manual Lardi read-only smoke workflow with `LARDI_API_KEY` and record the actual Advanced API Access/permission result.
2. After verified provider responses, add provider-specific canonical route/country/cargo/weight/price mappings without guessing field semantics.
3. Connect historical price trends and route economics to opportunity scoring and explainable recommendations.
4. Add review queue metrics/dashboard presentation and audit reporting.
5. Activate external publication only after provider-specific permission, commercial terms, privacy/retention and legal compliance are explicitly verified.
6. Expand to the next permitted market source only after the same adapter/provenance/compliance gate.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed. Lardi credentials are read from `LARDI_API_KEY`, with `LARDI_TRANS_API_TOKEN` retained only as a compatibility fallback. The smoke workflow does not echo secrets. Review API access requires `REVIEW_OPERATOR_TOKEN` and is disabled when it is not configured.

## Compliance

Provider publication is gated and transport-neutral. No claim is made that any marketplace permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation. AI negotiation remains bounded and escalates critical risk to a human.

## Handoff

DONE: Market Intelligence V4 implementation and hosted CI verification — historical observations, freshness, verified-field extraction, route economics, price trends and authenticated human review.
VERIFIED: Remote GitHub state and hosted CI Run #88.
NOT YET VERIFIED: Live Lardi provider permission/API response.
REQUIRED HUMAN ACTION: Run `Lardi read-only smoke` from GitHub Actions. If it returns an Advanced API Access/permission error, enable the required Lardi API package or provide the appropriate provider authorization before proceeding.
FILES: `migrations/0010_market_intelligence.sql`, `backend/logistics/market_observations.py`, `backend/logistics/route_economics.py`, `backend/logistics/review.py`, `backend/logistics/api.py`, `tests/test_market_observations.py`, `tests/test_market_observations_integration.py`, `tests/test_route_economics.py`, `tests/test_review.py`, `docker-compose.yml`, `docs/PROVIDER_INTEGRATIONS.md`, `docs/agent-log/commercial-batch-v4/2026-09-10.md`.
COMMITS: latest verified `d9c1de51610c421bf211e4ad2049ab2ff3501b32`; V4 implementation files were committed before this STATUS verification commit.
OPEN_ISSUES: Live Lardi provider permission validation remains open. DELLA transport remains intentionally unimplemented until an authorized current interface is verified.
