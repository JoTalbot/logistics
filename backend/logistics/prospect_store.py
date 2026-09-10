from __future__ import annotations

from dataclasses import asdict
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
    """Persist a provenance-first prospect without fetching or contacting anyone."""
    if not prospect.source.permitted:
        raise PermissionError("prospect source is not permitted")
    score = qualification.score if qualification else None
    tier = qualification.tier if qualification else None
    reasons = list(qualification.reasons) if qualification else []
    status = "suppressed" if suppressed else ("qualified" if qualification and tier in {"A", "B"} else "candidate")
    row = conn.execute(
        """
        INSERT INTO customer_prospects
          (tenant_id, organization_name, country, city, website, contact, signal,
           source_name, source_url, captured_at, source_permitted, suppressed,
           qualification_score, qualification_tier, qualification_reasons,
           status, last_seen_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,%s,%s,%s::jsonb,%s,now(),now())
        ON CONFLICT (tenant_id, source_name, source_url, organization_name)
        DO UPDATE SET
          country=EXCLUDED.country,
          city=EXCLUDED.city,
          website=EXCLUDED.website,
          contact=EXCLUDED.contact,
          signal=EXCLUDED.signal,
          captured_at=EXCLUDED.captured_at,
          source_permitted=EXCLUDED.source_permitted,
          suppressed=EXCLUDED.suppressed,
          qualification_score=EXCLUDED.qualification_score,
          qualification_tier=EXCLUDED.qualification_tier,
          qualification_reasons=EXCLUDED.qualification_reasons,
          status=EXCLUDED.status,
          last_seen_at=now(),
          updated_at=now()
        RETURNING id
        """,
        (
            tenant_id,
            prospect.organization_name,
            prospect.country,
            prospect.city,
            prospect.website,
            prospect.contact,
            prospect.signal,
            prospect.source.source,
            prospect.source.url,
            prospect.source.captured_at,
            suppressed,
            score,
            tier,
            __import__("json").dumps(reasons, ensure_ascii=False),
            status,
        ),
    ).fetchone()
    return row[0]


def list_prospects(conn: Any, *, tenant_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT id, organization_name, country, city, website, contact, signal,
               source_name, source_url, captured_at, suppressed,
               qualification_score, qualification_tier, qualification_reasons,
               status, last_seen_at, created_at, updated_at
        FROM customer_prospects
        WHERE tenant_id=%s
        ORDER BY qualification_score DESC NULLS LAST, updated_at DESC
        LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()
    keys = (
        "id", "organization_name", "country", "city", "website", "contact", "signal",
        "source_name", "source_url", "captured_at", "suppressed", "qualification_score",
        "qualification_tier", "qualification_reasons", "status", "last_seen_at", "created_at", "updated_at",
    )
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = str(item["id"])
        for key in ("captured_at", "last_seen_at", "created_at", "updated_at"):
            item[key] = item[key].isoformat()
        if item["qualification_score"] is not None:
            item["qualification_score"] = float(item["qualification_score"])
        result.append(item)
    return result
