# Backend implementation skill

## Verified V1 pattern

- Keep canonical Pydantic domain models independent from provider payloads.
- Use deterministic fakes for routing and optimization so replay and unit tests do not require external services.
- Carry tenant, actor, correlation and causation identifiers through commands/events.
- Treat the outbox as the durable publication boundary; do not make an external broker the source of business truth.
- Gate autonomous/critical actions through a policy decision and write an audit record for the decision.
- Keep the first workflow deterministic: normalize addresses, calculate a conservative route estimate, score risk-adjusted margin, emit an event.

## Quality gates

- Python 3.10+ compatibility.
- Domain contracts validate malformed inputs.
- Same fixture produces same opportunity score.
- Event envelope has explicit schema version and correlation metadata.
- SQL has tenant foreign keys and indexes for operational queries.
- No credentials in repository.

## Follow-ups

- Replace in-memory outbox with transactional PostgreSQL implementation.
- Add Alembic migration lifecycle around the SQL baseline.
- Add PostgreSQL RLS after final DB role/session design.
- Add NATS/JetStream EventBus adapter without changing domain events.
- Add real RoutingProvider and OptimizationService adapters behind the existing boundaries.
