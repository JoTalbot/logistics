# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V1 domain/event skeleton
STATUS: done
AGENT: backend-v1-bootstrap
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Первый исполняемый backend-контур: canonical domain, events/outbox, policy/audit, deterministic routing/optimization, load workflow, PostgreSQL baseline и Compose.
WORK_AREA: backend/*; migrations/*; tests/*; docker/*
OWNER: none

## Product rollout

**Этап 1: Украина.** Начать с украинского рынка, DELLA + Lardi-Trans и минимально необходимого набора интеграций.

**Этап 2: расширение.** Подключать дополнительные источники и сервисы постепенно по мере доказанной экономической ценности.

**Этап 3: Европа и далее.** Добавлять Trans.eu, Teleroute/Wtransnet, Cargo.LT и другие подтверждённо полезные источники после проверки API, стоимости, юридических условий и интеграционной готовности. ATI.SU допускается только при отдельной юридической и санкционной проверке и не является базовой зависимостью.

Ядро продукта не должно быть привязано к одной стране, бирже, карте, AI-провайдеру, телефонии, GPS-поставщику или solver.

## Completed

- Product vision, V1→V10 autonomy model, product specification, human workflow и distributed agent protocol.
- Техническая архитектура, roadmap и ecosystem/integration strategy.
- Routing/Geo/Optimization architecture: VROOM adapter candidate, OR-Tools advanced path, RoutingProvider, canonical geo pipeline, context-aware MatrixCache и replay benchmarks.
- V1 backend skeleton: canonical domain contracts, deterministic normalize→score→opportunity workflow.
- Event envelope, EventBus abstraction и outbox abstraction.
- Policy/authorization и audit primitives.
- PostgreSQL baseline schema для tenants, parties, loads, stops, opportunities, outbox и audit.
- Minimal FastAPI API и Docker Compose с PostgreSQL 17.
- Deterministic tests и backend implementation skill.

## Current implementation

`load → normalize → score → opportunity → event`

External providers are not yet business truth. Deterministic adapters make replay/testing possible before autonomous external actions.

## Research applied

- FastAPI official database guidance.
- PostgreSQL official RLS/security documentation.
- NATS official documentation for future messaging adapter.
- OpenTelemetry Python official documentation for future telemetry.
- Existing project architecture, roadmap, routing design and agent protocol.

## Deferred hardening

- Transactional PostgreSQL repositories + Alembic lifecycle.
- Final PostgreSQL RLS role/session design.
- NATS/JetStream EventBus adapter.
- Production RoutingProvider and OptimizationService adapters.
- Full OpenTelemetry instrumentation.

## Next

1. Run CI/runtime tests and fix implementation issues.
2. Add transactional PostgreSQL repositories and Alembic lifecycle.
3. Add NATS/JetStream EventBus adapter without changing domain contracts.
4. Finalize RLS tenant isolation with the real DB role/session model.
5. Connect real routing/optimization adapters and replay benchmarks.

## Handoff

DONE: V1 domain/event skeleton implemented.
VERIFIED: Repository structure reviewed; deterministic tests added; implementation boundaries documented; remote commit will be verified after push.
RESEARCHED: FastAPI, PostgreSQL, NATS and OpenTelemetry official documentation plus existing project architecture.
FILES: `backend/`, `migrations/0001_initial.sql`, `tests/`, `docker/`, `docker-compose.yml`, `pyproject.toml`, `docs/agent-skills/backend-v1-bootstrap.md`, `docs/agent-log/backend-v1-bootstrap/2026-09-10-domain-event-skeleton.md`.
OPEN_ISSUES: Runtime CI, transactional persistence, final RLS model, broker adapter and real routing providers remain next-stage work.
NEXT_STEP: Runtime verification and transactional persistence.
