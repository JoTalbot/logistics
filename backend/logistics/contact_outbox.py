from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from .contact_channels import ContactIntent


def enqueue_contact_intent(conn: Any, *, tenant_id: UUID, prospect_id: UUID, intent: ContactIntent) -> UUID:
    """Persist a human-reviewable contact intent. This function never sends it."""
    if intent.suppressed:
        raise ValueError("suppressed contact cannot enter the outbox")
    row = conn.execute(
        """
        INSERT INTO contact_intents
          (tenant_id, prospect_id, channel, target, message, authorized,
           suppressed, human_approval_required, status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'pending',now(),now())
        ON CONFLICT (tenant_id, prospect_id, channel, target)
        DO UPDATE SET
          message=EXCLUDED.message,
          authorized=EXCLUDED.authorized,
          suppressed=EXCLUDED.suppressed,
          human_approval_required=EXCLUDED.human_approval_required,
          updated_at=now()
        RETURNING id
        """,
        (tenant_id, prospect_id, intent.channel.value, intent.target, intent.message,
         intent.authorized, intent.suppressed, intent.human_approval_required),
    ).fetchone()
    return row[0]


def list_contact_intents(conn: Any, *, tenant_id: UUID, status: str = "pending", limit: int = 50) -> list[dict[str, Any]]:
    if status not in {"pending", "approved", "rejected", "sent", "suppressed"}:
        raise ValueError("invalid contact intent status")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT id, prospect_id, channel, target, message, authorized,
               suppressed, human_approval_required, status, created_at, updated_at
        FROM contact_intents
        WHERE tenant_id=%s AND status=%s
        ORDER BY created_at ASC
        LIMIT %s
        """, (tenant_id, status, limit)
    ).fetchall()
    keys = ("id", "prospect_id", "channel", "target", "message", "authorized", "suppressed", "human_approval_required", "status", "created_at", "updated_at")
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = str(item["id"])
        item["prospect_id"] = str(item["prospect_id"])
        item["created_at"] = item["created_at"].isoformat()
        item["updated_at"] = item["updated_at"].isoformat()
        result.append(item)
    return result
