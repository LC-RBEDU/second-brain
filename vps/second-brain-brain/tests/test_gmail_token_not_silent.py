"""NEW-1 — tokens set + unwired API → error_reason, not silent []."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.gmail_client import list_l1  # noqa: E402


def test_token_present_surfaces_error_reason(monkeypatch):
    monkeypatch.setenv("GMAIL_WORKSPACE_REFRESH_TOKEN", "tok")
    monkeypatch.delenv("GMAIL_PERSONAL_REFRESH_TOKEN", raising=False)
    result = list_l1(mailboxes=("workspace",))
    assert result.messages == []
    assert result.error_reason
    assert "gmail_api_not_wired" in result.error_reason
