"""Deadline inequality: parent day is on or after every open descendant."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from deadline_order import DeadlineNode, evaluate_deadline_order  # noqa: E402


def _nodes() -> list[DeadlineNode]:
    return [
        DeadlineNode("E1", None, "Doing", "2026-10-20"),
        DeadlineNode("S1", "E1", "Next", None),
        DeadlineNode("T1", "S1", "Next", "2026-10-18"),
        DeadlineNode("T2", "S1", "Done", "2026-10-25"),
    ]


def test_same_day_passes():
    out = evaluate_deadline_order(_nodes(), {"E1": "2026-10-18"})
    assert out["ok"] is True


def test_parent_earlier_than_open_descendant_is_rejected():
    out = evaluate_deadline_order(_nodes(), {"E1": "2026-10-17"})
    assert out["ok"] is False
    assert out["code"] == "deadline_order"
    assert out["conflicts"][0]["parent_id"] == "E1"
    assert out["conflicts"][0]["child_id"] == "T1"
    actions = {item["action"] for item in out["options"]}
    assert actions == {"move_child_earlier", "move_parent_later"}


def test_story_without_date_does_not_hide_the_task():
    out = evaluate_deadline_order(_nodes(), {"T1": "2026-10-21"})
    assert out["ok"] is False
    assert out["conflicts"][0]["parent_id"] == "E1"
    assert out["conflicts"][0]["child_id"] == "T1"


def test_done_descendant_does_not_count():
    out = evaluate_deadline_order(_nodes(), {"E1": "2026-10-18"})
    assert out["ok"] is True


def test_clearing_parent_deadline_is_allowed():
    out = evaluate_deadline_order(_nodes(), {"E1": None})
    assert out["ok"] is True


def test_later_parent_on_or_after_the_max_passes_without_the_flag():
    nodes = [
        DeadlineNode("E1", None, "Doing", "2026-10-20"),
        DeadlineNode("T1", "E1", "Next", "2026-10-18"),
    ]
    out = evaluate_deadline_order(nodes, {"E1": "2026-10-25"}, allow_parent_shift=False)
    assert out["ok"] is True


def test_allow_parent_shift_still_rejects_a_date_before_the_child():
    nodes = [
        DeadlineNode("E1", None, "Doing", "2026-10-10"),
        DeadlineNode("T1", "E1", "Next", "2026-10-18"),
    ]
    out = evaluate_deadline_order(nodes, {"E1": "2026-10-17"}, allow_parent_shift=True)
    assert out["ok"] is False


def test_shift_flag_accepts_any_day_on_or_after_the_max():
    nodes = [
        DeadlineNode("E1", None, "Doing", "2026-10-10"),
        DeadlineNode("T1", "E1", "Next", "2026-10-18"),
    ]
    out = evaluate_deadline_order(nodes, {"E1": "2026-10-19"}, allow_parent_shift=True)
    assert out["ok"] is True


def test_narrow_cone_ignores_a_sibling_and_keeps_a_descendant():
    nodes = [
        DeadlineNode("E", None, "Doing", "2026-10-20"),
        DeadlineNode("S", "E", "Next", "2026-10-25"),
        DeadlineNode("T", "E", "Next", "2026-10-18"),
        DeadlineNode("D", "T", "Next", "2026-10-18"),
    ]
    sibling = evaluate_deadline_order(nodes, touched_ids={"T"})
    assert sibling["ok"] is True
    whole = evaluate_deadline_order(nodes)
    assert whole["ok"] is False
    broken = [
        DeadlineNode("E", None, "Doing", "2026-10-20"),
        DeadlineNode("T", "E", "Next", "2026-10-18"),
        DeadlineNode("D", "T", "Next", "2026-10-25"),
    ]
    descendant = evaluate_deadline_order(broken, touched_ids={"T"})
    assert descendant["ok"] is False
    assert descendant["conflicts"][0]["child_id"] == "D"
