import json
from unittest.mock import patch, MagicMock
from logistics.local_llm_batch import pack, validate_batch, batch_request

def ad(**kw):
    d=dict(kind='load',multiple_ads=False,origin=None,destination=None,cargo=None,weight=None,volume=None,price=None,vehicle=None,date=None)
    d.update(kw);return d

def test_pack_100_short_no_101():
    rows=[{'id':i,'raw_text':'Київ'} for i in range(101)]
    assert len(pack(rows,context=32768))==100

def test_long_input_reduces_batch_never_truncates():
    rows=[{'id':i,'raw_text':'А'*3000} for i in range(100)]
    selected=pack(rows)
    assert 1<len(selected)<100
    assert all(len(r['raw_text'])==3000 for r in selected)

def test_results_match_by_id_not_position():
    rows=[{'id':1,'raw_text':'Київ'},{'id':2,'raw_text':'Львів'}]
    response={'results':[{'id':2,'ad':ad(origin='Львів')},{'id':1,'ad':ad(origin='Київ')}]}
    valid,errors,foreign=validate_batch(rows,response)
    assert valid[1]['origin']=='Київ' and valid[2]['origin']=='Львів'
    assert errors=={} and foreign==0

def test_missing_duplicate_foreign_preserve_good():
    rows=[{'id':i,'raw_text':'Київ'} for i in range(1,5)]
    response={'results':[{'id':1,'ad':ad(origin='Київ')},{'id':2,'ad':ad()},{'id':2,'ad':ad()},{'id':3,'ad':{'invalid':'schema'}},{'id':99,'ad':ad()}]}
    good,bad,foreign=validate_batch(rows,response)
    assert list(good)==[1]
    assert bad=={2:'DuplicateResult',3:'InvalidResult',4:'MissingResult'}
    assert foreign==1

def test_other_ad_evidence_not_accepted():
    good,_,_=validate_batch([{'id':1,'raw_text':'Київ'},{'id':2,'raw_text':'Львів'}],{'results':[{'id':1,'ad':ad(origin='Львів')},{'id':2,'ad':ad(origin='Львів')}]})
    assert good[1]['origin'] is None and good[2]['origin']=='Львів'

def test_exactly_one_request_for_file(tmp_path):
    p=tmp_path/'batch.json';p.write_text(json.dumps({'announcements':[{'id':1,'text':'Київ'},{'id':2,'text':'Львів'}]}))
    response={'results':[{'id':1,'ad':ad()},{'id':2,'ad':ad()}]}
    body={'done':True,'done_reason':'stop','message':{'content':json.dumps({'results':{'1':ad(),'2':ad()}})}}
    opener=MagicMock();opener.open.return_value.__enter__.return_value.read.return_value=json.dumps(body).encode()
    with patch('logistics.local_llm_batch.urllib.request.build_opener',return_value=opener):
        assert batch_request(p)==response
    assert opener.open.call_count==1
    request=opener.open.call_args.args[0]
    sent=json.loads(request.data)
    assert len(json.loads(sent['messages'][1]['content'])['announcements'])==2
