from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from .domain import CanonicalLocation, GeoPoint, Load, LoadStatus, LoadStop
from .recurring_demand import demand_pattern_key, detect_recurring_demand
from .recurring_demand_pipeline import persist_recurring_demand


def load_persisted_telegram_loads(
    conn: Any, *, tenant_id: UUID, since: datetime | None = None, limit: int = 5000
) -> list[Load]:
    """Rehydrate canonical Telegram loads for deterministic recurring-demand analysis."""
    if limit < 1 or limit > 50_000:
        raise ValueError("limit must be between 1 and 50000")
    params: list[Any] = [tenant_id]
    where = "l.tenant_id=%s AND l.telegram_source_message_id IS NOT NULL"
    if since is not None:
        where += " AND l.created_at >= %s"
        params.append(since)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT l.id, l.external_ref, l.cargo_type, l.weight_kg,
               l.offered_price, l.currency, l.status, l.created_at
        FROM loads l
        WHERE {where}
        ORDER BY l.created_at ASC, l.id ASC
        LIMIT %s
        """,
        tuple(params),
    ).fetchall()
    if not rows:
        return []

    ids = [row[0] for row in rows]
    stop_rows = conn.execute(
        """
        SELECT load_id, sequence, kind, raw_address, normalized_address,
               latitude, longitude, geo_confidence, geo_provenance, earliest, latest
        FROM load_stops
        WHERE load_id=ANY(%s)
        ORDER BY load_id, sequence
        """,
        (ids,),
    ).fetchall()
    stops_by_load: dict[UUID, list[LoadStop]] = {load_id: [] for load_id in ids}
    for row in stop_rows:
        load_id, sequence, kind, raw, normalized, lat, lon, confidence, provenance, earliest, latest = row
        point = GeoPoint(latitude=float(lat), longitude=float(lon)) if lat is not None and lon is not None else None
        stops_by_load[load_id].append(
            LoadStop(
                sequence=sequence,
                kind=kind,
                location=CanonicalLocation(
                    raw_address=raw,
                    normalized_address=normalized,
                    point=point,
                    confidence=float(confidence or 0),
                    provenance=provenance or "deterministic",
                ),
                earliest=earliest,
                latest=latest,
            )
        )

    loads: list[Load] = []
    for row in rows:
        load_id, external_ref, cargo_type, weight_kg, offered_price, currency, status, created_at = row
        stops = stops_by_load[load_id]
        if len(stops) < 2:
            continue
        loads.append(
            Load(
                id=load_id,
                tenant_id=tenant_id,
                external_ref=external_ref,
                cargo_type=cargo_type,
                weight_kg=weight_kg,
                offered_price=Decimal(offered_price),
                currency=currency,
                stops=stops,
                status=LoadStatus(status),
                created_at=created_at,
            )
        )
    return loads


def recompute_recurring_demand(
    conn: Any,
    *,
    tenant_id: UUID,
    now: datetime,
    since: datetime | None = None,
    limit: int = 5000,
    min_observations: int = 3,
) -> int:
    """Recompute persisted recurring-demand patterns from canonical Telegram loads."""
    loads = load_persisted_telegram_loads(conn, tenant_id=tenant_id, since=since, limit=limit)
    return persist_recurring_demand(
        conn,
        tenant_id,
        loads,
        now=now,
        min_observations=min_observations,
    )
