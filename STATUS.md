# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Customer discovery V1 — provenance-first discovery core
STATUS: ci_pending_customer_discovery
AGENT: logistics-commercial-batch-v4
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery foundations. No autonomous external commitment or outreach is enabled.

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
- Docker Compose fresh-database mount for migration `0011_opportunity_recommendations.sql`.
- Provenance-first customer discovery core with explicit permitted-source validation and no-fetch/no-scrape boundary.
- Customer discovery skill defining Organization/Facility/DemandSignal/BusinessContact/CustomerOpportunity/DiscoverySource boundaries and opt-out/compliance requirements.
- Unit coverage for discovery provenance, permission and validation rules.

## Current implementation

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → bounded negotiation → PublicationRequest → PolicyEngine → PublicationAdapter → Outbox`

Market discovery:

`Lardi API → provider boundary → MarketObservation → current state + immutable history → price intelligence → route economics → explainable recommendation → persisted Opportunity → operator review`

Customer discovery:

`Permitted source adapter → provenance-first Prospect → qualification → authorized contact → first load → recurring customer`

The discovery core deliberately does not fetch websites, scrape pages, harvest contact lists, send messages or perform opaque third-party enrichment.

Human exception path:

`Negotiation/Publication intent → authenticated review queue → approve/reject/hold → durable review audit`

External provider network operations remain behind explicit adapters. No browser automation, anti-bot bypass or unsupported scraping is part of the core.

## Verification

- Hosted CI Run #101 `34520924164` passed on the persisted-recommendation/status head.
- Review-reporting and customer-discovery commits are on `main`; a hosted CI run has been triggered and remains pending verification.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical route/country/cargo/weight/price mapping remains blocked until a verified provider response is obtained. No field semantics are inferred from guessed JSON names.

## Next batch

1. Verify customer-discovery and review-reporting CI, including PostgreSQL integration coverage.
2. Add durable customer discovery/prospect persistence with provenance, freshness and suppression/opt-out state.
3. Build deterministic qualification and customer-opportunity scoring from permitted signals.
4. Add authorized contact-channel adapters without autonomous outreach activation.
5. Add provider-specific canonical mappings from verified Lardi response samples after provider access is restored.
6. Re-run Lardi read-only smoke only after provider support confirms the edge block is resolved or supplies an authorized API path.
7. Activate external publication only after provider-specific permission, commercial terms, privacy/retention and legal compliance are explicitly verified.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed. Lardi credentials are read from `LARDI_API_KEY`, with `LARDI_TRANS_API_TOKEN` retained only as a compatibility fallback. The smoke workflow does not echo secrets. Review API access requires `REVIEW_OPERATOR_TOKEN` and is disabled when it is not configured.

## Compliance

Provider publication is gated and transport-neutral. Customer discovery uses only explicitly permitted source workflows and preserves provenance. Contact is a separate authorized stage with suppression/opt-out controls. No claim is made that any marketplace or source permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation.

## Handoff

DONE: Market-intelligence foundations, recommendation persistence, operator reporting and provenance-first customer-discovery core.
VERIFIED: Hosted CI Run #101 `34520924164` for the prior head.
PENDING: Hosted CI for the current review-reporting/customer-discovery head.
REQUIRED HUMAN ACTION: Lardi provider/support action is required before another live smoke. No repository-secret change is required.
OPEN_ISSUES: Live Lardi provider permission/API response; provider-specific field mapping; durable prospect persistence/qualification; authorized contact adapters; external publication remains gated.
