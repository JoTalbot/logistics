from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class MarketObservation:
    source: str
    external_ref: str
    observed_at: datetime
    payload: dict[str, Any]


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def normalize_lardi_response(response: Any, *, observed_at: datetime | None = None) -> list[MarketObservation]:
    """Convert common Lardi collection shapes into provider-neutral observations.

    Provider-specific fields remain inside payload so normalization never invents
    business values that the upstream response did not provide.
    """
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

    result: list[MarketObservation] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        external_ref = next((str(item[k]) for k in ("id", "proposalId", "proposal_id", "uuid", "external_ref") if item.get(k) is not None), None)
        if external_ref is None:
            external_ref = hashlib.sha256(_stable_json(item).encode()).hexdigest()
        result.append(MarketObservation("lardi-trans", external_ref, observed, item))
    return result


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
