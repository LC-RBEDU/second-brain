"""NEW-1/NEW-2 — MCP mount + OAuth routes exist; allowlist 403 path."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"
os.environ["BRAIN_PUBLIC_URL"] = "https://brain.example.com"
os.environ["GOOGLE_CLIENT_ID"] = "cid"
os.environ["GOOGLE_CLIENT_SECRET"] = "csecret"

from app.main import app  # noqa: E402


def test_mcp_mounted():
    mounts = [r for r in app.routes if type(r).__name__ == "Mount"]
    assert any(getattr(m, "path", None) == "/mcp" for m in mounts)


def test_oauth_authorize_redirect():
    client = TestClient(app)
    r = client.get("/oauth/authorize", follow_redirects=False)
    assert r.status_code == 302
    assert "accounts.google.com" in r.headers["location"]
    assert "redirect_uri=https%3A%2F%2Fbrain.example.com%2Foauth%2Fcallback" in r.headers[
        "location"
    ] or "brain.example.com/oauth/callback" in r.headers["location"]


def test_oauth_callback_reject_non_allowlist():
    client = TestClient(app)
    r0 = client.get("/oauth/authorize", follow_redirects=False)
    from urllib.parse import parse_qs, urlparse

    state = parse_qs(urlparse(r0.headers["location"]).query)["state"][0]

    mock_tok = MagicMock(status_code=200)
    mock_tok.json.return_value = {"access_token": "t"}
    mock_ui = MagicMock(status_code=200)
    mock_ui.json.return_value = {"email": "stranger@example.com"}

    class _CM:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            return mock_tok

        async def get(self, *a, **k):
            return mock_ui

    with patch("app.oauth_routes.httpx.AsyncClient", return_value=_CM()):
        r = client.get(f"/oauth/callback?code=x&state={state}")
    assert r.status_code == 403
