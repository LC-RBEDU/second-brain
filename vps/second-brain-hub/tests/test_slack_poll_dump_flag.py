"""T1 / B1–B2 — SLACK_POLL_DUMP=0 → no-op, 0 write."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "lib"))

_SPEC = importlib.util.spec_from_file_location(
    "slack_poll", HUB / "cron" / "slack_poll.py"
)
assert _SPEC and _SPEC.loader
slack_poll = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(slack_poll)


def test_dump_disabled_exits_without_write(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("SLACK_POLL_DUMP", "0")
    # If dump were on, missing token would still skip — assert early dump message.
    monkeypatch.delenv("SLACK_USER_TOKEN", raising=False)
    slack_poll.main()
    out = capsys.readouterr().out
    assert "dump disabled" in out
    assert not list(tmp_path.rglob("*.md"))


def test_dump_enabled_default_true(monkeypatch):
    monkeypatch.delenv("SLACK_POLL_DUMP", raising=False)
    assert slack_poll._dump_enabled() is True
    monkeypatch.setenv("SLACK_POLL_DUMP", "false")
    assert slack_poll._dump_enabled() is False
