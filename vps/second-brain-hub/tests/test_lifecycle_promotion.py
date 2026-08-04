"""Unit tests for lifecycle_promotion helpers (priority model v2)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from lifecycle_promotion import (  # noqa: E402
    DEFAULT_WAIT_UNTIL_DAYS,
    FOCUS_TARGET,
    count_focused,
    default_wait_until,
    has_wait_until_value,
    select_focus_suggestions,
    task_today_score,
)
from today_priority import URGENCY_BONUS_OVERDUE  # noqa: E402

TODAY = date(2026, 8, 4)  # 2026-W32


def _task(ice_i, ice_c, ice_e, deadline=None, tid="T1", focus=None):
    return SimpleNamespace(
        frontmatter={
            "ice_i": ice_i,
            "ice_c": ice_c,
            "ice_e": ice_e,
            "deadline": deadline,
            "focus": focus,
            "id": tid,
        }
    )


def test_default_wait_until_plus_three_days():
    assert default_wait_until(date(2026, 5, 28)).isoformat() == "2026-05-31"
    assert DEFAULT_WAIT_UNTIL_DAYS == 3


def test_has_wait_until_value():
    assert has_wait_until_value(None) is False
    assert has_wait_until_value("") is False
    assert has_wait_until_value("2026-06-01") is True
    assert has_wait_until_value(date(2026, 6, 1)) is True


def test_focus_target_is_five():
    assert FOCUS_TARGET == 5


def test_count_focused_only_counts_current_week():
    tasks = [
        _task(5, 5, 5, focus="2026-W32", tid="now"),
        _task(5, 5, 5, focus="2026-W31", tid="last-week"),
        _task(5, 5, 5, focus=None, tid="none"),
    ]
    assert count_focused(tasks, TODAY) == 1


def test_suggestions_ranked_by_today_score():
    low = _task(5, 5, 5, tid="low")
    high = _task(9, 9, 3, deadline="2026-08-04", tid="high")
    mid = _task(7, 7, 5, tid="mid")

    picked = select_focus_suggestions(
        [low, high, mid],
        today=TODAY,
        current_focus_count=3,
    )
    assert [t.frontmatter["id"] for t in picked] == ["high", "mid"]


def test_no_suggestions_when_focus_is_full():
    assert (
        select_focus_suggestions(
            [_task(9, 9, 1)],
            today=TODAY,
            current_focus_count=FOCUS_TARGET,
        )
        == []
    )


def test_overdue_no_longer_dominates_score():
    """Rot must not climb the list: overdue is a tiebreaker, not a jackpot."""
    base = task_today_score({"ice_i": 5, "ice_c": 5, "ice_e": 5}, TODAY)
    overdue = task_today_score(
        {"ice_i": 5, "ice_c": 5, "ice_e": 5, "deadline": "2026-07-01"},
        TODAY,
    )
    due_today = task_today_score(
        {"ice_i": 5, "ice_c": 5, "ice_e": 5, "deadline": "2026-08-04"},
        TODAY,
    )
    assert overdue == base + URGENCY_BONUS_OVERDUE
    assert URGENCY_BONUS_OVERDUE == 5
    assert due_today > overdue


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all passed")
