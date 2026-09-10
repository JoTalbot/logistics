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

Provider responses are converted at the boundary by `backend/logistics/market_observations.py`. The adapter preserves provider-specific fields inside the observation payload instead of inventing canonical business values. Stable provider identifiers are used for idempotent persistence; responses without an identifier receive a deterministic content hash.

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
