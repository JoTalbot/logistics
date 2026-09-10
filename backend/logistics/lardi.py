from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LardiConfig:
    base_url: str = "https://api.lardi-trans.com/v2"
    token: str = ""
    language: str = "uk"
    timeout_seconds: int = 20

    @classmethod
    def from_env(cls) -> "LardiConfig":
        return cls(
            token=os.getenv("LARDI_TRANS_API_TOKEN", ""),
            language=os.getenv("LARDI_TRANS_LANGUAGE", "uk"),
        )


class LardiTransClient:
    """Official Lardi-Trans API client. No browser automation or scraping."""

    def __init__(self, config: LardiConfig | None = None):
        self.config = config or LardiConfig.from_env()
        if not self.config.token:
            raise ProviderError("LARDI_TRANS_API_TOKEN is not configured")

    def _request(self, method: str, path: str, payload: dict | None = None) -> object:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}?language={self.config.language}"
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(url, data=body, method=method, headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.config.token,
        })
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:1000]
            raise ProviderError(f"Lardi HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ProviderError(f"Lardi transport error: {exc.reason}") from exc

    def search_cargo(self, filter_payload: dict, options: dict | None = None) -> object:
        """Requires Lardi Advanced API Access according to current provider docs."""
        return self._request("POST", "/proposals/search/cargo", {
            "filter": filter_payload,
            "options": options or {},
        })

    def search_transport(self, filter_payload: dict, options: dict | None = None) -> object:
        """Requires Lardi Advanced API Access according to current provider docs."""
        return self._request("POST", "/proposals/search/lorry", {
            "filter": filter_payload,
            "options": options or {},
        })


class LardiMarketAdapter:
    provider = "lardi-trans"

    def __init__(self, client: LardiTransClient | None = None):
        self.client = client

    def enabled(self) -> bool:
        return self.client is not None

    def discover_cargo(self, filter_payload: dict, options: dict | None = None) -> object:
        if not self.client:
            raise ProviderError("Lardi adapter is disabled")
        return self.client.search_cargo(filter_payload, options)

    def discover_transport(self, filter_payload: dict, options: dict | None = None) -> object:
        if not self.client:
            raise ProviderError("Lardi adapter is disabled")
        return self.client.search_transport(filter_payload, options)
