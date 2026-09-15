# Telegram Commercial Discovery V1

## Purpose

Connect the existing Telegram ingestion/parsing contour to the existing commercial scoring contour without enabling external autonomous actions.

## Flow

`TelegramSourceMessage[]` → deterministic parser → validation → canonical `Load[]` → price estimate → opportunity score → carrier matching → recurring-demand signal → priority ranking → evidence digest.

## Acceptance rules

An ad becomes a canonical load only when origin, destination, cargo type, weight, positive price, 3-letter currency and parser confidence meet the validation gate. Rejected ads remain visible in the report with explicit reasons.

## Safety boundary

This module is evidence-only. It does not send messages, publish loads, negotiate, sign contracts, change prices, make bookings, or execute financial operations. Lardi/Cloudflare protections are not bypassed.

## Determinism

Parsing and candidate construction use the repository's deterministic components. `candidate_digest()` exposes stable business fields suitable for an API, dashboard, or later evidence fingerprinting.

## Operational next step

Run the orchestration against authenticated, authorized Telegram sources and persist accepted records through `TelegramIngestionStore.ingest_message()`. Only after real operational data exists should commercial calibration be promoted beyond fixture validation.
