"""Unit tests for the focus week vocabulary and focus-based top priority."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from focus import (  # noqa: E402
    FOCUS_LIMIT,
    STATUS_CANCELLED,
    STATUS_DONE,
    TERMINAL_STATUSES,
    current_focus_week,
    is_focus_current,
    is_terminal,
    iso_week,
    normalise_agent,
    parse_focus,
)
from today_priority import (  # noqa: E402
    is_focus_eligible,
    is_queue_eligible,
    select_top_priority,
)

TODAY = date(2026, 8, 4)  # Tuesday of ISO week 2026-W32


def _t(tid, *, status="Next", focus=None, ice=(5, 5, 5), deadline=None):
    return {
        "id": tid,
        "status": status,
        "focus": focus,
        "deadline": deadline,
        "ice_i": ice[0],
        "ice_c": ice[1],
        "ice_e": ice[2],
        "title": tid,
    }


def test_iso_week_pads_single_digit():
    assert iso_week(date(2026, 1, 8)) == "2026-W02"
    assert iso_week(TODAY) == "2026-W32"
    assert current_focus_week(TODAY) == "2026-W32"


def test_parse_focus_normalises_and_rejects_garbage():
    assert parse_focus("2026-W7") == "2026-W07"
    assert parse_focus("2026-W32") == "2026-W32"
    assert parse_focus(None) is None
    assert parse_focus("null") is None
    assert parse_focus("tento týden") is None
    assert parse_focus("2026-W54") is None


def test_is_focus_current():
    assert is_focus_current("2026-W32", TODAY) is True
    assert is_focus_current("2026-W31", TODAY) is False
    assert is_focus_current(None, TODAY) is False


def test_terminal_statuses_include_cancelled():
    assert TERMINAL_STATUSES == {STATUS_DONE, STATUS_CANCELLED}
    assert is_terminal("Cancelled") is True
    assert is_terminal("Next") is False


def test_normalise_agent_defaults_to_none():
    assert normalise_agent("solo") == "solo"
    assert normalise_agent("ASSIST") == "assist"
    assert normalise_agent(None) == "none"
    assert normalise_agent("nesmysl") == "none"


def test_focus_eligibility_ignores_waiting_and_backlog():
    assert is_focus_eligible(_t("a", focus="2026-W32"), TODAY) is True
    assert is_focus_eligible(_t("b", focus="2026-W32", status="Waiting"), TODAY) is False
    assert is_focus_eligible(_t("c", focus="2026-W32", status="Backlog"), TODAY) is False
    assert is_focus_eligible(_t("d", focus="2026-W32", status="Cancelled"), TODAY) is False
    assert is_focus_eligible(_t("e", focus="2026-W31"), TODAY) is False


def test_queue_eligibility_covers_doing_and_next():
    assert is_queue_eligible(_t("a", status="Doing"), TODAY) is True
    assert is_queue_eligible(_t("b", status="Next"), TODAY) is True
    assert is_queue_eligible(_t("c", status="Backlog"), TODAY) is False
    assert is_queue_eligible(_t("d", status="Backlog", focus="2026-W32"), TODAY) is False


def test_top_today_comes_only_from_current_focus():
    tasks = [
        _t("focus-low", focus="2026-W32", ice=(3, 3, 5)),
        _t("focus-high", focus="2026-W32", ice=(9, 9, 3)),
        _t("next-huge", ice=(10, 10, 1)),
        _t("stale-focus", focus="2026-W31", status="Backlog", ice=(10, 10, 1)),
    ]
    top_today, top_general = select_top_priority(tasks, TODAY)

    assert [t["id"] for t in top_today] == ["focus-high", "focus-low"]
    # Last week's pick expires on its own; a high score does not bring it back.
    assert "stale-focus" not in [t["id"] for t in top_today]
    assert "next-huge" in [t["id"] for t in top_general]
    assert "stale-focus" not in [t["id"] for t in top_general]


def test_top_today_is_capped_at_focus_limit():
    tasks = [_t(f"f{i}", focus="2026-W32", ice=(9, 9, 1)) for i in range(9)]
    top_today, _ = select_top_priority(tasks, TODAY)
    assert len(top_today) == FOCUS_LIMIT == 5


def test_top_today_empty_when_nothing_is_focused():
    tasks = [_t("a"), _t("b", status="Doing")]
    top_today, top_general = select_top_priority(tasks, TODAY)
    assert top_today == []
    assert len(top_general) == 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all passed")
