"""Tests for hierarchy + GitHub Closes parsing."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from github_rbu_closes import (  # noqa: E402
    apply_close_action,
    classify_ref,
    extract_actions_from_text,
)
from hierarchy import (  # noqa: E402
    is_epic,
    is_focusable,
    mark_checkbox_done,
    normalise_work_type,
    parse_closes_refs,
    parse_parent_id,
    project_uses_hierarchy,
    split_subtask_ref,
)
from today_priority import is_focus_eligible, is_queue_eligible, select_top_priority  # noqa: E402

TODAY = date(2026, 9, 2)  # ISO 2026-W36


def test_normalise_work_type():
    assert normalise_work_type("epic") == "epic"
    assert normalise_work_type("STORY") == "story"
    assert normalise_work_type(None) == "task"
    assert normalise_work_type("weird") == "task"


def test_parse_parent_id():
    assert parse_parent_id("[[RBU23 — MVP karet]]") == "RBU23"
    assert parse_parent_id("[[RBU23]]") == "RBU23"
    assert parse_parent_id("RBU23") == "RBU23"
    assert parse_parent_id("RBU23 — Title") == "RBU23"
    assert parse_parent_id(None) is None


def test_project_uses_hierarchy():
    assert project_uses_hierarchy("rb-universe-development") is True
    assert project_uses_hierarchy("finance") is False
    assert project_uses_hierarchy("finance", hub_frontmatter={"hierarchy": True}) is True
    assert project_uses_hierarchy("finance", slug_has_epic=True) is True


def test_closes_refs():
    text = "feat: MCP tools\n\nCloses RBU62-1\nAlso fixes RBU62-2 and Resolves RBU61"
    assert parse_closes_refs(text) == ["RBU62-1", "RBU62-2", "RBU61"]


def test_split_and_classify():
    assert split_subtask_ref("RBU62-1") == ("RBU62", "1")
    assert split_subtask_ref("RBU62") is None
    a = classify_ref("RBU62-3")
    assert a.kind == "subtask" and a.task_id == "RBU62" and a.subtask_num == "3"
    b = classify_ref("RBU62")
    assert b.kind == "story" and b.task_id == "RBU62"


def test_mark_checkbox_done():
    body = "## Operativní kroky\n- [ ] **RBU62-1** Přidat MCP\n- [ ] **RBU62-2** Návod\n"
    new, changed = mark_checkbox_done(body, "RBU62", "1")
    assert changed
    assert "- [x] **RBU62-1**" in new
    assert "- [ ] **RBU62-2**" in new
    new2, changed2 = mark_checkbox_done(new, "RBU62", "1")
    assert not changed2


def test_epic_excluded_from_priority():
    epic = {
        "id": "RBU23",
        "type": "epic",
        "status": "Next",
        "focus": "2026-W36",
        "ice_i": 9,
        "ice_c": 9,
        "ice_e": 1,
        "title": "Epic",
    }
    story = {
        "id": "RBU62",
        "type": "story",
        "status": "Next",
        "focus": "2026-W36",
        "ice_i": 7,
        "ice_c": 7,
        "ice_e": 3,
        "title": "Story",
    }
    assert is_epic(epic) and not is_focusable(epic)
    assert is_focus_eligible(story, TODAY)
    assert not is_focus_eligible(epic, TODAY)
    assert not is_queue_eligible(epic, TODAY)
    today_list, general = select_top_priority([epic, story], TODAY)
    ids_today = [t["id"] for t in today_list]
    ids_gen = [t["id"] for t in general]
    assert "RBU62" in ids_today
    assert "RBU23" not in ids_today
    assert "RBU23" not in ids_gen


def test_extract_actions_ignores_non_rbu():
    acts = extract_actions_from_text("Closes AF14 and Closes RBU58-1")
    assert [a.ref for a in acts] == ["RBU58-1"]


class _FakeVault:
    def __init__(self):
        self.writes: list[tuple[str, str]] = []

    def write_text(self, rel_path, text, expect_mtime=None):
        self.writes.append((rel_path, text))


def _story_task(body: str, *, work_type: str = "story", status: str = "Next"):
    return SimpleNamespace(
        frontmatter={
            "id": "RBU62",
            "type": work_type,
            "status": status,
            "slug": "rb-universe-development",
            "title": "MCP",
        },
        body=body,
        rel_path="02-PROJEKTY/rb-universe-development/tasks/RBU62 — MCP.md",
        meta=SimpleNamespace(modified_time="2026-09-01T00:00:00Z"),
        is_terminal=(status in {"Done", "Cancelled"}),
    )


def test_apply_close_subtask_then_story_when_last():
    vault = _FakeVault()
    body = "## Operativní kroky\n- [ ] **RBU62-1** A\n- [x] **RBU62-2** B\n"
    task = _story_task(body)
    action = classify_ref("RBU62-1")
    action.sha = "abc"
    result, detail = apply_close_action(vault, task, action, today_str="2026-09-02")
    assert result == "applied"
    assert vault.writes
    written = vault.writes[0][1]
    assert "- [x] **RBU62-1**" in written
    assert "status: Done" in written


def test_apply_close_story_blocked_by_open_checkboxes():
    vault = _FakeVault()
    task = _story_task("## Operativní kroky\n- [ ] **RBU62-1** A\n")
    action = classify_ref("RBU62")
    result, detail = apply_close_action(vault, task, action, today_str="2026-09-02")
    assert result == "skipped"
    assert "open checkboxes" in detail
    assert not vault.writes


def test_apply_close_epic_blocked():
    vault = _FakeVault()
    task = _story_task("", work_type="epic")
    action = classify_ref("RBU62")
    result, _ = apply_close_action(vault, task, action, today_str="2026-09-02")
    assert result == "epic_blocked"
    assert not vault.writes
