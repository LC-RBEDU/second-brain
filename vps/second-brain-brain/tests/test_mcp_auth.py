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


def test_t12_middleware_sets_service_principal_contextvar():
    """T12 — Bearer auth sets ServicePrincipal on ContextVar during request."""
    import asyncio

    from starlette.responses import PlainTextResponse

    from app.auth_service import ServicePrincipal
    from app.mcp_auth import McpAuthMiddleware
    from app.request_principal import get_brain_principal

    seen: list = []

    async def inner(scope, receive, send):
        seen.append(get_brain_principal())
        resp = PlainTextResponse("ok")
        await resp(scope, receive, send)

    app = McpAuthMiddleware(inner)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/mcp/",
        "raw_path": b"/mcp/",
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [
            (b"authorization", b"Bearer test-service-token"),
            (b"host", b"testserver"),
        ],
        "client": ("127.0.0.1", 123),
        "server": ("testserver", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_msg):
        return None

    asyncio.run(app(scope, receive, send))
    assert len(seen) == 1
    assert isinstance(seen[0], ServicePrincipal)
    assert get_brain_principal() is None  # reset after request
