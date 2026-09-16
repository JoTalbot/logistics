"""Regression coverage for the remote-agent bearer authentication contract."""
from __future__ import annotations

import hashlib

import pytest
from fastapi import HTTPException

from logistics.remote_control import _require_hash


def test_agent_credential_requires_bearer_scheme():
    token = "test-agent-token"
    credential_hash = hashlib.sha256(token.encode()).hexdigest()

    with pytest.raises(HTTPException) as excinfo:
        _require_hash(token, credential_hash)

    assert excinfo.value.status_code == 401


def test_agent_credential_accepts_bearer_scheme():
    token = "test-agent-token"
    credential_hash = hashlib.sha256(token.encode()).hexdigest()

    _require_hash(f"Bearer {token}", credential_hash)
