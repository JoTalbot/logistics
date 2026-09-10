# Ecosystem and Integration Strategy

## Principles

External platforms are replaceable sources, not the product core. Every integration must have an adapter, capability declaration, health state, provenance, rate-limit handling, legal/ToS review and a fallback strategy where practical.

Priority order:

**Ukraine → nearby EU markets → wider Europe → other regions.**

## Tier 0 — Core infrastructure

| Capability | Initial approach | Priority |
|---|---|---|
| Database | PostgreSQL | P0 |
| Events | NATS/JetStream adapter | P0 |
| Durable workflows | Temporal adapter | P0 |
| Observability | OpenTelemetry | P0 |
| Object storage | S3-compatible | P0 |
| Identity/secrets | standard OIDC/secret-manager adapters | P0 |
| AI tools | MCP + internal tool contracts | P0 |
| Model providers | model gateway | P0 |

## Tier 1 — Ukraine

### Lardi-Trans

Use as a high-priority market source for loads, capacity, communication and other capabilities that are legally/API-accessible. The platform currently exposes a broad logistics ecosystem including search, AI-assisted data intake, leads, document workflows, tenders and API-related capabilities. Exact production integration must be revalidated against current provider terms and API access before implementation.

Adapter modules should be capability-specific rather than one giant provider client:

- `lardi.market`
- `lardi.contacts`
- `lardi.messaging`
- `lardi.documents`
- `lardi.tracking`
- `lardi.api`

### DELLA

Use as a second major Ukrainian market source. Separate ingestion/search from business decisions:

- load search;
- transport search;
- price observations/statistics where permitted;
- route-distance data where permitted;
- source freshness/availability.

Never make the domain layer depend on DELLA-specific object names.

### Maps and routing

Create a `RoutingProvider` contract supporting:

- route distance/time;
- alternative routes;
- restrictions;
- ETA;
- geocoding;
- reverse geocoding.

Use at least one primary and one fallback provider when economics justify it.

### Communications

Create channel-neutral contracts for:

- email;
- messaging platforms;
- SMS where needed;
- SIP/telephony;
- web chat.

### Documents

Start with object storage + OCR/document extraction abstraction. Add Ukrainian EDO, signing and insurance providers only after contract/API validation.

## Tier 2 — European freight exchanges

### Trans.eu

Candidate for major European expansion. Build an adapter around verified-company discovery, freight/capacity matching, messaging and TMS integration capabilities where commercially and technically available.

### Teleroute / Wtransnet

Treat Teleroute and Wtransnet as related but separately modeled providers. Build independent adapters even where access is through a common commercial ecosystem.

### Cargo.LT

Candidate for Central/Eastern European coverage and cross-border flows. Validate language, API/access model, pricing and legal requirements before enabling production automation.

### ATI.SU

Not a baseline dependency. Any future use requires an explicit legal, sanctions, counterparty and market-risk review for the jurisdictions involved. The architecture must work fully without it.

## Tier 3 — Enterprise ecosystem

Potential adapters, prioritized by proven business value:

- TMS/ERP systems;
- telematics/GPS providers;
- EDO/e-signature providers;
- insurance providers;
- payment and banking providers;
- factoring providers;
- KYC/KYB providers;
- accounting systems;
- CRM;
- email/calendar;
- customer portals;
- warehouse/terminal systems.

## Adapter contract

```python
class ProviderAdapter(Protocol):
    provider_id: str

    def capabilities(self) -> Capabilities: ...
    def health(self) -> ProviderHealth: ...
    def search(self, query: CanonicalSearchQuery) -> list[CanonicalOffer]: ...
    def get_entity(self, ref: ExternalRef) -> CanonicalEntity: ...
    def send(self, message: CanonicalMessage) -> DeliveryReceipt: ...
```

Production adapters additionally need:

- authentication;
- pagination;
- idempotency;
- rate limits;
- retries;
- webhooks/polling where allowed;
- provenance;
- clock/freshness metadata;
- capability/version detection;
- structured error taxonomy;
- circuit breaker;
- reconciliation.

## Integration qualification gate

No provider reaches autonomous production mode until all gates pass:

1. Official documentation/API verified.
2. Commercial terms verified.
3. ToS and automation permissions reviewed.
4. Authentication and secret handling verified.
5. Rate limits known.
6. Test/sandbox path identified where available.
7. Data fields mapped to canonical schema.
8. Failure/retry semantics tested.
9. Security/privacy review completed.
10. Provenance and audit implemented.
11. Provider failure fallback defined.
12. Unit economics proven.

## Integration maturity levels

| Level | Meaning |
|---|---|
| L0 | Researched only |
| L1 | Read-only/manual-assisted |
| L2 | Automated ingestion |
| L3 | Automated low-risk actions |
| L4 | Bounded autonomous workflows |
| L5 | Critical production integration with continuous monitoring |

A provider may be L5 for ingestion while remaining L1 for outbound actions. Capability maturity is not provider-wide.

## Current research anchors

- Lardi-Trans official site and API/product documentation.
- DELLA official site and available product/API information.
- Trans.eu official freight exchange documentation.
- Teleroute/Wtransnet official product documentation.
- Cargo.LT official product information.
- OpenAI Agents SDK documentation for agent/tool orchestration. citeturn0search8
- MCP 2026-07-28 specification and SDK ecosystem. citeturn0search6turn0search18

## Rule for future providers

Never add an integration because it is technically interesting. Add it when expected incremental profit, coverage, resilience or risk reduction justifies integration and maintenance cost.
