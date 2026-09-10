# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Market intelligence V4 — provider diagnostics and review operations
STATUS: ci_pending_after_v4_hardening
AGENT: logistics-commercial-batch-v4
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Historical market observations, freshness, verified provider-field extraction, route economics, price trends, provider diagnostics and authenticated human review. No autonomous external commitment is enabled.

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
- Lardi smoke diagnostics now distinguish provider-edge blocks from credential, permission and rate-limit failures.

## Current implementation

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → bounded negotiation → PublicationRequest → PolicyEngine → PublicationAdapter → Outbox`

Market discovery:

`Lardi API → provider boundary → MarketObservation → current state + immutable history → price intelligence → route economics → explainable recommendation`

Human exception path:

`Negotiation/Publication intent → authenticated review queue → approve/reject/hold → durable review audit`

Review operations:

`authenticated operator → queue/metrics → explicit decision → internal state + audit`

External provider network operations remain behind explicit adapters. No browser automation, anti-bot bypass or unsupported scraping is part of the core.

## Verification

- Hosted V4 CI Run #88 `34519826715` passed: package installation, PostgreSQL migrations, unit tests and integration tests.
- Manual Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; Actions confirmed the API secret was present and masked. The result is classified as a provider-edge block requiring provider-side action, not as a credential failure.
- No retry loop or bypass mechanism was added.
- A fresh hosted CI run is pending for the post-smoke diagnostics and review-metrics hardening commits.

## Provider status

Lardi discovery remains read-only. Canonical route/country/cargo/weight/price mapping remains blocked until a verified provider response is obtained. No field semantics are inferred from guessed JSON names.

## Next batch

1. Re-run Lardi read-only smoke only after provider support confirms the edge block is resolved or supplies an authorized API access path.
2. After verified provider responses, add provider-specific canonical route/country/cargo/weight/price mappings.
3. Connect historical price trends and route economics to opportunity scoring and explainable recommendations.
4. Add review dashboard presentation and audit reporting around the metrics endpoint.
5. Activate external publication only after provider-specific permission, commercial terms, privacy/retention and legal compliance are explicitly verified.
6. Expand to the next permitted market source only after the same adapter/provenance/compliance gate.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed. Lardi credentials are read from `LARDI_API_KEY`, with `LARDI_TRANS_API_TOKEN` retained only as a compatibility fallback. The smoke workflow does not echo secrets. Review API access requires `REVIEW_OPERATOR_TOKEN` and is disabled when it is not configured.

## Compliance

Provider publication is gated and transport-neutral. No claim is made that any marketplace permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation. AI negotiation remains bounded and escalates critical risk to a human.

## Handoff

DONE: V4 market-intelligence foundations plus provider-edge diagnostics and review queue metrics.
VERIFIED: Remote GitHub state and Lardi smoke Run `34519177888` provider-edge result.
PENDING: Hosted CI for commits after Run #88.
REQUIRED HUMAN ACTION: Lardi provider/support action is required before another live smoke. No action is required on repository secrets; `LARDI_API_KEY` is already being supplied to the workflow.
OPEN_ISSUES: Live Lardi provider permission/API response; DELLA transport remains intentionally unimplemented until an authorized current interface is verified.
