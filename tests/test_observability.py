from logistics.observability import IngestionObserver


def test_ingestion_observer_counts_processed_and_failed_messages():
    observer = IngestionObserver()
    observer.message_processed(source="chat", message_id=1, accepted=True)
    observer.message_processed(source="chat", message_id=2, accepted=False)

    assert observer.metrics.messages_seen == 2
    assert observer.metrics.messages_persisted == 2
    assert observer.metrics.ads_accepted == 1
    assert observer.metrics.ads_rejected == 1


def test_ingestion_observer_records_errors():
    observer = IngestionObserver()
    error = RuntimeError("boom")

    try:
        observer.message_failed(source="chat", message_id=3, error=error)
    except Exception:
        raise AssertionError("observer must not re-raise")

    assert observer.metrics.errors == 1
