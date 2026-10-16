"""A blocked rotation stays in tasks/. A story with an open child is not auto-done."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_HUB = Path(__file__).resolve().parents[1]
for folder in (_HUB / "lib", _HUB / "cron"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from lifecycle_done_from_checkboxes import should_auto_done  # noqa: E402
from lifecycle_recurring import rotation_blocked  # noqa: E402


def _task(**fm):
    body = fm.pop("body", "- [x] **RBU-S7-1** hotovo\n")
    path = fm.pop("path", "02-PROJEKTY/rb-universe-development/tasks/RBU-S7 — Story.md")
    item = SimpleNamespace(
        frontmatter=fm,
        body=body,
        rel_path=path,
        is_terminal=fm.get("status") in {"Done", "Cancelled"},
        task_id=fm.get("id"),
    )
    return item


def test_rotation_blocked_leaves_the_tasks_path_alone():
    story = _task(
        id="RBU-S7",
        type="story",
        status="Done",
        slug="rb-universe-development",
        deadline="2026-10-01",
        recurring={"frequency": "weekly", "weekday": "thursday"},
        parent="[[RBU-E1]]",
    )
    epic = _task(id="RBU-E1", type="epic", status="Doing", deadline="2026-10-02", slug="rb-universe-development", body="")
    blocked, _next, _order = rotation_blocked(story, [epic, story], date(2026, 10, 16))
    assert blocked is True
    assert story.rel_path.startswith("02-PROJEKTY/")


def test_story_with_open_child_is_not_auto_done():
    story = _task(id="RBU-S7", type="story", status="Doing", slug="rb-universe-development")
    child = _task(
        id="RBU-T1",
        type="task",
        status="Next",
        parent="[[RBU-S7]]",
        slug="rb-universe-development",
        body="",
    )
    assert should_auto_done(story, [story, child]) is False
