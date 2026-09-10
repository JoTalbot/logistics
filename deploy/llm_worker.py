"""Independent local CPU worker. No Telegram login, credentials or outbound actions."""
import hashlib
import json
import os
import time
import urllib.request
import psycopg
from psycopg.rows import dict_row
from logistics.local_llm import VERSION, ExtractedAd, extract, normalize

MODEL = 'qwen2.5:1.5b'
ENDPOINT = 'http://127.0.0.1:11434'

def run():
    # Verify the model already exists locally; never pull or call cloud models.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(ENDPOINT + '/api/tags', timeout=10) as f:
        tags = json.load(f)['models']
    digest = next(m['digest'] for m in tags if m['name'] == MODEL)
    if not digest.startswith('65ec06548149'):
        raise ValueError('Model digest changed: review required')
    tenant = os.environ['TENANT_ID']
    with psycopg.connect(os.environ['DATABASE_URL'], autocommit=True, row_factory=dict_row) as conn:
        if not conn.execute('SELECT pg_try_advisory_lock(760421901) AS locked').fetchone()['locked']:
            raise RuntimeError('Another normalizer is active')
        with conn.transaction():
            inserted = conn.execute('INSERT INTO telegram_llm_config(tenant_id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING tenant_id', (tenant,)).fetchone()
            if inserted:
                conn.execute('''INSERT INTO telegram_llm_jobs(tenant_id,source_message_id,parser_version,model,model_digest)
                    SELECT tenant_id,id,%s,%s,%s FROM (
                      SELECT tenant_id,id,row_number() OVER (PARTITION BY source ORDER BY message_id DESC) AS rn
                      FROM telegram_source_messages WHERE tenant_id=%s) r WHERE rn<=100
                    ON CONFLICT DO NOTHING''', (VERSION,MODEL,digest,tenant))
            conn.execute("UPDATE telegram_llm_jobs SET status=CASE WHEN attempts>=3 THEN 'failed' ELSE 'pending' END,updated_at=now() WHERE tenant_id=%s AND status='processing'", (tenant,))
        print('Local normalizer ready; model=qwen2.5:1.5b; review-only; single worker', flush=True)
        while True:
            conn.execute('''INSERT INTO telegram_llm_jobs(tenant_id,source_message_id,parser_version,model,model_digest)
                SELECT m.tenant_id,m.id,%s,%s,%s FROM telegram_source_messages m
                JOIN telegram_llm_config c ON c.tenant_id=m.tenant_id
                WHERE m.tenant_id=%s AND m.collected_at>=c.activated_at ON CONFLICT DO NOTHING''',
                (VERSION,MODEL,digest,tenant))
            row = conn.execute('''SELECT j.id,j.attempts,m.raw_text FROM telegram_llm_jobs j
                JOIN telegram_source_messages m ON m.id=j.source_message_id
                WHERE j.tenant_id=%s AND j.parser_version=%s AND j.model_digest=%s
                AND j.status='pending' AND j.available_at<=now() ORDER BY j.id LIMIT 1''', (tenant,VERSION,digest)).fetchone()
            if not row:
                time.sleep(10); continue
            job_id, text = row['id'], row['raw_text']
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            conn.execute("UPDATE telegram_llm_jobs SET status='processing', attempts=attempts+1,content_hash=%s,updated_at=now() WHERE id=%s", (content_hash,job_id))
            started = time.monotonic()
            try:
                cached = conn.execute('''SELECT normalized FROM telegram_llm_jobs
                    WHERE tenant_id=%s AND parser_version=%s AND model_digest=%s AND content_hash=%s
                    AND status='completed' LIMIT 1''', (tenant,VERSION,digest,content_hash)).fetchone()
                if cached:
                    result = cached['normalized']; status='completed'
                elif not text.strip() or len(text)>4000:
                    result={'review_required':True,'autopublish_allowed':False,'review_reasons':['empty_or_oversized_message'], 'parser_version':VERSION}
                    status='skipped'
                else:
                    result=normalize(text, extract(text,endpoint=ENDPOINT,model=MODEL)); status='completed'
                duration=round(time.monotonic()-started,2)
                conn.execute('''UPDATE telegram_llm_jobs SET status=%s,normalized=%s::jsonb,error_type=NULL,
                    duration_seconds=%s,updated_at=now() WHERE id=%s''', (status,json.dumps(result),duration,job_id))
                print(f'job={job_id} status={status} seconds={duration} cached={bool(cached)}',flush=True)
            except Exception as exc:
                attempt=row['attempts']+1
                status='failed' if attempt>=3 else 'pending'
                conn.execute('''UPDATE telegram_llm_jobs SET status=%s,error_type=%s,
                    available_at=now()+(%s * interval '1 second'),updated_at=now() WHERE id=%s''',
                    (status,type(exc).__name__,min(300,30*2**attempt),job_id))
                print(f'job={job_id} status={status} error={type(exc).__name__}',flush=True)
            time.sleep(2)

if __name__ == '__main__':
    run()
