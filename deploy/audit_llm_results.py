"""Read-only aggregate audit; no source text or extracted contact data printed."""
import json,os,re
from collections import Counter
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row
def squash(s): return re.sub(r'\s+', ' ', s).strip().casefold()

with psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row,connect_timeout=15) as c:
    c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    c.execute("SET LOCAL statement_timeout='20s'")
    queue=c.execute('SELECT status,count(*) AS count FROM telegram_llm_jobs GROUP BY status').fetchall()
    batches=c.execute('''SELECT id,item_count,request_count,status,completed_count,failed_count,
      foreign_ids,error_type,duration_seconds,created_at,finished_at,
      EXTRACT(EPOCH FROM(now()-created_at))::integer AS elapsed_seconds
      FROM telegram_llm_batches ORDER BY created_at DESC LIMIT 10''').fetchall()
    rows=c.execute('''SELECT j.id,j.batch_id,j.normalized,m.raw_text,m.source,p.origin AS regex_origin,
       p.destination AS regex_destination,p.weight_kg AS regex_weight,p.price AS regex_price,p.currency AS regex_currency
       FROM telegram_llm_jobs j JOIN telegram_source_messages m ON m.id=j.source_message_id
       LEFT JOIN telegram_parsed_load_ads p ON p.source_message_id=m.id
       WHERE j.status='completed' AND j.tenant_id=%s ORDER BY j.updated_at DESC LIMIT 50''',(os.environ['TENANT_ID'],)).fetchall()
    ingestion=c.execute('''SELECT source,max(collected_at) AS last_collected,count(*) FILTER (WHERE collected_at>=now()-interval '10 minutes') AS new_10min
       FROM telegram_source_messages WHERE tenant_id=%s GROUP BY source''',(os.environ['TENANT_ID'],)).fetchall()
    unqueued=c.execute('''SELECT count(*) AS count FROM telegram_source_messages m JOIN telegram_llm_config cfg ON cfg.tenant_id=m.tenant_id
      WHERE m.tenant_id=%s AND m.collected_at>=cfg.activated_at AND NOT EXISTS
      (SELECT 1 FROM telegram_llm_jobs j WHERE j.source_message_id=m.id)''',(os.environ['TENANT_ID'],)).fetchone()
    errors=c.execute("SELECT error_type,count(*) AS count FROM telegram_llm_jobs WHERE error_type IS NOT NULL GROUP BY error_type").fetchall()

counts=Counter(); kinds=Counter();reasons=Counter();comparisons=Counter();flags=Counter();sources=Counter()
for row in rows:
    r=row['normalized'];text=row['raw_text'];sources[row['source']]+=1
    for f in ('origin','destination','cargo_type','weight_kg','volume_m3','price','currency','vehicle_type','loading_date'):
        counts[f]+=int(bool(r.get(f)))
    counts['route']+=int(bool(r.get('origin') and r.get('destination')))
    counts['batch_mode']+=int(r.get('extraction_mode')=='batch-file-v1')
    counts['review_required']+=int(r.get('review_required') is True)
    counts['autopublish_allowed']+=int(r.get('autopublish_allowed') is True)
    counts['required_fields_present']+=int(all(r.get(f) for f in ('origin','destination','cargo_type','weight_kg','price','currency')))
    kinds[r.get('kind','missing')]+=1;reasons.update(r.get('review_reasons',[]))
    for f,v in r.get('evidence',{}).items():
        if v and squash(v) not in squash(text):flags['evidence_not_in_own_text']+=1
    for a,b in [('origin','regex_origin'),('destination','regex_destination'),('weight_kg','regex_weight'),('price','regex_price'),('currency','regex_currency')]:
        llm=r.get(a);old=row[b]
        if llm and not old:comparisons[a+'_llm_only']+=1
        if llm and old:
            same = str(llm)==str(old)
            if a in ('price','weight_kg'):
                from decimal import Decimal
                same=Decimal(str(llm))==Decimal(str(old))
            comparisons[a+('_agree' if same else '_disagree')]+=1
    ev=r.get('evidence',{})
    if r.get('origin') and r.get('destination') and squash(r['origin'])==squash(r['destination']):flags['identical_route_endpoints']+=1
    if r.get('weight_kg') and (r['weight_kg']<=0 or r['weight_kg']>60000):flags['weight_range_review']+=1
    if r.get('price') and not r.get('currency'):flags['price_without_currency']+=1
    if r.get('currency')=='UAH' and not re.search(r'грн|грив|UAH|₴',ev.get('price') or '',re.I):flags['uah_without_marker']+=1
    if re.search(r'(?:/|за\s*|per\s*)(?:км|km)\b',ev.get('price') or '',re.I) and r.get('price_basis')!='per_km':flags['unmarked_per_km_rate']+=1
    if r.get('kind')=='vehicle' and all(r.get(f) for f in ('origin','destination','weight_kg','price','currency')):flags['vehicle_with_load_fields_requires_review']+=1
print(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'queue':queue,'batches':batches,'ingestion':ingestion,'new_messages_not_yet_enqueued':unqueued,'error_types':errors,'sample_size':len(rows),'sample_by_source':sources,'fields':counts,'kinds':kinds,'review_reasons':reasons,'heuristic_flags':flags,'regex_comparison_not_ground_truth':comparisons},ensure_ascii=False,default=str,indent=2))
