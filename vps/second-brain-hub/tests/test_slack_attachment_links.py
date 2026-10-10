"""T11 / B14: slack attachment links — no Drive URL on git backend."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_CRON = Path(__file__).resolve().parents[1] / "cron"
sys.path.insert(0, str(_CRON))

from slack_poll import attachment_markdown_link  # noqa: E402


def test_git_backend_uses_permalink_not_drive():
    meta = SimpleNamespace(id="abc", oid="deadbeef")
    line = attachment_markdown_link(
        name="a.pdf",
        rel="01-INBOX/slack/x__1-a.pdf",
        meta=meta,
        permalink="https://slack.com/files/T/F/a.pdf",
        backend="git",
    )
    assert "drive.google.com" not in line
    assert "slack.com/files" in line


def test_git_backend_falls_back_to_vault_rel():
    meta = SimpleNamespace(id="oidish", oid="abc123")
    line = attachment_markdown_link(
        name="b.png",
        rel="01-INBOX/slack/y__1-b.png",
        meta=meta,
        permalink="",
        backend="git",
    )
    assert "drive.google.com" not in line
    assert "01-INBOX/slack/y__1-b.png" in line


def test_drive_backend_uses_drive_url():
    meta = SimpleNamespace(id="1DriveFileId", oid=None)
    line = attachment_markdown_link(
        name="c.bin",
        rel="01-INBOX/slack/z__1-c.bin",
        meta=meta,
        permalink="https://slack.com/x",
        backend="drive",
    )
    assert "drive.google.com/file/d/1DriveFileId/view" in line
