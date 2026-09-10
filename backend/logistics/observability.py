"""Dependency-light ingestion observability with optional OpenTelemetry export."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("logistics")
_otel_configured = False


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


def _configure_otel() -> None:
    global _otel_configured
    if _otel_configured:
        return
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "logistics-os")})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    _otel_configured = True


class _OpenTelemetrySink:
    """Optional OTel sink. Core ingestion remains usable without OTel packages."""

    def __init__(self) -> None:
        _configure_otel()
        from opentelemetry import metrics, trace

        self.tracer = trace.get_tracer("logistics.telegram")
        self.meter = metrics.get_meter("logistics.telegram")
        self.messages = self.meter.create_counter(
            "logistics.telegram.messages", description="Telegram messages processed"
        )
        self.accepted = self.meter.create_counter(
            "logistics.telegram.ads.accepted", description="Accepted Telegram load ads"
        )
        self.rejected = self.meter.create_counter(
            "logistics.telegram.ads.rejected", description="Rejected Telegram load ads"
        )
        self.errors = self.meter.create_counter(
            "logistics.telegram.errors", description="Telegram ingestion errors"
        )

    def processed(self, *, source: str, message_id: int, accepted: bool, duplicate: bool) -> None:
        attrs = {"source": source, "duplicate": str(duplicate).lower()}
        self.messages.add(1, attrs)
        (self.accepted if accepted else self.rejected).add(1, attrs)
        with self.tracer.start_as_current_span("telegram.message.processed") as span:
            span.set_attribute("telegram.source", source)
            span.set_attribute("telegram.message_id", message_id)
            span.set_attribute("telegram.accepted", accepted)
            span.set_attribute("telegram.duplicate", duplicate)

    def failed(self, *, source: str, message_id: int, error: Exception) -> None:
        self.errors.add(1, {"source": source, "error.type": type(error).__name__})
        with self.tracer.start_as_current_span("telegram.message.failed") as span:
            span.set_attribute("telegram.source", source)
            span.set_attribute("telegram.message_id", message_id)
            span.record_exception(error)


def _optional_otel_sink() -> _OpenTelemetrySink | None:
    if os.getenv("LOGISTICS_OTEL_ENABLED", "0").lower() not in {"1", "true", "yes"}:
        return None
    try:
        return _OpenTelemetrySink()
    except ImportError:
        logger.warning("LOGISTICS_OTEL_ENABLED is set but OpenTelemetry packages are not installed")
        return None


class IngestionObserver:
    """Worker-facing observer with counters, structured logs and optional OTel signals."""

    def __init__(self) -> None:
        self.metrics = IngestionMetrics()
        self._otel = _optional_otel_sink()

    def message_processed(
        self,
        *,
        source: str,
        message_id: int,
        accepted: bool,
        duplicate: bool = False,
        event_type: str | None = None,
    ) -> None:
        self.metrics.record(persisted=True, accepted=accepted, duplicate=duplicate)
        logger.info(
            "telegram_message_processed source=%s message_id=%s accepted=%s duplicate=%s event_type=%s",
            source,
            message_id,
            accepted,
            duplicate,
            event_type,
        )
        if self._otel:
            self._otel.processed(
                source=source,
                message_id=message_id,
                accepted=accepted,
                duplicate=duplicate,
            )

    def message_failed(self, *, source: str, message_id: int, error: Exception) -> None:
        self.metrics.errors += 1
        logger.exception(
            "telegram_message_failed source=%s message_id=%s error=%s",
            source,
            message_id,
            error,
        )
        if self._otel:
            self._otel.failed(source=source, message_id=message_id, error=error)
