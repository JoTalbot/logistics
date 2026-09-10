import asyncio
import importlib.util
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from pathlib import Path

spec = importlib.util.spec_from_file_location('collector_runtime', str(Path(__file__).resolve().parents[1] / 'deploy' / 'collector.py'))
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class Client:
    def __init__(self):
        self.calls = 0
    async def iter_messages(self, chat, **kwargs):
        self.calls += 1
        assert kwargs == {'limit': 100, 'reverse': False}
        for i in range(200, 100, -1):
            yield SimpleNamespace(id=i, date=datetime.now(timezone.utc), message='', media=None)

class Store:
    def __init__(self, fail=False):
        self.ids = []
        self.fail = fail
    def ingest_message(self, tenant, message, parsed):
        if self.fail and len(self.ids) == 50:
            self.fail = False
            raise RuntimeError('simulated interruption')
        self.ids.append(message.message_id)

def test_latest_once_and_restart(tmp_path):
    client, store, tenant = Client(), Store(), uuid4()
    path = tmp_path / 'state.json'
    asyncio.run(runtime.bootstrap_latest(client, store, tenant, 'https://t.me/example', path))
    assert store.ids == list(range(101, 201))
    asyncio.run(runtime.bootstrap_latest(client, store, tenant, 'https://t.me/example', path))
    assert client.calls == 1
    assert len(store.ids) == 100

def test_interruption_replays_fixed_snapshot(tmp_path):
    client, store, tenant = Client(), Store(fail=True), uuid4()
    path = tmp_path / 'state.json'
    with pytest.raises(RuntimeError):
        asyncio.run(runtime.bootstrap_latest(client, store, tenant, 'https://t.me/example', path))
    asyncio.run(runtime.bootstrap_latest(client, store, tenant, 'https://t.me/example', path))
    assert client.calls == 1
    assert store.ids[-100:] == list(range(101, 201))


def test_zero_weight_does_not_block_collection():
    from logistics.telegram import TelegramSourceMessage, parse_load_ad
    message = TelegramSourceMessage(chat='test', message_id=1,
        published_at=datetime.now(timezone.utc), text='Груз 0 т, 0 м3, цена 00 грн')
    parsed = parse_load_ad(message)
    assert parsed.weight_kg is None
    assert parsed.volume_m3 is None

    assert parsed.price is None
