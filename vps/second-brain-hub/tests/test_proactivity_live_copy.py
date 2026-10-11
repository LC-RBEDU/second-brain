"""T18 / B26 — proactivity CTA = live triáž, not slack_dump≈N."""
from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "cron" / "proactivity_dispatch.py"


def test_message_live_triage_not_dump_count():
    text = SRC.read_text(encoding="utf-8")
    assert "jdi do live triáže" in text
    assert "slack_dump≈" not in text
    assert "live triáže" in text
