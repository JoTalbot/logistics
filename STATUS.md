# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Routing/Geo/Optimization architecture extension
STATUS: done
AGENT: architecture-bootstrap
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Интеграция полезных идей из анализа открытых TMS/VRP-решений в архитектуру.
WORK_AREA: released; ownership освобождён
OWNER: none

## Product rollout

**Этап 1: Украина.** Начать с украинского рынка, DELLA + Lardi-Trans и минимально необходимого набора интеграций.

**Этап 2: расширение.** Подключать дополнительные источники и сервисы постепенно по мере доказанной экономической ценности.

**Этап 3: Европа и далее.** Добавлять Trans.eu, Teleroute/Wtransnet, Cargo.LT и другие подтверждённо полезные источники после проверки API, стоимости, юридических условий и интеграционной готовности. ATI.SU допускается только при отдельной юридической и санкционной проверке и не является базовой зависимостью.

Ядро продукта не должно быть привязано к одной стране, бирже, карте, AI-провайдеру, телефонии, GPS-поставщику или solver.

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
- Экосистема и стратегия интеграций сохранена в `docs/ECOSYSTEM_AND_INTEGRATIONS.md`.
- Routing/optimization architecture сохранена в `docs/ROUTING_OPTIMIZATION.md`.

## Routing decisions

- VROOM выбран первоначальным general-purpose VRP solver candidate за внутренним `OptimizationService` adapter.
- OR-Tools сохранён как advanced/experimental solver для нестандартных ограничений и objective functions.
- `RoutingProvider` отделён от solver и поддерживает OSRM, Valhalla и коммерческие providers.
- Геокодирование проходит через canonical address pipeline с confidence, provenance и freshness.
- `MatrixCache` является необязательным оптимизационным слоем и использует полный context-aware fingerprint.
- Routing/solver benchmarks и historical replay добавлены в evaluation track.
- Локальные OSRM/Valhalla datasets являются deployment assets и не обязательны для минимального локального запуска.

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

## Next

1. Bootstrap V1 repository skeleton.
2. Implement PostgreSQL domain migrations and canonical contracts.
3. Implement event envelope + outbox + EventBus interface.
4. Implement policy/authorization and audit primitives.
5. Implement canonical geo/routing/optimization contracts and deterministic fakes.
6. Implement deterministic `load → normalize → score → opportunity` workflow.
7. Add replay/simulation fixtures before real autonomous actions.

## Handoff

DONE: Routing/geo/optimization architecture extension completed.
VERIFIED: New routing architecture was committed to `main`; existing architecture, roadmap and integration strategy were updated with current blob SHAs before writes.
FILES: `docs/ROUTING_OPTIMIZATION.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/ECOSYSTEM_AND_INTEGRATIONS.md`, `STATUS.md`.
COMMITS: `d9b7768fba4ffa57b58a4c0ddd13679bd0012b55`, `0eb6dc835e10e0dcac65528cbe05101b1b9ac40b`, `9dc905e3df4fb19136a595d3efdbdf7bd9deab00`, `88d4709313295ba208b214c18a89cc7b11ff3c73`.
OPEN_ISSUES: Exact provider contracts, legal terms, API versions and production sizing must be revalidated during each implementation step.
NEXT_STEP: V1 domain/event skeleton.
