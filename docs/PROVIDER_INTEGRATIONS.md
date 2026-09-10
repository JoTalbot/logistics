# Provider integration policy

## Lardi-Trans

The repository now contains an official REST API client and read-only market discovery adapter in `backend/logistics/lardi.py`.

Current provider documentation confirms:

- base API: `https://api.lardi-trans.com/v2`;
- authentication uses an `Authorization` token;
- cargo and transport search endpoints are available through the Public API;
- the search endpoints require the provider's Advanced API Access package;
- provider responses can change while the API remains under active development.

The adapter therefore requires an explicit `LARDI_TRANS_API_TOKEN` runtime secret and does not scrape the website or automate browser controls.

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
