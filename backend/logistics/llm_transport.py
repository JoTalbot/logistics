"""AIOS LLMBalancer cloud-only transport. Never calls or falls back to Ollama."""
import hashlib
import json
import urllib.request

ENDPOINT='http://127.0.0.1:9600'
MODEL='aios-llmbalancer-cloud'
ROUTE_DIGEST='route:'+hashlib.sha256(b'aios-9600-cloud-only-explicit-providers-v1').hexdigest()
MAX_GOAL_CHARS=3800  # Existing cloud adapter truncates at 4000; stay below it.

class BackendUnavailable(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise BackendUnavailable('Redirect not allowed')

def opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())

def verify_backend():
    with opener().open(ENDPOINT+'/openapi.json',timeout=10) as f:schema=json.load(f)
    fields=schema.get('components',{}).get('schemas',{}).get('GoalRequest',{}).get('properties',{})
    if not {'cloud_only','json_mode'} <= set(fields):raise BackendUnavailable('Cloud-only capability missing')

def request(goal,system,timeout=120):
    if len(goal)>MAX_GOAL_CHARS:raise ValueError('Input exceeds balancer prompt limit; do not truncate')
    payload={'goal':goal,'system_prompt':system,'cloud_only':True,'json_mode':True}
    req=urllib.request.Request(ENDPOINT+'/api/v1/aios/ask',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with opener().open(req,timeout=min(timeout,120)) as f:response=json.loads(f.read(2_000_000))
    provider=response.get('provider') or ''
    if response.get('status')!='success' or response.get('tier')=='local' or not provider.startswith(('groq-','cerebras-','sambanova-','deepseek-','openrouter-','mistral-','gemini-','huggingface-','hf-')):
        raise BackendUnavailable('No permitted cloud provider returned a result')
    text=response.get('text','').strip()
    if text.startswith('```') and text.endswith('```'):
        lines=text.splitlines();text='\n'.join(lines[1:-1]).strip()
    return text,{'backend':MODEL,'provider':provider,'route_digest':ROUTE_DIGEST}
