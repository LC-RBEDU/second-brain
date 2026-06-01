"""Unit tests for lifecycle_promotion helpers."""
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
    TARGET_ASAP_COUNT,
    default_wait_until,
    has_wait_until_value,
    select_next_for_asap_promotion,
    task_today_score,
)


def _task(ice_i, ice_c, ice_e, deadline=None, tid="T1"):
    return SimpleNamespace(
        frontmatter={
            "ice_i": ice_i,
            "ice_c": ice_c,
            "ice_e": ice_e,
            "deadline": deadline,
            "id": tid,
        }
    )


def test_default_wait_until_plus_three_days():
    today = date(2026, 5, 28)
    assert default_wait_until(today).isoformat() == "2026-05-31"
    assert DEFAULT_WAIT_UNTIL_DAYS == 3


def test_has_wait_until_value():
    assert has_wait_until_value(None) is False
    assert has_wait_until_value("") is False
    assert has_wait_until_value("2026-06-01") is True
    assert has_wait_until_value(date(2026, 6, 1)) is True


def test_select_next_promotes_by_today_score():
    today = date(2026, 5, 28)
    low = _task(5, 5, 5, tid="low")
    high = _task(9, 9, 3, deadline="2026-05-28", tid="high")
    mid = _task(7, 7, 5, tid="mid")

    picked = select_next_for_asap_promotion(
        [low, high, mid],
        today=today,
        current_asap_count=1,
        target_asap=3,
    )
    assert len(picked) == 2
    assert picked[0].frontmatter["id"] == "high"
    assert picked[1].frontmatter["id"] == "mid"
    assert TARGET_ASAP_COUNT == 3


def test_select_next_no_promotion_when_asap_full():
    today = date(2026, 5, 28)
    assert (
        select_next_for_asap_promotion(
            [_task(9, 9, 1)],
            today=today,
            current_asap_count=3,
        )
        == []
    )


def test_task_today_score_adds_overdue_bonus():
    today = date(2026, 5, 28)
    base = task_today_score({"ice_i": 5, "ice_c": 5, "ice_e": 5}, today)
    overdue = task_today_score(
        {"ice_i": 5, "ice_c": 5, "ice_e": 5, "deadline": "2026-05-27"},
        today,
    )
    assert overdue == base + 35


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all passed")
