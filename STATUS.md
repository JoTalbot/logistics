# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Telegram load ingestion V1 hardening
STATUS: implemented_pending_runtime_ci
AGENT: telegram-load-ingestion-v1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Сбор Telegram-объявлений, детерминированный разбор, атомарная PostgreSQL persistence/checkpoint, validation/confidence gate, canonical Load persistence, transactional outbox, replay fixtures и optional OpenTelemetry. Публикация и наценка пока не входят в этот шаг.

## Completed

- Product vision, V1→V10 autonomy model, product specification, human workflow и distributed agent protocol.
- Техническая архитектура, roadmap и ecosystem/integration strategy.
- Routing/Geo/Optimization architecture: VROOM adapter candidate, OR-Tools advanced path, RoutingProvider, canonical geo pipeline, context-aware MatrixCache и replay benchmarks.
- V1 backend skeleton: canonical domain contracts, deterministic normalize→score→opportunity workflow.
- Event envelope, EventBus abstraction и outbox abstraction.
- Policy/authorization и audit primitives.
- PostgreSQL baseline schema для tenants, parties, loads, stops, opportunities, outbox и audit.
- Minimal FastAPI API and Docker Compose with PostgreSQL 17.
- Deterministic tests and backend implementation skill.
- Telegram ingestion: configured source chats, Telethon collection helper, deterministic parser, provenance envelope and parser tests.
- Telegram persistence: source checkpoints, source-message deduplication and parsed-ad storage with PostgreSQL UPSERT semantics.
- Telegram canonicalization: validation/confidence gate and ParsedLoadAd → canonical Load conversion.
- Telegram worker: checkpoint is advanced only inside the same DB transaction that persists source message and parsed result.
- GitHub Actions CI definition with PostgreSQL 17 service and clean SQL migration execution.
- Docker Compose fresh-database initialization includes Telegram migrations 0002 and 0003.
- Canonical Telegram loads with two stops are persisted transactionally for accepted ads.
- Durable LOAD_FOUND / LOAD_UPDATED outbox events are emitted transactionally and protected by idempotency keys.
- Deterministic Telegram replay fixtures cover accepted and rejected messages.
- Ingestion observability includes counters, structured logs and optional OpenTelemetry traces/metrics export.

## Current implementation

`Telegram message → deterministic parser → atomic source+parsed persistence → validation → canonical Load + load_stops → transactional outbox → checkpoint`

Incomplete/low-confidence ads remain non-canonical and are not published externally. No automatic markup or reposting is implemented in this stage.

## Verification

- Remote repository state confirmed through GitHub after each completed write.
- CI workflow exists and is configured for PostgreSQL 17, all three SQL migrations and pytest.
- The new push should trigger hosted CI automatically. Hosted CI result must be checked after the push before declaring runtime green.
- Local runtime execution is unavailable in the current environment.

## Telegram sources

- https://t.me/vantazhni_perevezennya_ua
- https://t.me/truck_world
- https://t.me/TURKIYA_UZBEKISTON_GRUBA_N1
- https://t.me/gruzoperevozki_ua

## Next batch

1. Verify the hosted CI run and fix any runtime failure it exposes.
2. Complete provider-specific publication adapters with provenance, role representation, markup and policy gates only after ingestion is runtime-green.
3. Add operational replay/benchmark reporting and outbox delivery worker hardening.
4. Continue toward demand discovery, carrier matching, pricing, negotiation and human-on-exception workflows.

## Security

`TG_API_ID` and `TG_API_HASH` remain runtime secrets. A Telethon user session is also a secret and must not be committed. No credentials are stored in the repository.

## Compliance

Telegram parsing remains deterministic/local. No LLM enrichment or AI/ML training pipeline is introduced. Production operation requires verification of source permissions, applicable platform terms, privacy/retention requirements and law.

## Handoff

DONE: Telegram parser, persistence, atomic checkpointing, canonical validation/conversion, canonical DB persistence, transactional outbox events, replay fixtures, worker orchestration, CI definition, fresh-DB Docker initialization and ingestion observability.
VERIFIED: Remote file state and repository writes.
NOT YET VERIFIED: Hosted CI execution result for this batch.
NEXT_STEP: Check hosted CI → fix runtime failures if any → publication adapters.
