# Provider integration policy

## Lardi-Trans

The repository contains an official REST API client and read-only market discovery adapter in `backend/logistics/lardi.py`.

Current provider documentation confirms:

- base API: `https://api.lardi-trans.com/v2`;
- authentication uses an `Authorization` token;
- cargo and transport search endpoints are available through the Public API;
- the search endpoints require the provider's Advanced API Access package;
- provider responses can change while the API remains under active development.

Runtime configuration uses the `LARDI_API_KEY` secret. The client retains `LARDI_TRANS_API_TOKEN` as a backward-compatible fallback for existing deployments. Credentials are never written to logs, payloads, tests or the repository.

The adapter does not scrape the website or automate browser controls. `.github/workflows/lardi-smoke.yml` is a manual, read-only smoke check and must not be used as a publication path.

## Market observations

Provider responses are converted at the boundary by `backend/logistics/market_observations.py`. The raw provider payload is retained for provenance, while canonical business fields must be extracted only through an explicit verified-field allowlist. The repository must not infer route, country, cargo, weight or price semantics merely because a similarly named JSON field happens to exist.

Current-state observations are idempotent by `(tenant_id, source, external_ref)`. Every distinct verified observation timestamp is also retained in `market_observation_history` for replay, freshness checks and historical price analysis. A stale response cannot overwrite a newer current observation.

## Route economics and pricing

`backend/logistics/route_economics.py` provides deterministic route economics: direct cost, risk reserve, clean profit, risk-adjusted profit, margin rate, historical market-price buckets and a conservative recommended-price floor. Market price never overrides the economic floor.

Historical trend analysis is advisory only. It does not authorize publication, negotiation or financial commitment.

## Human review

`backend/logistics/review.py` provides explicit approve/reject/hold transitions for publication intents and negotiation sessions. The API requires `REVIEW_OPERATOR_TOKEN` and records a durable `review_audit` entry. Review approval changes internal state only; it does not itself call an external provider.

## Publication

Publication remains policy-gated. A provider adapter may only be activated after verifying current API permissions, commercial terms, privacy/retention requirements and applicable law. No marketplace is treated as permitting automation merely because an endpoint exists.

## DELLA

No unsupported DELLA transport is implemented. The integration boundary remains provider-neutral until a current, authorized API or contractually permitted interface is verified.

## Runtime rules

1. Never commit provider credentials.
2. Keep provider payloads outside the canonical domain model until validated.
3. Apply tenant, authorization, risk and audit policy before consequential actions.
4. Respect 429 responses and provider-specific rate limits.
5. Persist source provenance and provider identifiers.
6. Treat provider APIs as replaceable adapters, not business logic.
7. Keep discovery read-only until publication authorization is explicitly verified.
8. Treat historical market data as observations, not truth; preserve timestamp and provenance.
9. Never turn an unverified provider field into a canonical business value.
