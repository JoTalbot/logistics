"""Independently enqueue committed source messages every 10 seconds."""
import json
import os
import time
import urllib.request
import psycopg
from psycopg.rows import dict_row
from logistics.local_llm import VERSION
MODEL='qwen2.5:1.5b'

def enqueue(conn,tenant,digest):
    with conn.transaction():
        first=conn.execute('INSERT INTO telegram_llm_config(tenant_id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING tenant_id',(tenant,)).fetchone()
        if first:
            conn.execute('''INSERT INTO telegram_llm_jobs(tenant_id,source_message_id,parser_version,model,model_digest)
              SELECT tenant_id,id,%s,%s,%s FROM (
                SELECT tenant_id,id,row_number() OVER(PARTITION BY source ORDER BY message_id DESC) rn
                FROM telegram_source_messages WHERE tenant_id=%s) r WHERE rn<=100 ON CONFLICT DO NOTHING''',(VERSION,MODEL,digest,tenant))
        inserted=conn.execute('''INSERT INTO telegram_llm_jobs(tenant_id,source_message_id,parser_version,model,model_digest)
          SELECT m.tenant_id,m.id,%s,%s,%s FROM telegram_source_messages m
          JOIN telegram_llm_config c ON c.tenant_id=m.tenant_id
          WHERE m.tenant_id=%s AND m.collected_at>=c.activated_at
          AND NOT EXISTS(SELECT 1 FROM telegram_llm_jobs j WHERE j.source_message_id=m.id)
          ON CONFLICT DO NOTHING''',(VERSION,MODEL,digest,tenant)).rowcount
        conn.execute('UPDATE telegram_llm_config SET enqueued_at=now(),last_enqueued_count=%s WHERE tenant_id=%s',(inserted,tenant))
    return inserted

def run():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:11434/api/tags',timeout=15) as f:tags=json.load(f)['models']
    digest=next(x['digest'] for x in tags if x['name']==MODEL)
    if not digest.startswith('65ec06548149'):raise ValueError('Unverified local model')
    with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,row_factory=dict_row) as conn:
        if not conn.execute('SELECT pg_try_advisory_lock(760421902) AS ok').fetchone()['ok']:raise RuntimeError('Enqueuer already running')
        print('Independent enqueue ready; interval=10s',flush=True)
        while True:
            count=enqueue(conn,os.environ['TENANT_ID'],digest)
            if count:print(f'enqueued={count}',flush=True)
            time.sleep(10)
if __name__=='__main__':run()
