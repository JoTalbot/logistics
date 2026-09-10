# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Architecture V1→V10 + ecosystem foundation
STATUS: researching
AGENT: architecture-bootstrap
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Превратить согласованную продуктовую концепцию в реализуемую V1→V10 архитектуру, roadmap и каталог интеграций.
WORK_AREA: docs/architecture/*; docs/ROADMAP.md; docs/ECOSYSTEM_AND_INTEGRATIONS.md
OWNER: architecture-bootstrap

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
- Правило немедленного commit/push после логически завершённого шага закреплено в `AGENTS.md`.

## Active

- Архитектура V1→V10.
- Приоритизированный roadmap.
- Каталог интеграций и integration-adapter strategy.
- Данные, события, агенты, governance, observability и disaster recovery.

## Parallel Work Areas

| Area | Owner | Status |
|---|---|---|
| docs/architecture | architecture-bootstrap | researching/implementing |
| docs/product | initial-bootstrap | active |
| backend | unassigned | open |
| integrations | unassigned | open |
| ai-agents | unassigned | open |
| voice | unassigned | open |
| risk | unassigned | open |
| finance | unassigned | open |
| frontend | unassigned | open |
| infrastructure | unassigned | open |

## Research gate completed for this step

- OpenAI Agents SDK: orchestration, guardrails, results/state and observability.
- MCP specification 2026-07-28: stateless core, routing, authorization hardening, tasks/extensions.
- Temporal: durable execution and crash-resume workflows.
- NATS/JetStream: event-driven messaging and durable streams.
- OpenTelemetry: vendor-neutral traces, metrics and logs.
- PostgreSQL Row-Level Security: multi-tenant isolation primitive.
- Debezium Outbox: reliable state-to-event consistency pattern.

## Decisions for this step

- PostgreSQL is the transactional system of record for V1.
- Event-driven boundaries are first-class; transactional changes use an outbox pattern.
- NATS/JetStream is the initial event transport candidate, isolated behind an event-bus interface.
- Temporal is the initial durable workflow candidate for long-running business processes, isolated behind workflow interfaces.
- MCP is the preferred tool/integration protocol where it fits, but external providers remain behind explicit adapters.
- OpenTelemetry is the observability standard.
- Multi-tenancy is enforced at application and database layers, including PostgreSQL RLS where appropriate.
- AI agents never bypass domain services or authorization to mutate business state directly.

## Next

1. Finish architecture documents and roadmap.
2. Add integration matrix and country rollout criteria.
3. Bootstrap V1 repository skeleton and domain contracts.
4. Implement simulation/shadow mode before autonomous real-world actions.

## Handoff

DONE: Research gate and architecture ownership established.
VERIFIED: Repository state and required operating instructions read before implementation.
RESEARCHED: Official OpenAI, MCP, Temporal, NATS, OpenTelemetry, PostgreSQL and Debezium documentation.
FILES: `STATUS.md` plus upcoming architecture/roadmap/integration documents.
COMMITS: Current status update followed by atomic documentation commits.
OPEN_ISSUES: Exact technology versions, provider contracts, legal terms and production sizing must be revalidated during implementation.
NEXT_STEP: Commit the architecture foundation, then move to V1 domain/event skeleton.
