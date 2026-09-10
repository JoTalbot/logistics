from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from .customer_discovery import Prospect, QualificationResult


def upsert_prospect(
    conn: Any,
    *,
    tenant_id: UUID,
    prospect: Prospect,
    qualification: QualificationResult | None = None,
    suppressed: bool = False,
) -> UUID:
    """Persist a provenance-first prospect; stale observations cannot regress state."""
    if not prospect.source.permitted:
        raise PermissionError("prospect source is not permitted")
    score = qualification.score if qualification else None
    tier = qualification.tier if qualification else None
    reasons = list(qualification.reasons) if qualification else []
    status = "suppressed" if suppressed else ("qualified" if qualification and tier in {"A", "B"} else "candidate")
    identity_key = f"{prospect.organization_name.strip().casefold()}|{(prospect.website or '').strip().casefold()}"
    captured_at = prospect.source.captured_at
    row = conn.execute(
        """
        INSERT INTO customer_prospects
          (tenant_id, organization_name, country, city, website, contact, signal,
           source_name, source_url, captured_at, source_permitted, suppressed,
           qualification_score, qualification_tier, qualification_reasons,
           status, last_seen_at, updated_at, identity_key, suppression_reason, suppressed_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,%s,%s,%s::jsonb,%s,now(),now(),%s,%s,%s)
        ON CONFLICT (tenant_id, source_name, source_url, organization_name)
        DO UPDATE SET
          country=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.country ELSE customer_prospects.country END,
          city=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.city ELSE customer_prospects.city END,
          website=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.website ELSE customer_prospects.website END,
          contact=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.contact ELSE customer_prospects.contact END,
          signal=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.signal ELSE customer_prospects.signal END,
          captured_at=GREATEST(customer_prospects.captured_at, EXCLUDED.captured_at),
          source_permitted=true,
          suppressed=customer_prospects.suppressed OR EXCLUDED.suppressed,
          qualification_score=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.qualification_score ELSE customer_prospects.qualification_score END,
          qualification_tier=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.qualification_tier ELSE customer_prospects.qualification_tier END,
          qualification_reasons=CASE WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.qualification_reasons ELSE customer_prospects.qualification_reasons END,
          status=CASE WHEN customer_prospects.suppressed OR EXCLUDED.suppressed THEN 'suppressed' WHEN EXCLUDED.captured_at >= customer_prospects.captured_at THEN EXCLUDED.status ELSE customer_prospects.status END,
          last_seen_at=GREATEST(customer_prospects.last_seen_at, EXCLUDED.captured_at),
          updated_at=now(),
          identity_key=COALESCE(NULLIF(customer_prospects.identity_key,''), EXCLUDED.identity_key),
          suppression_reason=CASE WHEN EXCLUDED.suppressed AND NOT customer_prospects.suppressed THEN 'operator_or_source_suppression' ELSE customer_prospects.suppression_reason END,
          suppressed_at=CASE WHEN EXCLUDED.suppressed AND NOT customer_prospects.suppressed THEN now() ELSE customer_prospects.suppressed_at END
        RETURNING id
        """,
        (
            tenant_id, prospect.organization_name, prospect.country, prospect.city,
            prospect.website, prospect.contact, prospect.signal, prospect.source.source,
            prospect.source.url, captured_at, suppressed, score, tier,
            json.dumps(reasons, ensure_ascii=False), status, identity_key,
            "operator_or_source_suppression" if suppressed else None,
            datetime.now(timezone.utc) if suppressed else None,
        ),
    ).fetchone()
    if not row:
        raise RuntimeError("prospect upsert returned no id")
    return row[0]


def set_prospect_suppression(conn: Any, *, tenant_id: UUID, prospect_id: UUID, suppressed: bool, reason: str) -> bool:
    reason = reason.strip()
    if not reason:
        raise ValueError("suppression reason is required")
    status = "suppressed" if suppressed else "candidate"
    row = conn.execute(
        """
        UPDATE customer_prospects
        SET suppressed=%s, status=%s, suppression_reason=%s,
            suppressed_at=%s, updated_at=now()
        WHERE tenant_id=%s AND id=%s
        RETURNING id
        """,
        (suppressed, status, reason if suppressed else None, datetime.now(timezone.utc) if suppressed else None, tenant_id, prospect_id),
    ).fetchone()
    return bool(row)


def list_prospects(conn: Any, *, tenant_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT id, organization_name, country, city, website, contact, signal,
               source_name, source_url, captured_at, suppressed, suppression_reason,
               suppressed_at, qualification_score, qualification_tier, qualification_reasons,
               status, last_seen_at, created_at, updated_at
        FROM customer_prospects
        WHERE tenant_id=%s
        ORDER BY qualification_score DESC NULLS LAST, updated_at DESC
        LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()
    keys = ("id", "organization_name", "country", "city", "website", "contact", "signal", "source_name", "source_url", "captured_at", "suppressed", "suppression_reason", "suppressed_at", "qualification_score", "qualification_tier", "qualification_reasons", "status", "last_seen_at", "created_at", "updated_at")
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = str(item["id"])
        for key in ("captured_at", "suppressed_at", "last_seen_at", "created_at", "updated_at"):
            if item[key] is not None:
                item[key] = item[key].isoformat()
        if item["qualification_score"] is not None:
            item["qualification_score"] = float(item["qualification_score"])
        result.append(item)
    return result
