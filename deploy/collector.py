import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID
import psycopg
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from logistics.telegram import DEFAULT_CHATS, TelegramSourceMessage, parse_load_ad
from logistics.telegram_store import TelegramIngestionStore
from logistics.telegram_worker import TelegramIngestionWorker

def save_state(path, state):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    temporary.replace(path)


async def bootstrap_latest(client, store, tenant, chat, state_path):
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    entry = state.get(chat)
    if entry and entry.get('complete'):
        return
    if entry is None:
        # Capture a fixed latest-100 snapshot; replay it after any interrupted write.
        messages = []
        async for message in client.iter_messages(chat, limit=100, reverse=False):
            messages.append(TelegramSourceMessage(
                chat=chat, message_id=message.id,
                message_url=f'{chat}/{message.id}', published_at=message.date,
                text=message.message or '', has_media=bool(message.media),
            ).model_dump(mode='json'))
        entry = {'complete': False, 'messages': sorted(messages, key=lambda m: m['message_id'])}
        state[chat] = entry
        save_state(state_path, state)
    for payload in entry['messages']:
        message = TelegramSourceMessage.model_validate(payload)
        store.ingest_message(tenant, message, parse_load_ad(message))
    count = len(entry['messages'])
    state[chat] = {'complete': True, 'count': count}
    save_state(state_path, state)
    print(f'Initial latest snapshot: {count} messages from {chat}', flush=True)


async def run(client):
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise SystemExit('Telegram session missing. Run the interactive login command first.')
        dsn = os.environ['DATABASE_URL']
        tenant = UUID(os.environ['TENANT_ID'])
        with psycopg.connect(dsn) as conn:
            conn.execute('INSERT INTO tenants (id,name) VALUES (%s,%s) ON CONFLICT (id) DO NOTHING', (tenant,'Logistics Telegram'))
        store = TelegramIngestionStore(dsn)
        worker = TelegramIngestionWorker(client, store, tenant)
        state_path = Path("/state/latest100-v1.json")
        while True:
            for chat in DEFAULT_CHATS:
                try:
                    await bootstrap_latest(client, store, tenant, chat, state_path)
                    count = await worker.run_once([chat], limit=100)
                    print(f'Processed {count} messages from {chat}', flush=True)
                except FloodWaitError as exc:
                    print(f'Telegram rate limit: waiting {exc.seconds} seconds', flush=True)
                    await asyncio.sleep(exc.seconds + 1)
                except Exception as exc:
                    print(f'Collection error for {chat}: {type(exc).__name__}', flush=True)
                    await asyncio.sleep(10)
            await asyncio.sleep(60)
    finally:
        await client.disconnect()

if __name__ == '__main__':
    os.umask(0o077)
    with open('/etc/logistics/telegram.json') as f:
        config = json.load(f)
    client = TelegramClient('/state/collector', config['TG_API_ID'], config['TG_API_HASH'])
    if '--login' in sys.argv:
        client.start()
        print('Telegram session saved. You may start the collector.')
        client.disconnect()
    else:
        asyncio.run(run(client))
