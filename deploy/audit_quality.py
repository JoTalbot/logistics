"""Read-only quality audit. Print only aggregates and synthetic test results."""
import os,json,re,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timezone
import psycopg
from psycopg.rows import dict_row
from logistics.telegram import TelegramSourceMessage,parse_load_ad
from logistics.telegram_pipeline import validate_parsed_ad

with psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row) as conn:
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    rows=conn.execute('''WITH ranked AS (
      SELECT m.*, row_number() OVER (PARTITION BY tenant_id,source ORDER BY message_id DESC) AS rn
      FROM telegram_source_messages m WHERE tenant_id=%s)
      SELECT r.*, p.origin,p.destination,p.cargo_type,p.weight_kg,p.volume_m3,p.price,p.currency,
      p.confidence,p.vehicle_type,NULL AS loading_date_text,p.id AS parsed_id,
      EXISTS(SELECT 1 FROM loads l WHERE l.telegram_source_message_id=r.id) AS canonical
      FROM ranked r LEFT JOIN telegram_parsed_load_ads p ON p.source_message_id=r.id WHERE rn<=100''',
      (os.environ['TENANT_ID'],)).fetchall()
    total=conn.execute('SELECT count(*) AS messages FROM telegram_source_messages WHERE tenant_id=%s',(os.environ['TENANT_ID'],)).fetchone()
    dup_ids=conn.execute('''SELECT count(*) AS duplicate_groups FROM (
      SELECT source,message_id FROM telegram_source_messages WHERE tenant_id=%s
      GROUP BY source,message_id HAVING count(*)>1) d''',(os.environ['TENANT_ID'],)).fetchone()

stats=defaultdict(Counter); reasons=Counter(); hashes=defaultdict(list); anomalies=Counter(); errors=Counter()
fields=['origin','destination','cargo_type','weight_kg','volume_m3','price','currency','vehicle_type','loading_date_text']
for r in rows:
    s=stats[r['source']];s['messages']+=1;s['parsed']+=int(r['parsed_id'] is not None);s['canonical']+=int(r['canonical'])
    for f in fields:s[f]+=int(bool(r[f]))
    s['empty_text']+=int(not r['raw_text'].strip())
    s['with_media']+=int(r['has_media'])
    s['confidence_ge_06']+=int(r['confidence'] is not None and r['confidence']>=0.6)
    text=r['raw_text']; normalized=re.sub(r'\s+',' ',text).strip().casefold()
    if normalized:hashes[hashlib.sha256(normalized.encode()).hexdigest()].append(r['source'])
    if not r['origin'] and re.search(r'[A-Za-zА-Яа-яІіЇїЄєЁё]{3,}\s*[—–-]\s*[A-Za-zА-Яа-яІіЇїЄєЁё]{3,}',text):anomalies['missing_route_with_dash_candidate']+=1
    if r['price'] and not r['currency']:anomalies['price_without_currency']+=1
    if r['weight_kg'] and r['weight_kg']>60000:anomalies['weight_over_60t_review']+=1
    if r['origin'] and len(r['origin'])>100:anomalies['origin_over_100_chars']+=1
    if r['destination'] and len(r['destination'])>100:anomalies['destination_over_100_chars']+=1
    try:
        m=TelegramSourceMessage(chat=r['source'],message_id=r['message_id'],published_at=r['published_at'],text=text,has_media=r['has_media'])
        parsed=parse_load_ad(m); verdict=validate_parsed_ad(parsed)
        reasons.update(verdict.reasons)
        s['current_parser_accepted']+=int(verdict.accepted)
    except Exception as exc:errors[type(exc).__name__]+=1

dups=[v for v in hashes.values() if len(v)>1]
fixtures=[
 ('arrow_route','Київ → Львів\nвантаж: зерно\n22 т\nціна: 25000 UAH',{'origin':'Київ','destination':'Львів','weight_kg':22000,'price':'25000','currency':'UAH'}),
 ('dash_route','Київ - Львів\nвантаж: зерно\n22 т\nціна: 25000 UAH',{'origin':'Київ','destination':'Львів'}),
 ('spaced_price','Київ → Львів\nвантаж: зерно\n22 т\nціна: 25 000 грн',{'price':'25000','currency':'UAH'}),
 ('decimal_weight','Київ → Львів\nвантаж: зерно\n22,5 т\nціна: 25000 грн',{'weight_kg':22500}),
 ('kg_weight','Київ → Львів\nвантаж: зерно\n22000 кг\nціна: 25000 грн',{'weight_kg':22000}),
 ('english_t_weight','Kyiv → Lviv\ncargo: grain\n22 t\nprice: 25000 UAH',{'weight_kg':22000}),
 ('vehicle_date','Київ → Львів\nвантаж: зерно\n22 т\nкузов: тент\nзавантаження: 11.09.2026\nціна: 25000 грн',{'vehicle_type':'тент','loading_date_text':'11.09.2026'}),
 ('currency_dollar_word','Київ → Львів\nвантаж: зерно\n22 т\nцена: 500 доллар',{'currency':'USD'}),
 ('unlabelled_cargo','Київ → Львів\n22 т зерно\n25000 грн',{'cargo_type':'зерно'}),
]
synthetic=[]
for name,text,expected in fixtures:
    try:
        p=parse_load_ad(TelegramSourceMessage(chat='synthetic',message_id=1,published_at=datetime.now(timezone.utc),text=text))
        actual={k:str(getattr(p,k)) if k=='price' and getattr(p,k) is not None else getattr(p,k) for k in expected}
        synthetic.append({'case':name,'pass':actual==expected,'expected':expected,'actual':actual})
    except Exception as exc:synthetic.append({'case':name,'error':type(exc).__name__})
print(json.dumps({'checked_at_utc':datetime.now(timezone.utc).isoformat(),'sample_messages':len(rows),'all_stored':total,'duplicate_ids':dup_ids,'by_source':dict(stats),'rejection_reasons':reasons,'anomalies_heuristic':anomalies,'parser_errors':errors,'text_duplicates':{'groups':len(dups),'extra_copies':sum(len(v)-1 for v in dups),'cross_source_groups':sum(len(set(v))>1 for v in dups)},'synthetic_tests':synthetic},ensure_ascii=False,default=str,indent=2))
