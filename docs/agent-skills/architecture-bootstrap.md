# Skill — architecture-bootstrap

## Purpose
Design and evolve the AI Logistics OS architecture while preserving business-domain independence from providers and AI vendors.

## Verified workflow

1. Read `AGENTS.md` and `STATUS.md`.
2. Inspect current repository/docs and recent changes.
3. Research official technology/provider documentation.
4. Check mature open-source patterns when relevant.
5. Record architecture decisions before implementation.
6. Prefer stable interfaces around external dependencies.
7. Keep V1 operationally simple; preserve V10 capability through contracts.
8. Verify, update status/log/skill, commit and push immediately.

## Architecture patterns

- Domain state is authoritative; AI output is a proposal/action request.
- Commands mutate state; events record facts.
- Transactional state + outbox provides reliable event publication.
- Durable workflows handle long-running processes, timers and recovery.
- Provider integrations are adapters with capability and health metadata.
- AI agents use authorized tools/domain commands rather than direct DB access.
- Simulation and shadow execution share domain commands with production but suppress external side effects.
- Observability correlation must connect tenant, workflow, agent, decision and business aggregate IDs.
- Business optimization is separate from physical route solving.
- Routing providers and optimization solvers are independently replaceable.
- Canonical address/geocoding pipelines preserve confidence, provenance and freshness.
- Matrix caches are context-aware optimization layers, never authoritative state.
- Routing benchmarks evaluate feasibility, quality, latency and business economics.

## Preferred V1 candidates

- PostgreSQL for transactional state.
- NATS/JetStream behind an EventBus interface.
- Temporal behind a Workflow interface.
- OpenTelemetry for telemetry.
- MCP where its tool/resource protocol is an appropriate integration surface.
- Modular monolith + workers before service decomposition.
- VROOM behind an OptimizationService interface for standard VRP workloads.
- OSRM/Valhalla behind a RoutingProvider interface for self-hosted routing/matrices where justified.
- OR-Tools behind the same optimization boundary for validated special cases.

## Routing design rules

- Never expose VROOM/OR-Tools/provider schemas as domain schemas.
- Do not encode the entire business objective in a routing solver.
- Validate solver feasibility before accepting a route.
- Feed route cost and feasibility back into profit/risk evaluation.
- Matrix cache fingerprints must include provider/version, map freshness, routing profile and time-dependent context when applicable.
- Local geographic datasets are deployment assets, not mandatory source-controlled dependencies.
- Use deterministic fake routing/solver implementations for unit and integration tests.

## Quality criteria

- Provider independence.
- Tenant isolation.
- Idempotent commands.
- Explicit authorization and risk policy.
- Auditability.
- Recoverability.
- Testability/replayability.
- Explainable business outcomes.
- No secrets in source control.
- Measurable optimization quality and regressions.

## Known pitfalls

- Do not make external provider schemas domain schemas.
- Do not let model responses mutate business state without policy enforcement.
- Do not introduce microservices merely for architectural aesthetics.
- Do not make one exchange, model, map, voice, GPS provider or solver a hard dependency.
- Do not enable autonomous critical actions before shadow/simulation and human escalation exist.
- Do not promise solver-level latency as end-to-end system SLA.
- Do not cache routing matrices using coordinates alone when routing context affects the result.

## Primary research sources

- OpenAI Developers / Agents SDK: https://developers.openai.com/
- MCP: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- Temporal: https://docs.temporal.io/
- NATS: https://docs.nats.io/
- OpenTelemetry: https://opentelemetry.io/docs/
- PostgreSQL: https://www.postgresql.org/docs/17/ddl-rowsecurity.html
- Debezium: https://debezium.io/documentation/reference/transformations/outbox-event-router.html
- VROOM: https://github.com/VROOM-Project/vroom
- OSRM: https://project-osrm.org/docs/v26.4.0/http/
- Valhalla: https://valhalla.github.io/valhalla/api/matrix/
- OR-Tools: https://developers.google.com/optimization/routing
