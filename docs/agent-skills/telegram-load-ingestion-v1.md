# Telegram Load Ingestion V1

## Goal
Collect configured Telegram load advertisements and turn them into deterministic structured `ParsedLoadAd` records and, when validation passes, canonical `Load` records. Publication, markup, negotiation and outbound posting remain explicitly out of scope.

## Sources
- https://t.me/vantazhni_perevezennya_ua
- https://t.me/truck_world
- https://t.me/TURKIYA_UZBEKISTON_GRUBA_N1
- https://t.me/gruzoperevozki_ua

## Security
- `TG_API_ID` and `TG_API_HASH` are runtime secrets and must never be committed.
- A Telethon user session is required for authenticated history access. The session file/string is also a secret.
- Do not log session credentials or raw private data unnecessarily.

## Parsing policy
V1 uses deterministic local regex parsing only. Do not send Telegram content to an LLM or external enrichment service. Keep source chat/message id and raw text for audit/replay where retention is permitted.

## Pipeline
`Telegram message -> deterministic parser -> atomic source+parsed persistence -> checkpoint -> validation/confidence gate -> canonical Load`

The source message, parser result and checkpoint must commit together. A failed transaction must not advance the source checkpoint.

## Canonicalization gate
A `ParsedLoadAd` becomes a canonical `Load` only when it has origin, destination, cargo type, positive weight, positive price, 3-letter currency and sufficient parser confidence. Missing or low-confidence ads remain non-canonical and require later review/enrichment.

## Required parser fields
Route, weight, volume, price/currency, cargo/vehicle hints, loading date text, phone numbers, source provenance, raw text and parser confidence.

## Operational rules
- Read incrementally using per-chat message ids.
- Deduplicate by `(tenant_id, source_chat, message_id)`.
- Treat parser confidence as a routing signal, not proof of correctness.
- Never auto-publish parsed content in V1.
- Use PostgreSQL UPSERT semantics for retries.
- CI must exercise both Python tests and the SQL migration path.
- Respect Telegram API/content terms and source-specific rules.
