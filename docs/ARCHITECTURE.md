# AI Logistics OS — Technical Architecture V1→V10

## 1. Architecture goal

Build an event-driven, multi-tenant, provider-agnostic logistics operating system whose first production scope is Ukraine and whose core can expand to Europe and other markets without rewriting the domain.

The system must support:

`Market → Price → Match → Negotiate → Deal → Contract → Dispatch → Track → Deliver → Invoice → Pay → Learn → Optimize`

The architecture deliberately separates **business state**, **AI reasoning**, **external integrations**, and **execution workflows**. AI may propose or execute only through authorized domain tools.

## 2. Reference architecture

```text
                    ┌──────────────────────────────┐
                    │          AI CEO / UI          │
                    │ strategy • operator • alerts  │
                    └──────────────┬───────────────┘
                                   │
                         Governance / Policy
                                   │
        ┌──────────────────────────┼─────────────────────────┐
        │                          │                         │
  Agent Supervisor          Risk / Trust              Simulation
        │                          │                  / Digital Twin
        └───────────────┬──────────┴───────────────┘
                        │
                 Domain Services
                        │
     ┌──────────────────┼───────────────────┐
     │                  │                   │
  Market/Price      Matching/Deal       Dispatch/Route
     │                  │                   │
     └──────────────────┼───────────────────┘
                        │
                PostgreSQL + Outbox
                        │
                 Event Bus / Stream
                        │
       ┌────────────────┼──────────────────────┐
       │                │                      │
   AI Workers       Workflows              Analytics
       │                │                      │
       └────────────────┼──────────────────────┘
                        │
              Adapter / Integration Layer
                        │
   DELLA • Lardi • TMS • Maps • GPS • Voice • Docs
   Payments • Insurance • EDO • Email • Messaging
```

## 3. Core technology choices

These are **architecture candidates**, not irreversible dependencies.

| Concern | V1 candidate | Rule |
|---|---|---|
| Transactional DB | PostgreSQL | System of record; tenant isolation; strong consistency |
| Event transport | NATS JetStream | Behind an internal EventBus interface |
| Durable workflows | Temporal | Long-running/retryable business processes behind Workflow interface |
| AI orchestration | OpenAI Agents SDK + internal Supervisor | Provider/model abstraction required |
| Tool protocol | MCP where appropriate | External adapters remain explicit and policy-controlled |
| Observability | OpenTelemetry | Vendor-neutral traces, metrics, logs |
| Cache | Redis-compatible abstraction | Never make cache authoritative |
| Object storage | S3-compatible abstraction | Documents/audio/evidence, encrypted |
| Search | PostgreSQL FTS initially; dedicated engine later | Avoid premature distributed search |

The current MCP specification is stateless at its protocol core, which is useful for horizontally scalable tool gateways. citeturn0search6 OpenAI's current Agents SDK documentation covers orchestration, guardrails, state/results and observability. citeturn0search8 Temporal is appropriate for workflows that must resume after crashes or infrastructure failures. citeturn0search1 NATS provides the initial event-streaming candidate. citeturn0search0

## 4. Domain boundaries

### 4.1 Tenant and identity

- Tenant/company
- User
- Role
- Permission
- API credential reference
- Agent identity
- Machine/runtime identity

### 4.2 Market

- Load offer
- Truck/capacity offer
- Market source
- Search query
- Market snapshot
- Price observation
- Market heatmap cell

### 4.3 Parties and Trust Graph

- Client
- Carrier
- Driver
- Vehicle
- Contact point
- Bank/payment identity
- Document identity
- Relationship edge
- Trust/risk observation

### 4.4 Deal lifecycle

- Opportunity
- Quote
- Negotiation
- Deal
- Contract
- Shipment
- Stop
- Assignment
- SLA
- Exception
- Delivery proof

### 4.5 Finance

- Cost estimate
- Revenue
- Margin
- Risk-adjusted margin
- Invoice
- Receivable
- Payment
- Factoring event
- Cash-flow projection
- Treasury position

### 4.6 Documents

- Document
- Document version
- Extraction
- Validation
- Signature state
- EDO transaction
- Evidence/provenance

