#!/bin/bash
set -eu
cd /opt/logistics
restore() {
  python3 - <<'PY'
import json
from pathlib import Path
size=3
try:
    d=json.loads(Path('/var/lib/logistics/benchmarks/latest.json').read_text())
    if d.get('status')=='completed' and d.get('recommended_batch_size') in (3,5,10):
        size=d['recommended_batch_size']
except (OSError,ValueError):
    pass
p=Path('/etc/logistics/llm.env')
lines=[x for x in p.read_text().splitlines() if not x.startswith('LLM_BATCH_MAX_ITEMS=')]
p.write_text('\n'.join(lines+[f'LLM_BATCH_MAX_ITEMS={size}'])+'\n')
p.chmod(0o600)
print('Selected batch limit:',size)
PY
  docker compose -f deploy/compose.collector.yml up -d normalizer
}
trap restore EXIT
docker run --rm --name logistics-llm-benchmark --network host --env-file /etc/logistics/llm.env --read-only --tmpfs /tmp --memory 384m --cpus 0.5 -v /opt/logistics/deploy/benchmark_batches.py:/runtime/benchmark_batches.py:ro -v /var/lib/logistics/benchmarks:/benchmarks logistics-collector-collector python -u /runtime/benchmark_batches.py
