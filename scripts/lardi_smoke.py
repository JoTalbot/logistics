from __future__ import annotations

import json
import sys
import time

from logistics.lardi import LardiConfig, LardiTransClient, ProviderError


def classify_error(message: str) -> str:
    lowered = message.casefold()
    if "http 403" in lowered and ("cloudflare" in lowered or "browser_signature" in lowered or "1010" in lowered):
        return "provider_edge_block"
    if "http 403" in lowered:
        return "provider_permission_denied"
    if "http 401" in lowered:
        return "invalid_or_unauthorized_credentials"
    if "http 429" in lowered:
        return "provider_rate_limited"
    return "provider_request_failed"


def main() -> int:
    config = LardiConfig.from_env()
    if not config.token:
        print(json.dumps({"provider": "lardi-trans", "operation": "search_cargo", "status": "configuration_missing", "action": "configure_LARDI_API_KEY"}, ensure_ascii=False))
        return 2

    client = LardiTransClient(config)
    started = time.monotonic()
    try:
        response = client.search_cargo({}, {})
    except ProviderError as exc:
        message = str(exc)
        print(json.dumps({
            "provider": "lardi-trans",
            "operation": "search_cargo",
            "status": "failed",
            "classification": classify_error(message),
            "detail": message,
            "retryable": False if "1010" in message or "browser_signature_banned" in message else None,
            "action": "contact_provider_or_enable_required_api_access",
        }, ensure_ascii=False))
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
