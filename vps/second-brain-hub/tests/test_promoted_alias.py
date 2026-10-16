"""Alias window and queue hiding for a story that still has an open task."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from promoted_alias import alias_state  # noqa: E402
from today_priority import is_queue_eligible, parents_with_open_task_children, select_top_priority  # noqa: E402

TODAY = date(2026, 10, 16)


def test_alias_window_includes_day_90_and_stops_on_day_91():
    applied = date(2026, 10, 1)
    assert alias_state(date(2026, 12, 30), applied) == "active"
    assert alias_state(date(2026, 12, 31), applied) == "expired"
    assert alias_state(TODAY, None) == "inactive"


def test_story_with_open_child_leaves_the_wider_queue():
    story = {"id": "RBU-S1", "type": "story", "status": "Doing", "slug": "rb-universe-development"}
    child = {
        "id": "RBU-T2",
        "type": "task",
        "status": "Next",
        "parent": "[[RBU-S1 — Story]]",
        "slug": "rb-universe-development",
    }
    hidden = parents_with_open_task_children([story, child])
    assert hidden == {"RBU-S1"}
    assert is_queue_eligible(story, TODAY, open_child_parents=hidden) is False
    assert is_queue_eligible(child, TODAY, open_child_parents=hidden) is True
    _today, wider = select_top_priority([story, child], TODAY)
    assert [item["id"] for item in wider] == ["RBU-T2"]