## 5. Event model

Events are immutable facts, not commands. Commands request a state change; events record what actually happened.

Minimum event envelope:

```json
{
  "event_id": "uuid",
  "event_type": "LOAD_FOUND",
  "event_version": 1,
  "tenant_id": "uuid",
  "aggregate_type": "load",
  "aggregate_id": "uuid",
  "occurred_at": "timestamp",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "actor": {"type": "agent|user|system|provider", "id": "..."},
  "schema_version": "1.0",
  "payload": {}
}
```

Initial event families:

`LOAD_FOUND`, `LOAD_UPDATED`, `PRICE_OBSERVED`, `OPPORTUNITY_SCORED`, `CARRIER_MATCHED`, `NEGOTIATION_STARTED`, `MESSAGE_SENT`, `QUOTE_RECEIVED`, `DEAL_AGREED`, `CONTRACT_SIGNED`, `DOCUMENT_RECEIVED`, `TRUCK_ASSIGNED`, `TRUCK_DEPARTED`, `ETA_CHANGED`, `EXCEPTION_OPENED`, `DELIVERY_CONFIRMED`, `INVOICE_ISSUED`, `PAYMENT_RECEIVED`, `RISK_CHANGED`, `AGENT_ACTION_PROPOSED`, `AGENT_ACTION_APPROVED`, `AGENT_ACTION_EXECUTED`, `AGENT_ACTION_REJECTED`.

Use an outbox pattern for reliable publication of DB state changes to the event bus. Debezium documents the outbox pattern specifically for keeping persisted service state consistent with published events. citeturn0search11

## 6. Agent architecture

Agents are bounded specialists, not independent sources of truth.

```text
Supervisor
├── Scout Agent
├── Pricing Agent
├── Matching Agent
├── Carrier Intelligence Agent
├── Negotiator Agent
├── Voice Agent
├── Risk Agent
├── Contract/Document Agent
├── Dispatch Agent
├── Route/ETA Agent
├── Finance Agent
├── Incident Agent
├── Optimizer Agent
├── Forecasting Agent
└── AI CEO
```

Each agent has:

- identity and version;
- explicit capabilities/tools;
- allowed domains and tenants;
- risk class;
- budget/time limits;
- confidence threshold;
- escalation policy;
- audit trail;
- evaluation suite;
- rollback/compensation policy where possible.

Agents do not write directly to PostgreSQL tables. They call domain commands/tools, which enforce authorization, invariants, risk policy and audit logging.

## 7. Governance and action policy

Every consequential action is classified:

| Risk | Example | Default |
|---|---|---|
| R0 | Read/search/analyze | Autonomous |
| R1 | Draft message/quote | Autonomous draft |
| R2 | Send routine message within policy | Autonomous |
| R3 | Negotiation within approved limits | Autonomous with monitoring |
| R4 | Contract/financial commitment above threshold | Human approval |
| R5 | Legal, sanctions, identity or exceptional financial decision | Human/dual-control |

Policy evaluation occurs **before** tool execution and is recorded with the decision.

## 8. Data architecture

PostgreSQL is the transactional source of truth. Use normalized domain tables plus append-only audit/event records. Multi-tenancy uses application authorization plus database controls; PostgreSQL Row-Level Security can provide per-user/tenant row restrictions and defaults to deny when no policy permits access. citeturn0search9

Separate storage classes:

1. transactional data;
2. event/audit history;
3. documents/evidence;
4. analytical facts/features;
5. embeddings/vector indexes;
6. temporary AI context.

AI memory must never silently become authoritative business state.

## 9. Workflow architecture

Use durable workflows for processes that span minutes/hours/days or require retries, timers, callbacks and recovery:

- negotiation lifecycle;
- shipment lifecycle;
- document collection;
- payment follow-up;
- incident handling;
- carrier onboarding;
- human approval waits;
- recurring market scans.

Use ordinary service calls for short synchronous operations. This avoids turning every HTTP request into a distributed workflow circus, because humanity has already suffered enough distributed systems diagrams.

## 10. Integration architecture

Every provider is an adapter implementing stable internal contracts:

