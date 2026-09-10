"""Safe ingestion worker orchestration for Telegram sources."""
from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from .telegram import collect_messages, parse_load_ad
from .telegram_store import TelegramIngestionStore


class TelegramIngestionWorker:
    """Process source messages and checkpoint only inside the persistence transaction."""

    def __init__(self, client, store: TelegramIngestionStore, tenant_id: UUID):
        self.client = client
        self.store = store
        self.tenant_id = tenant_id

    async def run_once(self, chats: Iterable[str], *, limit: int = 100) -> int:
        chats = tuple(chats)
        checkpoints = self.store.get_checkpoints(self.tenant_id, chats)
        processed = 0
        async for message in collect_messages(self.client, chats, limit=limit, min_id_by_chat=checkpoints):
            parsed = parse_load_ad(message)
            self.store.ingest_message(self.tenant_id, message, parsed)
            processed += 1
        return processed


async def run_ingestion_once(client, store: TelegramIngestionStore, tenant_id: UUID, chats: Iterable[str], *, limit: int = 100) -> int:
    return await TelegramIngestionWorker(client, store, tenant_id).run_once(chats, limit=limit)
