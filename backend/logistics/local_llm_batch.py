"""Bounded batch requests through cloud-only AIOS LLMBalancer."""
import json
import math
import urllib.request
from collections import Counter
from pathlib import Path
from .local_llm import ExtractedAd, SYSTEM, normalize
from .llm_transport import request, MAX_GOAL_CHARS

CONTEXT = 16384
MAX_ITEMS = 100
OUTPUT_PER_ITEM = 256
PROMPT_RESERVE = 3000

def pack(rows, max_items=MAX_ITEMS, context=CONTEXT):
    """Conservative UTF-8 byte upper bound + output reserve; never truncate."""
    selected=[]
    budget=PROMPT_RESERVE
    for row in rows:
        if len(selected)>=min(max_items,MAX_ITEMS): break
        item={'id':row['id'],'text':row['raw_text']}
        cost=len(json.dumps(item,ensure_ascii=False).encode())+OUTPUT_PER_ITEM
        payload={'batch_id':'x'*36,'announcements':[{'id':r['id'],'text':r['raw_text']} for r in selected+[row]]}
        if budget+cost>context or len(json.dumps(payload,ensure_ascii=False))>MAX_GOAL_CHARS:
            if selected: break
            continue
        selected.append(row);budget+=cost
    return selected

def batch_request(input_file: Path, *, timeout=600):
    data=json.loads(input_file.read_text())
    items=data['announcements']
    if not items or len(items)>MAX_ITEMS or len({i['id'] for i in items})!=len(items):
        raise ValueError('Invalid batch input IDs')
    keys=[str(i['id']) for i in items]
    schema={'type':'object','$defs':{'Ad':ExtractedAd.model_json_schema()},
        'properties':{'results':{'type':'object','properties':{k:{'$ref':'#/$defs/Ad'} for k in keys},
        'required':keys,'additionalProperties':False}},'required':['results'],'additionalProperties':False}
    system=SYSTEM+' Input is a JSON file with announcements. Analyze each independently. Every ID must appear once as a key in results. multiple_ads refers to one announcement only, not the batch. Return ONLY JSON matching this schema: '+json.dumps(schema,ensure_ascii=False)
    text,backend=request(json.dumps(data,ensure_ascii=False),system,timeout=timeout)
    def unique_object(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('Duplicate response key')
            obj[key]=value
        return obj
    result=json.loads(text,object_pairs_hook=unique_object)
    if not isinstance(result,dict) or set(result)!={'results'} or not isinstance(result['results'],dict):
        raise ValueError('Invalid keyed batch envelope')
    converted=[]
    for key,ad in result['results'].items():
        if not key.isdecimal() or str(int(key))!=key:raise ValueError('Invalid response ID')
        converted.append({'id':int(key),'ad':ad})
    return {'results':converted,'_backend':backend}

def validate_batch(rows, response):
    """Validate each record against ONLY its own input, preserving good siblings."""
    if not isinstance(response,dict) or set(response)-{'results','_backend'} or 'results' not in response or not isinstance(response['results'],list):
        raise ValueError('Invalid batch envelope')
    expected={r['id']:r['raw_text'] for r in rows}
    ids=[x.get('id') for x in response['results'] if isinstance(x,dict) and type(x.get('id')) is int]
    counts=Counter(ids)
    valid={};errors={i:'MissingResult' for i in expected}
    foreign=sum(i not in expected for i in ids)
    for item in response['results']:
        if not isinstance(item,dict) or type(item.get('id')) is not int:continue
        key=item['id']
        if key not in expected:continue
        if counts[key]!=1:
            errors[key]='DuplicateResult';continue
        try:
            if set(item)!={'id','ad'}:raise ValueError('Unexpected result fields')
            ad=ExtractedAd.model_validate(item['ad'])
            normalized=normalize(expected[key],ad)
            normalized['extraction_mode']='batch-balancer-v1'
            meta=response.get('_backend',{})
            if meta:
                normalized['llm_backend']=meta['backend']
                normalized['llm_provider']=meta['provider']
                normalized['llm_route_fingerprint']=meta['route_digest']
            valid[key]=normalized
            errors.pop(key,None)
        except Exception:
            errors[key]='InvalidResult'
    return valid,errors,foreign
