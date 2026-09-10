"""Bounded file-based batch requests to the installed local Ollama model."""
import json
import math
import urllib.request
from collections import Counter
from pathlib import Path
from .local_llm import ExtractedAd, NoRedirect, SYSTEM, normalize

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
        if budget+cost>context:
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
    payload={'model':'qwen2.5:1.5b','stream':False,'format':schema,'keep_alive':'5m',
        'options':{'temperature':0,'num_ctx':CONTEXT,'num_predict':max(1024,len(items)*OUTPUT_PER_ITEM),'num_thread':1},
        'messages':[{'role':'system','content':SYSTEM+' Input is a JSON file with announcements. Analyze EACH announcement independently. Return exactly one result for every input id. Copy its integer id unchanged. Never combine different ids. multiple_ads refers only to offers INSIDE ONE announcement, not to batch size; default false for one offer. Output {"results":{"123":{...ad fields...},"124":{...ad fields...}}}. Every input id is a REQUIRED object key; do not stop after the first announcement.'},
                    {'role':'user','content':json.dumps(data,ensure_ascii=False)}]}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with opener.open(request,timeout=timeout) as response:
        body=json.loads(response.read(2_000_000))
    if not body.get('done') or body.get('done_reason')!='stop':
        raise ValueError('Incomplete batch generation')
    if body.get('prompt_eval_count',0)+body.get('eval_count',0)>=CONTEXT-32:
        raise ValueError('Batch may exceed model context')
    def unique_object(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('Duplicate response key')
            obj[key]=value
        return obj
    result=json.loads(body['message']['content'],object_pairs_hook=unique_object)
    if not isinstance(result,dict) or set(result)!={'results'} or not isinstance(result['results'],dict):
        raise ValueError('Invalid keyed batch envelope')
    converted=[]
    for key,ad in result['results'].items():
        if not key.isdecimal() or str(int(key))!=key:raise ValueError('Invalid response ID')
        converted.append({'id':int(key),'ad':ad})
    return {'results':converted}

def validate_batch(rows, response):
    """Validate each record against ONLY its own input, preserving good siblings."""
    if not isinstance(response,dict) or set(response)!={'results'} or not isinstance(response['results'],list):
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
            normalized['extraction_mode']='batch-file-v1'
            valid[key]=normalized
            errors.pop(key,None)
        except Exception:
            errors[key]='InvalidResult'
    return valid,errors,foreign
