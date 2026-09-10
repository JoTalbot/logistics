from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

import psycopg

from .telegram import ParsedLoadAd, TelegramSourceMessage
from .telegram_pipeline import parsed_ad_to_load, validate_parsed_ad


@dataclass(frozen=True)
class IngestionResult:
    source_message_id: UUID
    load_id: UUID | None
    accepted: bool
    duplicate: bool
    event_type: str | None


class TelegramIngestionStore:
    """PostgreSQL persistence boundary for Telegram ingestion and canonical loads."""

    def __init__(self, dsn: str):
        self.dsn = dsn

    @staticmethod
    def _event_key(source_message_id: UUID, event_type: str, payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
        return f"telegram:{source_message_id}:{event_type}:{digest}"

    @staticmethod
    def _load_payload(load, load_id: UUID, source_message_id: UUID) -> dict:
        return {
            "load_id": str(load_id),
            "source_message_id": str(source_message_id),
            "external_ref": load.external_ref,
            "cargo_type": load.cargo_type,
            "weight_kg": load.weight_kg,
            "offered_price": str(load.offered_price),
            "currency": load.currency,
            "status": load.status.value,
            "stops": [
                {
                    "sequence": stop.sequence,
                    "kind": stop.kind,
                    "raw_address": stop.location.raw_address,
                    "normalized_address": stop.location.normalized_address,
                    "latitude": stop.location.point.latitude if stop.location.point else None,
                    "longitude": stop.location.point.longitude if stop.location.point else None,
                    "confidence": stop.location.confidence,
                    "provenance": stop.location.provenance,
                }
                for stop in load.stops
            ],
        }

    def ingest_message(
        self, tenant_id: UUID, message: TelegramSourceMessage, parsed: ParsedLoadAd
    ) -> IngestionResult:
        """Persist source, parsed ad, canonical state, outbox and checkpoint atomically."""
        validation = validate_parsed_ad(parsed)
        canonical = parsed_ad_to_load(parsed, tenant_id=tenant_id) if validation.accepted else None

        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """
                INSERT INTO telegram_source_messages
                    (tenant_id, source, message_id, message_url, published_at, raw_text, has_media)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, source, message_id) DO UPDATE
                SET message_url = EXCLUDED.message_url,
                    published_at = EXCLUDED.published_at,
                    raw_text = EXCLUDED.raw_text,
                    has_media = EXCLUDED.has_media
                RETURNING id, (xmax = 0) AS inserted
                """,
                (tenant_id, message.chat, message.message_id, message.message_url,
                 message.published_at, message.text, message.has_media),
            ).fetchone()
            source_message_id, source_inserted = row

            conn.execute(
                """
                INSERT INTO telegram_parsed_load_ads
                    (tenant_id, source_message_id, origin, destination, cargo_type,
                     vehicle_type, weight_kg, volume_m3, price, currency,
                     loading_date_text, phone_numbers, confidence, parser_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (source_message_id) DO UPDATE SET
                    origin = EXCLUDED.origin, destination = EXCLUDED.destination,
                    cargo_type = EXCLUDED.cargo_type, vehicle_type = EXCLUDED.vehicle_type,
                    weight_kg = EXCLUDED.weight_kg, volume_m3 = EXCLUDED.volume_m3,
                    price = EXCLUDED.price, currency = EXCLUDED.currency,
                    loading_date_text = EXCLUDED.loading_date_text,
                    phone_numbers = EXCLUDED.phone_numbers, confidence = EXCLUDED.confidence,
                    parser_version = EXCLUDED.parser_version, parsed_at = now()
                """,
                (tenant_id, source_message_id, parsed.origin, parsed.destination, parsed.cargo_type,
                 parsed.vehicle_type, parsed.weight_kg, parsed.volume_m3, parsed.price, parsed.currency,
                 parsed.loading_date_text, json.dumps(parsed.phone_numbers, ensure_ascii=False),
                 parsed.confidence, parsed.parser_version),
            )

            load_id: UUID | None = None
            event_type: str | None = None
            canonical_changed = False
            if canonical is not None:
                existing = conn.execute(
                    """
                    SELECT id, cargo_type, weight_kg, offered_price, currency, status, external_ref
                    FROM loads
                    WHERE tenant_id = %s AND telegram_source_message_id = %s
                    FOR UPDATE
                    """,
                    (tenant_id, source_message_id),
                ).fetchone()

                if existing is None:
                    load_id = canonical.id
                    conn.execute(
                        """
                        INSERT INTO loads
                          (id, tenant_id, external_ref, cargo_type, weight_kg, offered_price,
                           currency, status, telegram_source_message_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (load_id, tenant_id, canonical.external_ref, canonical.cargo_type,
                         canonical.weight_kg, canonical.offered_price, canonical.currency,
                         canonical.status.value, source_message_id),
                    )
                    event_type = "LOAD_FOUND"
                    canonical_changed = True
                else:
                    load_id = existing[0]
                    changed = (
                        existing[1] != canonical.cargo_type
                        or existing[2] != canonical.weight_kg
                        or existing[3] != canonical.offered_price
                        or existing[4] != canonical.currency
                        or existing[5] != canonical.status.value
                        or existing[6] != canonical.external_ref
                    )
                    existing_stops = conn.execute(
                        """
                        SELECT sequence, kind, raw_address, normalized_address, latitude, longitude,
                               geo_confidence, geo_provenance, earliest, latest
                        FROM load_stops WHERE load_id = %s ORDER BY sequence
                        """,
                        (load_id,),
                    ).fetchall()
                    canonical_stops = [
                        (
                            stop.sequence, stop.kind, stop.location.raw_address,
                            stop.location.normalized_address,
                            stop.location.point.latitude if stop.location.point else None,
                            stop.location.point.longitude if stop.location.point else None,
                            stop.location.confidence, stop.location.provenance,
                            stop.earliest, stop.latest,
                        )
                        for stop in canonical.stops
                    ]
                    if existing_stops != canonical_stops:
                        changed = True

                    if changed:
                        conn.execute(
                            """
                            UPDATE loads SET external_ref=%s, cargo_type=%s, weight_kg=%s,
                              offered_price=%s, currency=%s, status=%s
                            WHERE id=%s
                            """,
                            (canonical.external_ref, canonical.cargo_type, canonical.weight_kg,
                             canonical.offered_price, canonical.currency, canonical.status.value, load_id),
                        )
                        conn.execute("DELETE FROM load_stops WHERE load_id = %s", (load_id,))
                        canonical_changed = True
                        event_type = "LOAD_UPDATED"

                if canonical_changed:
                    for stop in canonical.stops:
                        conn.execute(
                            """
                            INSERT INTO load_stops
                              (load_id, sequence, kind, raw_address, normalized_address,
                               latitude, longitude, geo_confidence, geo_provenance, earliest, latest)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                load_id, stop.sequence, stop.kind, stop.location.raw_address,
                                stop.location.normalized_address,
                                stop.location.point.latitude if stop.location.point else None,
                                stop.location.point.longitude if stop.location.point else None,
                                stop.location.confidence, stop.location.provenance,
                                stop.earliest, stop.latest,
                            ),
                        )

                    payload = self._load_payload(canonical, load_id, source_message_id)
                    event_key = self._event_key(source_message_id, event_type, payload)
                    conn.execute(
                        """
                        INSERT INTO outbox_events
                          (event_id, tenant_id, event_type, aggregate_type, aggregate_id,
                           schema_version, occurred_at, correlation_id, payload, idempotency_key)
                        VALUES (gen_random_uuid(), %s, %s, 'load', %s, 1, now(), %s, %s::jsonb, %s)
                        ON CONFLICT (idempotency_key) DO NOTHING
                        """,
                        (tenant_id, event_type, load_id, source_message_id,
                         json.dumps(payload, ensure_ascii=False), event_key),
                    )

            conn.execute(
                """
                INSERT INTO telegram_sources (tenant_id, source, last_message_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (tenant_id, source) DO UPDATE
                SET last_message_id = GREATEST(telegram_sources.last_message_id, EXCLUDED.last_message_id),
                    updated_at = now()
                """,
                (tenant_id, message.chat, message.message_id),
            )
            conn.commit()

            return IngestionResult(
                source_message_id=source_message_id,
                load_id=load_id,
                accepted=canonical is not None,
                duplicate=not source_inserted and not canonical_changed,
                event_type=event_type,
            )

    def record_message(self, tenant_id: UUID, message: TelegramSourceMessage) -> UUID | None:
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """INSERT INTO telegram_source_messages
                (tenant_id, source, message_id, message_url, published_at, raw_text, has_media)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (tenant_id, source, message_id) DO NOTHING RETURNING id""",
                (tenant_id, message.chat, message.message_id, message.message_url,
                 message.published_at, message.text, message.has_media),
            ).fetchone()
            conn.commit()
            return row[0] if row else None

    def record_parsed_ad(self, tenant_id: UUID, source_message_id: UUID, parsed: ParsedLoadAd) -> UUID:
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """INSERT INTO telegram_parsed_load_ads
                (tenant_id, source_message_id, origin, destination, cargo_type, vehicle_type,
                 weight_kg, volume_m3, price, currency, loading_date_text, phone_numbers, confidence, parser_version)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                ON CONFLICT (source_message_id) DO UPDATE SET origin=EXCLUDED.origin,
                destination=EXCLUDED.destination,cargo_type=EXCLUDED.cargo_type,vehicle_type=EXCLUDED.vehicle_type,
                weight_kg=EXCLUDED.weight_kg,volume_m3=EXCLUDED.volume_m3,price=EXCLUDED.price,currency=EXCLUDED.currency,
                loading_date_text=EXCLUDED.loading_date_text,phone_numbers=EXCLUDED.phone_numbers,
                confidence=EXCLUDED.confidence,parser_version=EXCLUDED.parser_version,parsed_at=now() RETURNING id""",
                (tenant_id, source_message_id, parsed.origin, parsed.destination, parsed.cargo_type,
                 parsed.vehicle_type, parsed.weight_kg, parsed.volume_m3, parsed.price, parsed.currency,
                 parsed.loading_date_text, json.dumps(parsed.phone_numbers, ensure_ascii=False),
                 parsed.confidence, parsed.parser_version),
            ).fetchone()
            conn.commit()
            return row[0]

    def update_checkpoint(self, tenant_id: UUID, source: str, last_message_id: int) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute("""INSERT INTO telegram_sources (tenant_id, source, last_message_id)
            VALUES (%s,%s,%s) ON CONFLICT (tenant_id,source) DO UPDATE SET
            last_message_id=GREATEST(telegram_sources.last_message_id,EXCLUDED.last_message_id),updated_at=now()""",
            (tenant_id, source, last_message_id))
            conn.commit()

    def get_checkpoints(self, tenant_id: UUID, sources: Iterable[str]) -> dict[str, int]:
        source_list = list(sources)
        if not source_list:
            return {}
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute(
                "SELECT source,last_message_id FROM telegram_sources WHERE tenant_id=%s AND source=ANY(%s)",
                (tenant_id, source_list)).fetchall()
        return {source: message_id for source, message_id in rows}
