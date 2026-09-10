# Backend V1 skeleton

The first implementation keeps the business core deliberately small and deterministic:

`load -> normalize -> score -> opportunity -> event`

## Boundaries

- `domain.py`: canonical domain contracts only.
- `optimization.py`: deterministic offline routing/optimization substitutes. Production providers remain adapters.
- `events.py`: versioned event envelope and EventBus abstraction.
- `outbox.py`: durable-outbox contract plus in-memory test implementation.
- `policy.py`: risk-aware authorization and audit primitives.
- `workflow.py`: deterministic V1 application flow.

The database migration contains tenant, party, load, stop, opportunity, outbox and audit state. PostgreSQL Row-Level Security is intentionally a follow-up hardening step because tenant isolation must be designed together with the final database role model.

## Run

```bash
docker compose up --build
```

API health: `GET /health`.

## Test

```bash
python -m pytest
```
