"""T5 — slack_live: no dump; token missing; queries exclude Saved."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.tools import slack_live as mod  # noqa: E402


def test_token_missing():
    out = mod.slack_live_search(env={})
    assert out["candidates"] == []
    assert out["dumped"] is False
    assert out["error_reason"] == "slack_token_missing"


def test_search_no_dump_and_eyes_query():
    calls: list[str] = []

    def fake_search(token: str, query: str, **_kw):
        calls.append(query)
        return [{"ts": "1.0", "channel": "C1", "text": "hi", "permalink": "http://x"}]

    with patch.object(mod, "_search", side_effect=fake_search):
        out = mod.slack_live_search(
            env={"SLACK_USER_TOKEN": "xoxp-t", "SLACK_LUKAS_USER_ID": "U1"}
        )
    assert out["dumped"] is False
    assert out["candidates"]
    joined = " ".join(calls)
    assert "hasmy::eyes:" in joined
    assert "hasmy::gear:" in joined
    assert "is:saved" not in joined.lower()
    assert "saved" not in joined.lower()
