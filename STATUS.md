# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Telegram load ingestion V1
STATUS: implemented_pending_runtime_ci
AGENT: telegram-load-ingestion-v1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Сбор сообщений из заданных Telegram-источников, идемпотентное сохранение, checkpoint/dedup, детерминированный разбор и безопасная канонизация объявлений о грузах. Публикация и наценка намеренно не входят в этот шаг.

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
- Telegram ingestion: configured source chats, Telethon collection helper, deterministic parser, provenance envelope and parser tests.
- Telegram persistence: source checkpoints, source-message deduplication and parsed-ad storage with PostgreSQL UPSERT semantics.
- Telegram canonicalization: validation/confidence gate and ParsedLoadAd → canonical Load conversion.
- Telegram worker: checkpoint is advanced only inside the same DB transaction that persists source message and parsed result.

## Current implementation

`Telegram message → deterministic parser → atomic source+parsed persistence → checkpoint → validation → canonical Load`

Incomplete/low-confidence ads remain non-canonical and are not published externally. No automatic markup or reposting is implemented in this stage.

## Telegram sources

- https://t.me/vantazhni_perevezennya_ua
- https://t.me/truck_world
- https://t.me/TURKIYA_UZBEKISTON_GRUBA_N1
- https://t.me/gruzoperevozki_ua

## Next

1. Runtime CI and PostgreSQL integration execution.
2. Add observability counters/traces and deterministic replay fixtures.
3. Add canonical Load persistence and event publication after validation.
4. Add provider-specific publication adapters only after ingestion is reliable, with explicit provenance, role representation, markup and policy gates.
5. Keep Telegram parsing deterministic unless a legally compliant data/licensing path for AI/ML use is established.

## Security

`TG_API_ID` and `TG_API_HASH` remain runtime secrets. A Telethon user session is also a secret and must not be committed. No credentials are stored in the repository.

## Handoff

DONE: Telegram parser, persistence, atomic checkpointing, canonical validation/conversion and worker orchestration.
VERIFIED: All changes in this batch were written to the remote repository.
NOT YET VERIFIED: Runtime CI/database integration execution in the current environment.
