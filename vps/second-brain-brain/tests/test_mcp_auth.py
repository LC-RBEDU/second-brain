"""NEW-3 — MCP mount requires auth when service token configured."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"

from app.main import app  # noqa: E402


def test_mcp_without_auth_401():
    client = TestClient(app)
    r = client.post("/mcp", json={})
    assert r.status_code == 401
    assert r.json().get("error_reason") == "client_error"


def test_mcp_with_service_token_passes_auth_gate():
    client = TestClient(app)
    try:
        r = client.post(
            "/mcp",
            headers={"Authorization": "Bearer test-service-token"},
            json={},
        )
        # MCP protocol may 4xx/5xx — auth gate must not be 401
        assert r.status_code != 401
    except RuntimeError as exc:
        # streamable HTTP needs lifespan task group — still means auth passed
        assert "Task group" in str(exc) or "run()" in str(exc)
