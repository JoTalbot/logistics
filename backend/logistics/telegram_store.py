from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

import psycopg

from .telegram import ParsedLoadAd, TelegramSourceMessage


class TelegramIngestionStore:
    """Small PostgreSQL persistence boundary for Telegram ingestion.

    The unique source/message key makes ingestion idempotent under retries and
    concurrent workers. PostgreSQL ON CONFLICT provides the atomic insert path.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    def record_message(
        self,
        tenant_id: UUID,
        message: TelegramSourceMessage,
    ) -> UUID | None:
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """
                INSERT INTO telegram_source_messages
                    (tenant_id, source, message_id, message_url, published_at, raw_text, has_media)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, source, message_id) DO NOTHING
                RETURNING id
                """,
                (
                    tenant_id,
                    message.chat,
                    message.message_id,
                    message.message_url,
                    message.published_at,
                    message.text,
                    message.has_media,
                ),
            ).fetchone()
            conn.commit()
            return row[0] if row else None

    def record_parsed_ad(
        self,
        tenant_id: UUID,
        source_message_id: UUID,
        parsed: ParsedLoadAd,
    ) -> UUID:
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute(
                """
                INSERT INTO telegram_parsed_load_ads
                    (tenant_id, source_message_id, origin, destination, cargo_type,
                     vehicle_type, weight_kg, volume_m3, price, currency,
                     loading_date_text, phone_numbers, confidence, parser_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (source_message_id) DO UPDATE SET
                    origin = EXCLUDED.origin,
                    destination = EXCLUDED.destination,
                    cargo_type = EXCLUDED.cargo_type,
                    vehicle_type = EXCLUDED.vehicle_type,
                    weight_kg = EXCLUDED.weight_kg,
                    volume_m3 = EXCLUDED.volume_m3,
                    price = EXCLUDED.price,
                    currency = EXCLUDED.currency,
                    loading_date_text = EXCLUDED.loading_date_text,
                    phone_numbers = EXCLUDED.phone_numbers,
                    confidence = EXCLUDED.confidence,
                    parser_version = EXCLUDED.parser_version,
                    parsed_at = now()
                RETURNING id
                """,
                (
                    tenant_id,
                    source_message_id,
                    parsed.origin,
                    parsed.destination,
                    parsed.cargo_type,
                    parsed.vehicle_type,
                    parsed.weight_kg,
                    parsed.volume_m3,
                    parsed.price,
                    parsed.currency,
                    parsed.loading_date_text,
                    json.dumps(parsed.phone_numbers, ensure_ascii=False),
                    parsed.confidence,
                    parsed.parser_version,
                ),
            ).fetchone()
            conn.commit()
            return row[0]

    def update_checkpoint(self, tenant_id: UUID, source: str, last_message_id: int) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                INSERT INTO telegram_sources (tenant_id, source, last_message_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (tenant_id, source) DO UPDATE
                SET last_message_id = GREATEST(telegram_sources.last_message_id, EXCLUDED.last_message_id),
                    updated_at = now()
                """,
                (tenant_id, source, last_message_id),
            )
            conn.commit()

    def get_checkpoints(self, tenant_id: UUID, sources: Iterable[str]) -> dict[str, int]:
        source_list = list(sources)
        if not source_list:
            return {}
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute(
                "SELECT source, last_message_id FROM telegram_sources WHERE tenant_id = %s AND source = ANY(%s)",
                (tenant_id, source_list),
            ).fetchall()
        return {source: message_id for source, message_id in rows}
