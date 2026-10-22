"""MCP get_task errors keep error_reason in the tool text."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")
os.environ.setdefault("BRAIN_SERVICE_TOKEN", "test-service-token")

from fastapi.testclient import TestClient  # noqa: E402
from unittest.mock import patch  # noqa: E402

from app.main import app  # noqa: E402
from app.mcp_app import build_mcp  # noqa: E402
from app.tools import get_task as get_task_mod  # noqa: E402


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *args):
        return False


def _empty_vault():
    vault = MagicMock()
    vault.list_dir.return_value = []
    return vault


def test_mcp_not_found_keeps_reason():
    mcp = build_mcp()
    with patch.object(get_task_mod, "brain_vault", return_value=_CM(_empty_vault())):
        result = asyncio.run(mcp.call_tool("get_task", {"task_id": "F-T152"}))
    assert result.is_error is True
    text = result.content[0].text
    assert not text.startswith("Error executing tool")
    payload = json.loads(text)
    assert payload["error_reason"] == "not_found"
    assert payload["message"].startswith("not_found: F-T152.")
    assert "archiv" in payload["message"]
    assert result.structured_content == payload


def test_rest_not_found_same_message():
    with patch.object(get_task_mod, "brain_vault", return_value=_CM(_empty_vault())):
        response = TestClient(app).get(
            "/v1/tasks/item",
            params={"task_id": "F-T152"},
            headers={"Authorization": "Bearer test-service-token"},
        )
    assert response.status_code == 404
    body = response.json()
    assert body["error_reason"] == "not_found"
    assert body["message"].startswith("not_found: F-T152.")
