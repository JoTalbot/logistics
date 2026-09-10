"""Safe ingestion worker orchestration for Telegram sources."""
from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from .observability import IngestionObserver
from .telegram import collect_messages, parse_load_ad
from .telegram_store import TelegramIngestionStore


class TelegramIngestionWorker:
    """Process source messages and checkpoint only inside the persistence transaction."""

    def __init__(
        self,
        client,
        store: TelegramIngestionStore,
        tenant_id: UUID,
        observer: IngestionObserver | None = None,
    ):
        self.client = client
        self.store = store
        self.tenant_id = tenant_id
        self.observer = observer or IngestionObserver()

    async def run_once(self, chats: Iterable[str], *, limit: int = 100) -> int:
        chats = tuple(chats)
        checkpoints = self.store.get_checkpoints(self.tenant_id, chats)
        processed = 0
        async for message in collect_messages(
            self.client, chats, limit=limit, min_id_by_chat=checkpoints
        ):
            try:
                parsed = parse_load_ad(message)
                result = self.store.ingest_message(self.tenant_id, message, parsed)
                self.observer.message_processed(
                    source=message.chat,
                    message_id=message.message_id,
                    accepted=result.accepted,
                    duplicate=result.duplicate,
                    event_type=result.event_type,
                )
                processed += 1
            except Exception as exc:
                self.observer.message_failed(
                    source=message.chat,
                    message_id=message.message_id,
                    error=exc,
                )
                raise
        return processed


async def run_ingestion_once(
    client,
    store: TelegramIngestionStore,
    tenant_id: UUID,
    chats: Iterable[str],
    *,
    limit: int = 100,
    observer: IngestionObserver | None = None,
) -> int:
    return await TelegramIngestionWorker(
        client, store, tenant_id, observer=observer
    ).run_once(chats, limit=limit)
