"""Matched local benchmark: same 10 short unique real ads, no production writes."""
import hashlib,json,os,time,urllib.request
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row
from logistics.local_llm import VERSION
from logistics.local_llm_batch import batch_request,validate_batch,pack,CONTEXT

DIR=Path('/benchmarks');DIR.mkdir(exist_ok=True,mode=0o700);os.umask(0o077)
def persist(report):
    temp=DIR/'latest.tmp';temp.write_text(json.dumps(report,ensure_ascii=False,default=str,indent=2));temp.replace(DIR/'latest.json')

def main():
    with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True,row_factory=dict_row) as conn:
        if not conn.execute('SELECT pg_try_advisory_lock(760421901) AS locked').fetchone()['locked']:raise RuntimeError('Normalizer must be paused')
        rows=conn.execute('''WITH recent AS (
          SELECT id,source,message_id,raw_text,row_number() OVER(PARTITION BY source ORDER BY message_id DESC) rn
          FROM telegram_source_messages WHERE tenant_id=%s)
          SELECT * FROM recent WHERE rn<=100 AND octet_length(raw_text) BETWEEN 50 AND 900 ORDER BY source,message_id DESC''',(os.environ['TENANT_ID'],)).fetchall()
        by_source={}
        for row in rows:by_source.setdefault(row['source'],[]).append(row)
        selected=[];seen=set()
        while len(selected)<10 and any(by_source.values()):
            for source,values in by_source.items():
                while values:
                    row=values.pop(0);h=hashlib.sha256(row['raw_text'].encode()).hexdigest()
                    if h in seen:continue
                    seen.add(h);selected.append({'id':len(selected)+1,'raw_text':row['raw_text'],'source':source,'source_message_id':str(row['id']),'sha256':h});break
                if len(selected)==10:break
        if len(selected)!=10 or len(pack(selected,max_items=10))!=10:raise ValueError('Cannot build matched 10-ad input in context')
        from logistics.llm_transport import ROUTE_DIGEST,verify_backend
        verify_backend();digest=ROUTE_DIGEST
        report={'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'parser_version':VERSION,'model_digest':digest,'context':CONTEXT,
          'dataset_count':10,'dataset_sources':{s:sum(x['source']==s for x in selected) for s in by_source},
          'manifest':[{k:r[k] for k in ('id','source_message_id','sha256')} for r in selected],
          'method':'same 10 unique real short ads per case; order 5,3,10; no application cache; one pass; shared host; field presence not accuracy',
          'cases':[],'status':'running'}
        persist(report)
        for size in (5,3,10):
            case={'batch_size':size,'requests':0,'valid_results':0,'failed_results':0,'seconds':0,'with_route':0,'with_weight':0,'with_price_currency':0,'unsupported_fields':0,'errors':[],'load_before':os.getloadavg()}
            started=time.monotonic()
            for index in range(0,10,size):
                group=selected[index:index+size];path=DIR/f'{uuid4()}.json'
                path.write_text(json.dumps({'announcements':[{'id':r['id'],'text':r['raw_text']} for r in group]},ensure_ascii=False))
                case['requests']+=1
                print(f'BENCH size={size} request={case["requests"]} items={len(group)} start',flush=True)
                try:
                    answer=batch_request(path,timeout=360)
                    good,bad,foreign=validate_batch(group,answer)
                    case['valid_results']+=len(good);case['failed_results']+=len(bad)
                    for result in good.values():
                        case['with_route']+=bool(result.get('origin') and result.get('destination'))
                        case['with_weight']+=bool(result.get('weight_kg'))
                        case['with_price_currency']+=bool(result.get('price') and result.get('currency'))
                        case['unsupported_fields']+=sum(x.startswith('unsupported_') for x in result['review_reasons'])
                    if foreign:case['errors'].append('ForeignIds')
                except Exception as exc:
                    case['failed_results']+=len(group);case['errors'].append(type(exc).__name__)
                finally:path.unlink(missing_ok=True)
                case['seconds']=round(time.monotonic()-started,2)
                print(f'BENCH size={size} valid={case["valid_results"]} failed={case["failed_results"]} seconds={case["seconds"]}',flush=True)
                persist({**report,'active_case':case})
            case['seconds_per_input']=round(case['seconds']/10,2)
            case['load_after']=os.getloadavg();report['cases'].append(case);persist(report)
        eligible=[x for x in report['cases'] if x['valid_results']==10 and x['failed_results']==0]
        report['recommended_batch_size']=min(eligible,key=lambda x:x['seconds'])['batch_size'] if eligible else 3
        report['recommendation_basis']='fastest complete 10/10 case; does not establish semantic accuracy' if eligible else 'conservative fallback: no case completed all 10'
        report['status']='completed';persist(report)
        print('BENCHMARK_COMPLETE '+json.dumps({'cases':report['cases'],'recommended_batch_size':report['recommended_batch_size']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