```text
ProviderAdapter
├── authenticate()
├── capabilities()
├── search_loads()
├── search_capacity()
├── get_entity()
├── send_message()
├── receive_events()
├── get_document()
└── health()
```

Adapters must expose capability discovery, rate limits, freshness, provenance and failure state. Provider-specific objects are mapped into canonical domain objects at the boundary.

## 11. AI/model gateway

Never couple domain logic directly to one model vendor.

The Model Gateway selects models based on:

- task class;
- latency budget;
- cost budget;
- required context window;
- structured-output requirement;
- reliability;
- privacy/data residency;
- fallback availability.

A decision record must capture model/provider/version and relevant policy metadata without storing secrets.

## 12. Simulation and shadow mode

Before autonomous external actions, the same domain commands must support:

- dry-run;
- shadow execution;
- replay from historical events;
- synthetic scenarios;
- counterfactual comparison;
- digital-twin simulation.

Simulation must answer: **what would the AI have done, what would it have earned, what risk would it have created, and what actually happened?**

## 13. Observability

OpenTelemetry is the standard instrumentation layer for traces, metrics and logs. It is vendor-neutral and designed to correlate telemetry across distributed components. citeturn0search2turn0search4

Required correlation IDs:

`tenant_id`, `workflow_id`, `correlation_id`, `causation_id`, `agent_id`, `decision_id`, `deal_id`, `shipment_id`.

Business metrics must include:

- gross margin;
- risk-adjusted margin;
- cost per AI action;
- negotiation conversion;
- deal rejection reasons;
- ETA accuracy;
- exception rate;
- human intervention rate;
- provider failure rate;
- cash conversion cycle.

## 14. Reliability

Every external integration has:

- timeout;
- retry with bounded backoff;
- idempotency key;
- circuit breaker;
- rate-limit handling;
- provider health score;
- fallback provider where feasible;
- dead-letter/reconciliation path.

Critical financial and shipment workflows must be recoverable after process/node/network failure.

## 15. Security

- Least privilege.
- Tenant isolation.
- Secret manager references only.
- Encryption in transit and at rest.
- Immutable audit trail for consequential actions.
- Explicit authorization for every tool.
- Prompt/tool injection defenses at integration boundaries.
- Malware/document scanning for uploaded files.
- PII minimization and retention policies.
- Sanctions/compliance checks before applicable transactions.

## 16. V1→V10 evolution

| Version | Architecture capability |
|---|---|
| V1 | Observe: integrations, normalized market data, CRM, audit |
| V2 | Recommend: pricing, matching, opportunity scoring |
| V3 | Safe actions: messages, data updates, routine workflows |
| V4 | Negotiation: bounded multi-channel negotiation |
| V5 | Deal autonomy: contracts/commitments inside policy |
| V6 | Operations: dispatch, GPS, ETA, exceptions |
| V7 | Network optimization: chains, backhaul, consolidation |
| V8 | Network control: capacity forecasting and marketplace |
| V9 | Profit/risk optimization: treasury, portfolio and strategy |
| V10 | AI CEO: strategic control with human exception/governance |

## 17. V1 deployment topology

Start as a modular monolith plus worker processes, not a microservice zoo.

```text
Web/API
  │
Application Core ─── PostgreSQL
  │                    └── Outbox
  ├── Worker Pool ─── NATS/JetStream
  ├── Workflow Worker ─ Temporal
  ├── Adapter Gateway
  ├── AI/Model Gateway
  └── OTel Collector
```

Split services only when scaling, security, ownership or reliability requires it. The interfaces must be service-ready from the beginning.

## 18. Non-negotiable architectural invariants

1. Domain state is authoritative; model output is not.
2. AI cannot bypass authorization/policy.
3. Every consequential action is auditable.
4. Every external provider is replaceable behind an adapter.
5. Every long-running process is recoverable.
6. Every autonomous action has limits and escalation.
7. Ukraine is the first market, not a permanent architecture constraint.
8. Simulation/shadow mode precedes dangerous autonomy.
9. Profit is optimized subject to risk and compliance constraints.
10. All completed engineering work is committed and pushed immediately according to `AGENTS.md`.
