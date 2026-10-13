"""T1 — Sembly webhook field mapping (no vault)."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.sembly_template import filename_for, render_markdown  # noqa: E402
from app.tools import ingest_sembly as ingest_mod  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402


class _FakeVault:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.mkdirs: list[str] = []

    def exists(self, rel: str) -> bool:
        return rel in self.files

    def mkdir_p(self, rel: str) -> None:
        self.mkdirs.append(rel)

    def write_text(self, rel: str, body: str, **_kw) -> None:
        self.files[rel] = body

    def read_text(self, rel: str):
        return self.files[rel], MagicMock(oid="x")


def test_webhook_fields_filename_and_md():
    payload = {
        "meeting_id": "meet-wh-1",
        "meeting_title": "Finance Sync",
        "meeting_started_at": "2026-10-13T11:15:00+02:00",
        "meeting_transcription": "hello transcript",
        "duration": 2700,
        "attendees": [{"name": "Anna"}, "Bob"],
    }
    name = filename_for(payload)
    assert name.startswith("2026-10-13-1115-")
    assert "Finance" in name or "Sync" in name
    assert not name.startswith("unknown-time")
    md = render_markdown(payload)
    assert "Finance Sync" in md
    assert "**Trvání**: 45 min" in md
    assert "hello transcript" in md
    assert "Anna" in md and "Bob" in md
    assert "llm" not in md.casefold()


def test_duration_minutes_wins_over_seconds():
    md = render_markdown(
        {
            "meeting_title": "X",
            "meeting_started_at": "2026-10-13T12:00:00",
            "duration_minutes": 30,
            "duration": 2700,
        }
    )
    assert "**Trvání**: 30 min" in md


def test_top_level_meeting_title_beats_nested_title():
    md = render_markdown(
        {
            "meeting_title": "A",
            "meeting": {"title": "B", "start_time": "2026-10-13T10:00:00"},
        }
    )
    assert "# A —" in md
    assert "# B —" not in md


def test_started_at_and_full_transcript_legacy():
    payload = {
        "meeting": {
            "title": "Legacy",
            "started_at": "2026-10-11T10:00:00",
        },
        "full_transcript": "full text here",
    }
    assert filename_for(payload).startswith("2026-10-11-1000-")
    md = render_markdown(payload)
    assert "full text here" in md


def test_whitespace_title_falls_through():
    name = filename_for(
        {
            "meeting_title": "   ",
            "title": "Real Title",
            "meeting_started_at": "2026-10-13T09:00:00",
        }
    )
    assert "Real" in name or "Title" in name


def test_ingest_webhook_writes_stamped_path():
    vault = _FakeVault()

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    payload = {
        "meeting_id": "meet-wh-2",
        "meeting_title": "Sync",
        "meeting_started_at": "2026-10-13T11:15:00",
        "meeting_transcription": "t",
    }
    with patch.object(ingest_mod, "brain_vault", return_value=_CM()):
        r = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
    assert r["deduped"] is False
    assert "unknown-time" not in r["path"]
    assert "2026-10-13-1115" in r["path"]
