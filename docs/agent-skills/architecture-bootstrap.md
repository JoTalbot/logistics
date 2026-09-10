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

## Preferred V1 candidates

- PostgreSQL for transactional state.
- NATS/JetStream behind an EventBus interface.
- Temporal behind a Workflow interface.
- OpenTelemetry for telemetry.
- MCP where its tool/resource protocol is an appropriate integration surface.
- Modular monolith + workers before service decomposition.

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

## Known pitfalls

- Do not make external provider schemas domain schemas.
- Do not let model responses mutate business state without policy enforcement.
- Do not introduce microservices merely for architectural aesthetics.
- Do not make one exchange, model, map, voice or GPS provider a hard dependency.
- Do not enable autonomous critical actions before shadow/simulation and human escalation exist.

## Primary research sources

- OpenAI Developers / Agents SDK: https://developers.openai.com/
- MCP: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- Temporal: https://docs.temporal.io/
- NATS: https://docs.nats.io/
- OpenTelemetry: https://opentelemetry.io/docs/
- PostgreSQL: https://www.postgresql.org/docs/17/ddl-rowsecurity.html
- Debezium: https://debezium.io/documentation/reference/transformations/outbox-event-router.html
