"""Safe orchestration from Telegram ingestion to commercial discovery.

This module composes the existing authenticated collector, transactional
persistence boundary, and deterministic commercial discovery report. It does
not publish, negotiate, contract, mutate prices, book capacity, or perform
financial actions.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from .commercial_pipeline import CommercialCandidate
from .discovery_pipeline import DiscoveryReport, build_discovery_report
from .market_ops import PricingInput
from .observability import IngestionObserver
from .telegram import TelegramSourceMessage, collect_messages, parse_load_ad
from .telegram_store import IngestionResult, TelegramIngestionStore
from .domain import Vehicle


@dataclass(frozen=True)
class IngestionDiscoveryResult:
    """Evidence returned from one bounded ingestion/discovery pass."""

    processed: tuple[IngestionResult, ...]
    report: DiscoveryReport

    @property
    def candidates(self) -> tuple[CommercialCandidate, ...]:
        return self.report.candidates


async def run_ingestion_discovery_once(
    client,
    store: TelegramIngestionStore,
    tenant_id: UUID,
    chats: Iterable[str],
    carriers: Iterable[Vehicle],
    pricing: PricingInput,
    *,
    limit: int = 100,
    min_confidence: float = 0.6,
    min_observations: int = 3,
    now=None,
    observer: IngestionObserver | None = None,
) -> IngestionDiscoveryResult:
    """Collect, persist, and rank one bounded Telegram batch.

    The source messages used for ranking are exactly the messages that passed
    through the ingestion boundary in this invocation. Persistence remains
    authoritative for durable state and checkpoints; the returned report is a
    deterministic evidence view of the batch.
    """
    chats = tuple(chats)
    checkpoints = store.get_checkpoints(tenant_id, chats)
    source_messages: list[TelegramSourceMessage] = []
    processed: list[IngestionResult] = []
    observer = observer or IngestionObserver()

    async for message in collect_messages(
        client, chats, limit=limit, min_id_by_chat=checkpoints
    ):
        try:
            parsed = parse_load_ad(message)
            result = store.ingest_message(tenant_id, message, parsed)
            source_messages.append(message)
            processed.append(result)
            observer.message_processed(
                source=message.chat,
                message_id=message.message_id,
                accepted=result.accepted,
                duplicate=result.duplicate,
                event_type=result.event_type,
            )
        except Exception as exc:
            observer.message_failed(
                source=message.chat,
                message_id=message.message_id,
                error=exc,
            )
            raise

    report = build_discovery_report(
        source_messages,
        carriers,
        pricing,
        tenant_id=tenant_id,
        min_confidence=min_confidence,
        min_observations=min_observations,
        now=now,
    )
    return IngestionDiscoveryResult(tuple(processed), report)
