"""F5 — Brain-first docs (T5 / T6 / T7)."""
from __future__ import annotations

import os

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_t5_guide_brain_first():
    vault = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault"))
    if not vault.is_dir():
        import pytest

        pytest.skip("vault není na tomhle stroji")
    text = (vault / "00-System" / "agent-guide-mimo-cursor.md").read_text(encoding="utf-8")
    assert "Brain" in text or "brain.cyprovi.cz" in text
    assert "create_task" in text or "capture_daily" in text
    assert "01-INBOX/slack" in text
    assert "dump" in text.lower()


def test_t6_cowork_brain_and_dump_off():
    text = (REPO / "cowork-instructions.md").read_text(encoding="utf-8")
    assert "second-brain-vault/00-System/agent-guide-mimo-cursor.md" in text
    assert "Brain" in text or "brain" in text.lower()
    assert "01-INBOX/slack" in text
    assert "dump off" in text.lower() or "ne zapisuj" in text.lower()


def test_t7_morning_schedule_not_light_primary():
    prompt = (REPO / "ŠABLONY" / "cowork-morning-brief.md").read_text(encoding="utf-8")
    assert "agenda-co-ted" in prompt
    assert "NOT follow agenda-co-ted" in prompt or "do NOT follow agenda-co-ted" in prompt
    assert "light" in prompt.lower()
    assert "agent-context.json" in prompt
    assert "get_context" in prompt
    assert "/v1/context/light" in prompt
    assert "Do not run build_agent_context.py" in prompt
    assert "Do not write" in prompt and "Slack" in prompt
