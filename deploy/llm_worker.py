"""Independent local CPU worker. No Telegram login, credentials or outbound actions."""
import hashlib
import json
import os
import time
from pathlib import Path
from uuid import uuid4
import urllib.request
import psycopg
from psycopg.rows import dict_row
from logistics.local_llm import VERSION
from logistics.local_llm_batch import pack, batch_request, validate_batch

from logistics.llm_transport import MODEL, ROUTE_DIGEST, verify_backend

def run():
    verify_backend()
    digest=ROUTE_DIGEST
    tenant = os.environ['TENANT_ID']
    with psycopg.connect(os.environ['DATABASE_URL'], autocommit=True, row_factory=dict_row) as conn:
        if not conn.execute('SELECT pg_try_advisory_lock(760421901) AS locked').fetchone()['locked']:
            raise RuntimeError('Another normalizer is active')
        conn.execute("UPDATE telegram_llm_jobs SET status='pending',attempts=GREATEST(0,attempts-1),error_type='Interrupted',updated_at=now() WHERE tenant_id=%s AND status='processing'", (tenant,))
        conn.execute("UPDATE telegram_llm_batches SET status='interrupted',finished_at=now() WHERE tenant_id=%s AND status='processing'", (tenant,))
        os.umask(0o077)
        directory=Path('/batches')
        directory.mkdir(exist_ok=True,mode=0o700)
        max_items=min(100,max(1,int(os.environ.get('LLM_BATCH_MAX_ITEMS','5'))))
        print(f'LLMBalancer cloud-only normalizer ready; max_items={max_items}; review-only',flush=True)
        while True:
            # Files contain private source text. Retain at most 24h after batch ends.
            expired=conn.execute("SELECT input_file FROM telegram_llm_batches WHERE tenant_id=%s AND finished_at < now()-interval '24 hours'",(tenant,)).fetchall()
            for old in expired:
                candidate=directory/Path(old['input_file']).name
                candidate.unlink(missing_ok=True)
            rows=conn.execute('''SELECT j.id,j.attempts,m.raw_text FROM telegram_llm_jobs j
                JOIN telegram_source_messages m ON m.id=j.source_message_id
                WHERE j.tenant_id=%s AND j.parser_version=%s AND j.model_digest=%s
                AND j.status='pending' AND j.available_at<=now() ORDER BY j.id LIMIT 100''',(tenant,VERSION,digest)).fetchall()
            candidates=[]
            for row in rows:
                text=row['raw_text']
                content_hash=hashlib.sha256(text.encode()).hexdigest()
                conn.execute('UPDATE telegram_llm_jobs SET content_hash=%s WHERE id=%s',(content_hash,row['id']))
                cached=conn.execute('''SELECT normalized FROM telegram_llm_jobs WHERE tenant_id=%s AND parser_version=%s
                    AND model_digest=%s AND content_hash=%s AND status='completed' LIMIT 1''',(tenant,VERSION,digest,content_hash)).fetchone()
                if cached:
                    conn.execute("UPDATE telegram_llm_jobs SET status='completed',normalized=%s::jsonb,error_type=NULL,duration_seconds=0,updated_at=now() WHERE id=%s",(json.dumps(cached['normalized']),row['id']))
                elif not text.strip() or len(text)>4000 or not pack([row],max_items=1):
                    result={'review_required':True,'autopublish_allowed':False,'review_reasons':['empty_or_oversized_message'],'parser_version':VERSION}
                    conn.execute("UPDATE telegram_llm_jobs SET status='skipped',normalized=%s::jsonb,updated_at=now() WHERE id=%s",(json.dumps(result),row['id']))
                else:candidates.append(row)
            selected=pack(candidates,max_items=max_items)
            if not selected:
                time.sleep(10);continue
            batch_id=uuid4()
            path=directory/f'{batch_id}.json'
            payload={'batch_id':str(batch_id),'announcements':[{'id':r['id'],'text':r['raw_text']} for r in selected]}
            content=json.dumps(payload,ensure_ascii=False).encode()
            temporary=path.with_suffix('.tmp')
            with temporary.open('wb') as f:
                f.write(content);f.flush();os.fsync(f.fileno())
            temporary.replace(path)
            ids=[r['id'] for r in selected]
            with conn.transaction():
                conn.execute('''INSERT INTO telegram_llm_batches(id,tenant_id,model_digest,input_file,input_sha256,item_count)
                    VALUES (%s,%s,%s,%s,%s,%s)''',(batch_id,tenant,digest,str(path),hashlib.sha256(content).hexdigest(),len(ids)))
                conn.execute("UPDATE telegram_llm_jobs SET status='processing',attempts=attempts+1,batch_id=%s,updated_at=now() WHERE id=ANY(%s)",(batch_id,ids))
            started=time.monotonic()
            print(f'batch={batch_id} items={len(ids)} request=1 started',flush=True)
            error_type=None
            try:
                conn.execute('UPDATE telegram_llm_batches SET request_count=1 WHERE id=%s',(batch_id,))
                response=batch_request(path)  # Exactly one HTTP inference call per file.
                valid,errors,foreign=validate_batch(selected,response)
            except Exception as exc:
                valid={};errors={i:type(exc).__name__ for i in ids};foreign=0;error_type=type(exc).__name__
            duration=round(time.monotonic()-started,2)
            # Each successful ad is independently committed. Missing/invalid siblings retry later.
            for row in selected:
                key=row['id']
                if key in valid:
                    conn.execute('''UPDATE telegram_llm_jobs SET status='completed',normalized=%s::jsonb,error_type=NULL,
                        duration_seconds=%s,updated_at=now() WHERE id=%s''',(json.dumps(valid[key]),duration/len(ids),key))
                else:
                    attempt=row['attempts']+1
                    status='failed' if attempt>=3 else 'pending'
                    conn.execute('''UPDATE telegram_llm_jobs SET status=%s,error_type=%s,available_at=now()+(%s*interval '1 second'),
                        updated_at=now() WHERE id=%s''',(status,errors.get(key,'MissingResult'),min(300,30*2**attempt),key))
            status='completed' if len(valid)==len(ids) else ('partial' if valid else 'failed')
            conn.execute('''UPDATE telegram_llm_batches SET status=%s,completed_count=%s,failed_count=%s,foreign_ids=%s,
                error_type=%s,duration_seconds=%s,finished_at=now() WHERE id=%s''',
                (status,len(valid),len(ids)-len(valid),foreign,error_type,duration,batch_id))
            print(f'batch={batch_id} status={status} saved={len(valid)} retry_or_failed={len(ids)-len(valid)} seconds={duration}',flush=True)
            time.sleep(2)

if __name__ == '__main__':
    run()
