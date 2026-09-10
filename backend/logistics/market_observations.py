from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class MarketObservation:
    source: str
    external_ref: str
    observed_at: datetime
    payload: dict[str, Any]


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_external_ref(item: dict[str, Any], *, source: str) -> str:
    for key in ("id", "proposalId", "proposal_id", "uuid", "external_ref", "number"):
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    digest = hashlib.sha256(f"{source}:".encode() + _stable_json(item).encode()).hexdigest()
    return digest


def normalize_lardi_response(response: Any, *, observed_at: datetime | None = None) -> list[MarketObservation]:
    """Convert common Lardi collection shapes into provider-neutral observations."""
    observed = observed_at or datetime.now(timezone.utc)
    if isinstance(response, dict):
        items = response.get("items")
        if items is None:
            items = response.get("proposals")
        if items is None:
            items = response.get("data")
        if not isinstance(items, list):
            items = [response]
    elif isinstance(response, list):
        items = response
    else:
        items = []

    return [
        MarketObservation("lardi-trans", stable_external_ref(item, source="lardi-trans"), observed, item)
        for item in items if isinstance(item, dict)
    ]


def upsert_market_observations(conn: Any, tenant_id: str, observations: list[MarketObservation]) -> int:
    count = 0
    for observation in observations:
        conn.execute(
            """
            INSERT INTO market_observations (tenant_id, source, external_ref, observed_at, payload)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, source, external_ref)
            DO UPDATE SET observed_at = EXCLUDED.observed_at, payload = EXCLUDED.payload
            """,
            (tenant_id, observation.source, observation.external_ref, observation.observed_at, _stable_json(observation.payload)),
        )
        count += 1
    return count


def extract_price(item: dict[str, Any]) -> tuple[Decimal | None, str | None]:
    candidates = (item.get("price"), item.get("offered_price"), item.get("rate"), item.get("cost"))
    value = next((x for x in candidates if x not in (None, "")), None)
    if isinstance(value, dict):
        currency = value.get("currency") or value.get("currencyCode")
        value = value.get("amount") or value.get("value")
    else:
        currency = item.get("currency") or item.get("currency_code")
    if value in (None, ""):
        return None, str(currency) if currency else None
    try:
        return Decimal(str(value)), str(currency) if currency else None
    except (InvalidOperation, ValueError):
        return None, str(currency) if currency else None
