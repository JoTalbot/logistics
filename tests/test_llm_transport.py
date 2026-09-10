import json
from unittest.mock import MagicMock,patch
import pytest
from logistics.llm_transport import request,BackendUnavailable,verify_backend

def fake_open(data):
    op=MagicMock();op.open.return_value.__enter__.return_value.read.return_value=json.dumps(data).encode()
    return op

def test_cloud_only_flag_and_provider_recorded():
    op=fake_open({'status':'success','tier':'fast','provider':'groq-gpt-oss-20b','text':'{}'})
    with patch('logistics.llm_transport.opener',return_value=op):text,meta=request('synthetic','system')
    assert text=='{}' and meta['provider']=='groq-gpt-oss-20b'
    sent=json.loads(op.open.call_args.args[0].data)
    assert sent['cloud_only'] is True and sent['json_mode'] is True
    assert op.open.call_count==1

@pytest.mark.parametrize('body',[
 {'status':'unavailable','provider':None,'text':''},
 {'status':'success','provider':'ollama-qwen2.5:1.5b','tier':'local','text':'{}'},
 {'status':'success','provider':'emergency_engine','text':'{}'}])
def test_no_local_or_fake_fallback(body):
    op=fake_open(body)
    with patch('logistics.llm_transport.opener',return_value=op),pytest.raises(BackendUnavailable):request('test','system')
    assert op.open.call_count==1

def test_large_prompt_rejected_before_send():
    with patch('logistics.llm_transport.opener') as op,pytest.raises(ValueError):request('x'*4001,'system')
    op.assert_not_called()

def test_json_fence_removed_only_as_wrapper():
    op=fake_open({'status':'success','provider':'groq-gpt-oss-20b','text':'```json\n{}\n```'})
    with patch('logistics.llm_transport.opener',return_value=op):text,_=request('test','system')
    assert text=='{}'
