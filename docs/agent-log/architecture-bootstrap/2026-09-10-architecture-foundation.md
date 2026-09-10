# Architecture Bootstrap Log — 2026-09-10

## Task
Turn the agreed AI Logistics OS concept into a concrete V1→V10 architecture, roadmap and integration strategy.

## Research

Official/current research completed before implementation:

- OpenAI Developers / Agents SDK: orchestration, guardrails, state/results, integrations and observability.
- MCP 2026-07-28: stateless protocol core, routing, authorization hardening, tasks/extensions and current SDK line.
- Temporal: durable execution and recovery after failures.
- NATS: event messaging and JetStream concepts.
- OpenTelemetry: traces, metrics and logs with vendor-neutral instrumentation.
- PostgreSQL RLS: database-level row security for tenant/user isolation.
- Debezium Outbox: reliable DB-state/event publication pattern.

## Decisions

1. PostgreSQL is the V1 transactional source of truth.
2. Event-driven architecture is first-class, with outbox for reliable publication.
3. NATS/JetStream is the initial event transport candidate behind an internal abstraction.
4. Temporal is the initial durable workflow candidate behind a workflow abstraction.
5. MCP is preferred for compatible tool/integration surfaces, but provider adapters remain explicit and policy-controlled.
6. OpenTelemetry is the common observability layer.
7. Agents cannot mutate business state directly; they invoke authorized domain commands/tools.
8. V1 should be a modular monolith plus workers, not premature microservices.
9. Simulation/shadow mode is required before dangerous autonomous operations.
10. Ukraine is the first market; country/provider independence remains a core invariant.

## Files

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/ECOSYSTEM_AND_INTEGRATIONS.md`
- `STATUS.md`

## Verification

- Repository state read before work.
- `AGENTS.md` and `STATUS.md` read.
- Research gate completed.
- Documentation committed directly to `main` through GitHub.
- Commits: `9f3dffa753611dd6b288a511cb86f1c15d57660b`, `11abd440baaf739f56ccff3631e0495b09d9fa4a`, `f2411530cf908816b0e06d5cf5e9621ab7cfd9e6`, `92b6ad36f338064c00edf85e9017bfe86264abe2`.

## Lessons

- Keep technology choices behind interfaces so the business domain survives provider changes.
- Use durable workflows only where durability is needed; ordinary service calls remain simpler.
- Treat AI as a policy-governed actor, not as a database authority.
- Integration maturity must be capability-specific, not provider-wide.
- The first implementation should prove a measurable business loop before expanding infrastructure.

## Next

Bootstrap the V1 domain/event skeleton, migrations, policy service and deterministic `load → normalize → score → opportunity` workflow.
