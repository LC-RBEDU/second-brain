"""T3 — sembly template + filename (no vault)."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.sembly_template import filename_for, render_markdown  # noqa: E402


def test_render_has_no_llm_marker_and_sections():
    md = render_markdown(
        {
            "id": "abc",
            "meeting": {
                "title": "Sync",
                "start_time": "2026-10-11T10:00:00",
                "participants": [{"name": "Lukáš"}],
                "duration_minutes": 30,
                "permalink": "https://sembly.ai/x",
            },
            "summary": "hello",
            "action_items": ["do thing"],
            "transcript": "hi",
        }
    )
    assert "## Shrnutí" in md
    assert "hello" in md
    assert "**Trvání**: 30 min" in md
    assert "llm" not in md.casefold()
    assert filename_for({"meeting": {"title": "Sync", "start_time": "2026-10-11T10:00:00"}}).endswith(
        "-Sync.md"
    )


def test_legacy_started_at_and_full_transcript():
    payload = {
        "meeting": {"title": "X", "started_at": "2026-10-11T10:30:00"},
        "full_transcript": "legacy full",
    }
    assert "2026-10-11-1030" in filename_for(payload)
    assert "legacy full" in render_markdown(payload)
