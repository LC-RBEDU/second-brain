"""Overlay parent checks. No vault write."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.errors import BrainClientError  # noqa: E402
from app.tools.parent_link import check_overlay, needs_forest  # noqa: E402


def _task(task_id: str, work_type: str, parent: str | None, status: str = "Next"):
    return SimpleNamespace(
        frontmatter={
            "id": task_id,
            "type": work_type,
            "parent": parent,
            "status": status,
        },
        rel_path=f"02-PROJEKTY/demo/tasks/{task_id}.md",
    )


def test_pure_done_does_not_need_the_forest():
    assert needs_forest({"status": "Done"}) is False
    assert needs_forest({"status": "Done", "parent": ""}) is True


def test_done_plus_empty_parent_on_a_story_is_required():
    story = _task("S1", "story", "[[E1]]")
    epic = _task("E1", "epic", None)
    with pytest.raises(BrainClientError) as ei:
        check_overlay(
            [story, epic],
            [{"id": "S1", "patch": {"status": "Done", "parent": ""}}],
        )
    assert ei.value.error_reason == "parent_required"
    assert ei.value.detail["errors"] == ["parent_required"]


def test_bare_epic_conversion_returns_both_reasons():
    epic = _task("E0", "epic", None)
    story = _task("S1", "story", "[[E0]]")
    child = _task("T1", "task", "[[S1]]", status="Next")
    with pytest.raises(BrainClientError) as ei:
        check_overlay(
            [epic, story, child],
            [{"id": "S1", "patch": {"type": "epic"}}],
        )
    assert ei.value.error_reason == "epic_has_no_parent"
    assert ei.value.detail["errors"] == ["epic_has_no_parent", "parent_not_story"]


def test_cleared_parent_and_open_child_is_only_the_child():
    epic = _task("E0", "epic", None)
    story = _task("S1", "story", "[[E0]]")
    child = _task("T1", "task", "[[S1]]")
    with pytest.raises(BrainClientError) as ei:
        check_overlay(
            [epic, story, child],
            [{"id": "S1", "patch": {"type": "epic", "parent": ""}}],
        )
    assert ei.value.detail["errors"] == ["parent_not_story"]


def test_combined_bulk_reports_the_child_once():
    epic = _task("E0", "epic", None)
    story = _task("S1", "story", "[[E0]]")
    child = _task("T1", "task", "[[S1]]", status="Done")
    with pytest.raises(BrainClientError) as ei:
        check_overlay(
            [epic, story, child],
            [
                {"id": "S1", "patch": {"type": "epic"}},
                {"id": "T1", "patch": {"status": "Next"}},
            ],
        )
    assert ei.value.detail["errors"] == ["epic_has_no_parent", "parent_not_story"]


def test_unreadable_parent_with_an_active_status_is_only_not_found():
    epic = _task("E1", "epic", None)
    story = _task("S1", "story", "[[E1]]")
    with pytest.raises(BrainClientError) as ei:
        check_overlay(
            [epic, story],
            [{"id": "S1", "patch": {"status": "Doing", "parent": "not an id"}}],
        )
    assert ei.value.error_reason == "parent_not_found"
    assert ei.value.detail["errors"] == ["parent_not_found"]
