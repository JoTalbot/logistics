# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Architecture V1→V10 + ecosystem foundation
STATUS: done
AGENT: architecture-bootstrap
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Архитектура V1→V10, приоритетный roadmap и стратегия интеграций.
WORK_AREA: released; ownership освобождён
OWNER: none

## Product rollout

**Этап 1: Украина.** Начать с украинского рынка, DELLA + Lardi-Trans и минимально необходимого набора интеграций.

**Этап 2: расширение.** Подключать дополнительные источники и сервисы постепенно по мере доказанной экономической ценности.

**Этап 3: Европа и далее.** Добавлять Trans.eu, Teleroute/Wtransnet, Cargo.LT и другие подтверждённо полезные источники после проверки API, стоимости, юридических условий и интеграционной готовности. ATI.SU допускается только при отдельной юридической и санкционной проверке и не является базовой зависимостью.

Ядро продукта не должно быть привязано к одной стране, бирже, карте, AI-провайдеру, телефонии или GPS-поставщику.

## Completed

- Repository `JoTalbot/logistics` подключён.
- Product vision и V1→V10 autonomy model сохранены.
- Product specification сохранена в `docs/PRODUCT_SPEC.md`.
- Human workflow сохранён в `docs/HUMAN_WORKFLOW.md`.
- Distributed AI-agent operating protocol сохранён в `AGENTS.md`.
- Практический workflow агентов сохранён в `docs/AGENT_WORKFLOW.md`.
- Немедленный commit/push после логически завершённого шага закреплён в `AGENTS.md`.
- Техническая архитектура V1→V10 сохранена в `docs/ARCHITECTURE.md`.
- Приоритетный roadmap сохранён в `docs/ROADMAP.md`.
- Экосистема и стратегия интеграций сохранены в `docs/ECOSYSTEM_AND_INTEGRATIONS.md`.
- Research log и reusable architecture skill сохранены в `docs/agent-log/architecture-bootstrap/` и `docs/agent-skills/architecture-bootstrap.md`.

## Active

- Переход от документации к V1 domain/event skeleton.

## Parallel Work Areas

| Area | Owner | Status |
|---|---|---|
| docs/architecture | none | done |
| docs/product | initial-bootstrap | active |
| backend | unassigned | open |
| integrations | unassigned | open |
| ai-agents | unassigned | open |
| voice | unassigned | open |
| risk | unassigned | open |
| finance | unassigned | open |
| frontend | unassigned | open |
| infrastructure | unassigned | open |

## Research completed

- OpenAI Agents SDK: orchestration, guardrails, results/state and observability.
- MCP specification 2026-07-28: stateless core, routing, authorization hardening, tasks/extensions.
- Temporal: durable execution and crash-resume workflows.
- NATS/JetStream: event-driven messaging and durable streams.
- OpenTelemetry: vendor-neutral traces, metrics and logs.
- PostgreSQL Row-Level Security: multi-tenant isolation primitive.
- Debezium Outbox: reliable state-to-event consistency pattern.

## Architecture decisions

- PostgreSQL is the transactional system of record for V1.
- Event-driven boundaries are first-class; transactional changes use an outbox pattern.
- NATS/JetStream is the initial event transport candidate, isolated behind an event-bus interface.
- Temporal is the initial durable workflow candidate for long-running business processes, isolated behind workflow interfaces.
- MCP is the preferred tool/integration protocol where it fits, but external providers remain behind explicit adapters.
- OpenTelemetry is the observability standard.
- Multi-tenancy is enforced at application and database layers, including PostgreSQL RLS where appropriate.
- AI agents never bypass domain services or authorization to mutate business state directly.
- V1 starts as a modular monolith plus workers; service decomposition is earned by scaling/ownership/reliability needs.
- Simulation/shadow mode precedes dangerous autonomous external actions.

## Next

1. Bootstrap V1 repository skeleton.
2. Implement PostgreSQL domain migrations and canonical contracts.
3. Implement event envelope + outbox + EventBus interface.
4. Implement policy/authorization and audit primitives.
5. Implement deterministic `load → normalize → score → opportunity` workflow.
6. Add replay/simulation fixtures before real autonomous actions.

## Handoff

DONE: Architecture foundation, roadmap, ecosystem strategy, research log and architecture skill completed.
VERIFIED: All new files were written to `main` through GitHub and each returned a commit SHA.
RESEARCHED: Official OpenAI, MCP, Temporal, NATS, OpenTelemetry, PostgreSQL and Debezium documentation.
FILES: `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/ECOSYSTEM_AND_INTEGRATIONS.md`, `docs/agent-log/architecture-bootstrap/2026-09-10-architecture-foundation.md`, `docs/agent-skills/architecture-bootstrap.md`, `STATUS.md`.
COMMITS: `9f3dffa753611dd6b288a511cb86f1c15d57660b`, `11abd440baaf739f56ccff3631e0495b09d9fa4a`, `f2411530cf908816b0e06d5cf5e9621ab7cfd9e6`, `92b6ad36f338064c00edf85e9017bfe86264abe2`, `cc5faac6b27bcec6ed34081402b131d4fff22ab4`, `bca4c24b670f21b30dd39dcf1604d1e17fec5d5a`.
OPEN_ISSUES: Exact provider contracts, legal terms, API versions and production sizing must be revalidated during each implementation step.
NEXT_STEP: V1 domain/event skeleton.
