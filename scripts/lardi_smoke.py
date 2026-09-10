from __future__ import annotations

import json
import os
import sys
import time

from logistics.lardi import LardiConfig, LardiTransClient, ProviderError


def main() -> int:
    config = LardiConfig.from_env()
    if not config.token:
        print("Lardi smoke: LARDI_API_KEY is not configured")
        return 2

    client = LardiTransClient(config)
    started = time.monotonic()
    try:
        response = client.search_cargo({}, {})
    except ProviderError as exc:
        # Never print configuration values or authorization headers.
        print(f"Lardi smoke: provider request failed: {exc}")
        return 1

    elapsed_ms = round((time.monotonic() - started) * 1000)
    if isinstance(response, dict):
        items = response.get("items") or response.get("proposals") or response.get("data")
        count = len(items) if isinstance(items, list) else 1
    elif isinstance(response, list):
        count = len(response)
    else:
        count = 1

    print(json.dumps({"provider": "lardi-trans", "operation": "search_cargo", "http": "success", "observations": count, "latency_ms": elapsed_ms}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
