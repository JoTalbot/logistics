# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Telegram load ingestion V1
STATUS: implemented_pending_runtime_ci
AGENT: telegram-load-ingestion-v1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Сбор сообщений из заданных Telegram-источников и детерминированный разбор объявлений о грузах. Публикация и наценка намеренно не входят в этот шаг.
WORK_AREA: backend/logistics/telegram.py; tests/test_telegram_parser.py; docs/agent-skills/telegram-load-ingestion-v1.md; docs/agent-log/telegram-load-ingestion-v1/2026-09-10.md; pyproject.toml
OWNER: none

## Product rollout

**Этап 1: Украина.** Начать с украинского рынка, DELLA + Lardi-Trans и минимально необходимого набора интеграций.

**Этап 2: расширение.** Подключать дополнительные источники и сервисы постепенно по мере доказанной экономической ценности.

**Этап 3: Европа и далее.** Добавлять Trans.eu, Teleroute/Wtransnet, Cargo.LT и другие подтверждённо полезные источники после проверки API, стоимости, юридических условий и интеграционной готовности.

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
- Deterministic tests and backend implementation skill.
- Telegram ingestion V1: configured source chats, Telethon collection helper, deterministic parser, provenance envelope and parser tests.

## Current implementation

`Telegram message → deterministic parser → ParsedLoadAd`

The intermediate Telegram record is not yet a canonical business Load and is not published externally.

## Telegram sources

- https://t.me/vantazhni_perevezennya_ua
- https://t.me/truck_world
- https://t.me/TURKIYA_UZBEKISTON_GRUBA_N1
- https://t.me/gruzoperevozki_ua

## Deferred hardening / next

1. Run CI/runtime parser tests and fix implementation issues.
2. Add persistent source-message checkpoint/dedup storage.
3. Add canonical Load conversion + validation and confidence thresholds.
4. Add production worker/scheduler and observability.
5. Only after ingestion is reliable, design provider-specific publication adapters and markup/policy gates.
6. Keep Telegram parsing deterministic unless a legally compliant data/licensing path for AI/ML use is established.

## Security

`TG_API_ID` and `TG_API_HASH` remain runtime secrets. A Telethon user session is also a secret and must not be committed. No credentials are stored in the repository.

## Handoff

DONE: Telegram collection/parsing code and tests added.
VERIFIED: Source code and configuration changes committed to the remote repository in this batch.
NOT YET VERIFIED: Runtime CI execution in the current environment.
