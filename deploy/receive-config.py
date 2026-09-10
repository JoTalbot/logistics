#!/usr/bin/python3
import json, os, sys, tempfile
os.umask(0o077)
d = json.loads(sys.stdin.buffer.read(8192))
api_id = str(d.get('TG_API_ID', '')).strip()
api_hash = str(d.get('TG_API_HASH', '')).strip()
if not api_id.isdigit() or int(api_id) <= 0 or len(api_hash) != 32 or any(c not in '0123456789abcdefABCDEF' for c in api_hash):
    sys.exit('Invalid Telegram configuration')
os.makedirs('/etc/logistics', mode=0o700, exist_ok=True)
fd, path = tempfile.mkstemp(dir='/etc/logistics')
with os.fdopen(fd, 'w') as f:
    json.dump({'TG_API_ID': int(api_id), 'TG_API_HASH': api_hash}, f)
os.replace(path, '/etc/logistics/telegram.json')
print('Telegram configuration installed; values not printed.')
