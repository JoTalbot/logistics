import asyncio
import json
import os
import sys
from uuid import UUID
import psycopg
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from logistics.telegram import DEFAULT_CHATS
from logistics.telegram_store import TelegramIngestionStore
from logistics.telegram_worker import TelegramIngestionWorker

os.umask(0o077)
with open('/etc/logistics/telegram.json') as f:
    config = json.load(f)
client = TelegramClient('/state/collector', config['TG_API_ID'], config['TG_API_HASH'])

async def run():
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise SystemExit('Telegram session missing. Run the interactive login command first.')
        dsn = os.environ['DATABASE_URL']
        tenant = UUID(os.environ['TENANT_ID'])
        with psycopg.connect(dsn) as conn:
            conn.execute('INSERT INTO tenants (id,name) VALUES (%s,%s) ON CONFLICT (id) DO NOTHING', (tenant,'Logistics Telegram'))
        worker = TelegramIngestionWorker(client, TelegramIngestionStore(dsn), tenant)
        while True:
            for chat in DEFAULT_CHATS:
                try:
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

if '--login' in sys.argv:
    client.start()
    print('Telegram session saved. You may start the collector.')
    client.disconnect()
else:
    asyncio.run(run())
