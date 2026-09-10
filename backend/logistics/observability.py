"""Small, dependency-light observability facade for the logistics workers."""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("logistics")


@dataclass
class IngestionMetrics:
    messages_seen: int = 0
    messages_persisted: int = 0
    messages_duplicate: int = 0
    ads_accepted: int = 0
    ads_rejected: int = 0
    errors: int = 0

    def record(self, *, persisted: bool, accepted: bool, duplicate: bool = False) -> None:
        self.messages_seen += 1
        if persisted:
            self.messages_persisted += 1
        if duplicate:
            self.messages_duplicate += 1
        if accepted:
            self.ads_accepted += 1
        else:
            self.ads_rejected += 1


class IngestionObserver:
    """Interface used by workers; production exporters can be attached later."""

    def __init__(self) -> None:
        self.metrics = IngestionMetrics()

    def message_processed(self, *, source: str, message_id: int, accepted: bool) -> None:
        self.metrics.record(persisted=True, accepted=accepted)
        logger.info(
            "telegram_message_processed source=%s message_id=%s accepted=%s",
            source,
            message_id,
            accepted,
        )

    def message_failed(self, *, source: str, message_id: int, error: Exception) -> None:
        self.metrics.errors += 1
        logger.exception(
            "telegram_message_failed source=%s message_id=%s error=%s",
            source,
            message_id,
            error,
        )
