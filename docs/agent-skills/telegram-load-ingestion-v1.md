# Telegram Load Ingestion V1

## Goal
Collect configured Telegram load advertisements and turn them into deterministic structured `ParsedLoadAd` records. Publication, markup, negotiation and outbound posting are explicitly out of scope for this step.

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
V1 uses deterministic local regex parsing only. Do not send Telegram content to an LLM or external enrichment service. Keep the original source chat/message id and raw text for audit/replay where retention is permitted.

## Pipeline
`Telegram message -> source envelope -> deterministic parser -> ParsedLoadAd -> future validation/dedup -> future canonical Load`

## Required parser fields
Route, weight, volume, price/currency, cargo/vehicle hints, loading date text, phone numbers, source provenance, raw text and parser confidence.

## Operational rules
- Read incrementally using per-chat message ids.
- Deduplicate by `(source_chat, message_id)` before any future publication step.
- Treat parser confidence as a routing signal, not proof of correctness.
- Never auto-publish parsed content in V1.
- Respect Telegram API/content terms and source-specific rules.
