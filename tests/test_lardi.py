from unittest.mock import patch

import pytest

from logistics.lardi import LardiConfig, LardiMarketAdapter, LardiTransClient, ProviderError


def test_lardi_requires_runtime_token():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ProviderError):
            LardiTransClient()


def test_lardi_adapter_disabled_without_client():
    adapter = LardiMarketAdapter()
    assert not adapter.enabled()
    with pytest.raises(ProviderError):
        adapter.discover_cargo({})


def test_lardi_request_uses_authorization_and_expected_endpoint():
    client = LardiTransClient(LardiConfig(token="runtime-secret", language="uk"))
    with patch("logistics.lardi.urlopen") as mocked:
        response = mocked.return_value.__enter__.return_value
        response.read.return_value = b'{"items": []}'
        client.search_cargo({"country": "UA"})
        request = mocked.call_args.args[0]
        assert request.full_url.endswith("/proposals/search/cargo?language=uk")
        assert request.get_header("Authorization") == "runtime-secret"
        assert request.get_method() == "POST"
