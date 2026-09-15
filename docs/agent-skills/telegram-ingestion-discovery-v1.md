# Telegram Ingestion → Commercial Discovery v1

## Purpose

V37 composes the authenticated Telegram collector, transactional persistence, and deterministic commercial discovery into one bounded batch operation.

## Flow

```text
Telegram client
  -> collect_messages()
  -> parse_load_ad()
  -> TelegramIngestionStore.ingest_message()
  -> canonical Load / outbox / checkpoint
  -> build_discovery_report()
  -> commercial candidates + evidence digest
```

The worker uses the messages collected in the current bounded invocation for the returned discovery report. PostgreSQL remains authoritative for durable source messages, canonical loads, outbox events, and checkpoints.

## Entry point

`backend/logistics/telegram_discovery_worker.py::run_ingestion_discovery_once`

Inputs:

- authenticated Telegram client;
- `TelegramIngestionStore`;
- tenant UUID;
- explicit Telegram chat allow-list;
- carrier inventory;
- deterministic `PricingInput`;
- bounded message limit.

Output:

- per-message ingestion results;
- deterministic `DiscoveryReport`;
- ranked commercial candidates.

## Operational guarantees

- Checkpoints are read before collection and advanced only by the existing transactional ingestion boundary.
- Duplicate source messages remain idempotent through the existing database constraints and event idempotency key.
- Parsing and ranking are deterministic and do not require an LLM.
- Empty batches return an empty evidence report without side effects beyond checkpoint reads.
- Exceptions are surfaced after the existing failure observer is called; partial messages are not silently swallowed.

## Safety boundary

This contour is **evidence-only**. It does not:

- publish loads to external exchanges;
- send messages or contact carriers;
- negotiate or contract;
- mutate prices;
- book capacity;
- execute financial actions;
- bypass Cloudflare, provider controls, or authentication boundaries.

Provider telemetry is not treated as proof of authorization or availability.

## Production activation

Live execution still requires authorized Telegram credentials and explicit source access. Provider-specific access such as Lardi remains an external gate. Fixture/integration tests validate the orchestration without pretending that provider access exists.
