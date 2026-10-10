"""T13 pieces — C4 Slack skip after Grok; backoff; chain stop on success."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import reminder_chat_delivery as mod  # noqa: E402


def test_backoff_minutes():
    assert mod.backoff_minutes(0) == 1
    assert mod.backoff_minutes(1) == 2
    assert mod.backoff_minutes(6) == 60


def test_chain_stops_on_grok_ok():
    rem = {"id": "r1", "message": "hi"}
    with patch.object(
        mod,
        "send_grok_chat",
        return_value=mod.ChannelResult("grok", ok=True, detail="http=200"),
    ):
        with patch.object(mod, "send_claude_chat") as claude:
            ok, results = mod.deliver_chat_chain(rem, env={})
    assert ok is True
    assert results[0].channel == "grok"
    claude.assert_not_called()


def test_slack_runs_after_grok_fail_even_without_token():
    rem = {"id": "r1", "message": "hi"}
    env = {}
    with patch.object(
        mod,
        "send_grok_chat",
        return_value=mod.ChannelResult("grok", ok=False, detail="no key"),
    ):
        with patch.object(
            mod,
            "send_claude_chat",
            return_value=mod.ChannelResult("claude", ok=False, skipped=True),
        ):
            ok, results = mod.deliver_chat_chain(
                rem,
                env=env,
                slack_token="",
                format_text=lambda r: r["message"],
                post_message=lambda *a: "ts",
                resolve_dm_channel=lambda t: "D1",
            )
    assert ok is False
    assert [r.channel for r in results] == ["grok", "claude", "slack"]
    assert results[2].skipped is True
