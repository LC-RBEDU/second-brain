"""NEW-3 — MCP mount requires auth when service token configured."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    # Session manager .run() is once-per-instance — one lifespan for the module.
    with TestClient(app) as c:
        yield c


def test_mcp_without_auth_401(client: TestClient):
    r = client.post("/mcp", json={})
    assert r.status_code == 401
    assert r.json().get("error_reason") == "client_error"


def test_mcp_with_service_token_passes_auth_gate(client: TestClient):
    """Lifespan starts MCP session_manager — auth gate must not 401."""
    r = client.post(
        "/mcp/",
        headers={
            "Authorization": "Bearer test-service-token",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
    )
    # Auth middleware passed (not 401). MCP transport may 421 on Host=testserver.
    assert r.status_code != 401
    assert r.status_code != 500
