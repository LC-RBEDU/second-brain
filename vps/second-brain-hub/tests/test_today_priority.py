"""Unit tests for effective_due + split urgency (priority model v2.1)."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from today_priority import (
    URGENCY_BONUS_OVERDUE,
    URGENCY_BONUS_REVIEW_TODAY,
    URGENCY_BONUS_REVIEW_TOMORROW,
    URGENCY_BONUS_TODAY,
    URGENCY_BONUS_TOMORROW,
    effective_due,
    needs_decision,
    today_score,
    urgency_bonus,
)

TODAY = date(2026, 9, 20)


def test_effective_due_min_of_both():
    assert effective_due("2026-09-25", "2026-09-22") == date(2026, 9, 22)
    assert effective_due("2026-09-21", "2026-09-28") == date(2026, 9, 21)


def test_effective_due_single_axis():
    assert effective_due("2026-09-25", None) == date(2026, 9, 25)
    assert effective_due(None, "2026-09-22") == date(2026, 9, 22)
    assert effective_due(None, None) is None


def test_urgency_external_outranks_review_same_day():
    # Both today → external +30 wins over review +20
    assert urgency_bonus("2026-09-20", TODAY, "2026-09-20") == URGENCY_BONUS_TODAY


def test_urgency_review_when_no_external():
    assert urgency_bonus(None, TODAY, "2026-09-20") == URGENCY_BONUS_REVIEW_TODAY
    assert urgency_bonus(None, TODAY, "2026-09-21") == URGENCY_BONUS_REVIEW_TOMORROW


def test_urgency_external_tomorrow_beats_review_overdue():
    # External tomorrow +15 > review overdue +5
    assert (
        urgency_bonus("2026-09-21", TODAY, "2026-09-10")
        == URGENCY_BONUS_TOMORROW
    )


def test_urgency_overdue_tiebreak():
    assert urgency_bonus("2026-09-10", TODAY, None) == URGENCY_BONUS_OVERDUE
    assert urgency_bonus(None, TODAY, "2026-09-10") == URGENCY_BONUS_OVERDUE


def test_today_score_includes_review():
    # priority 10 + review today 20 = 30
    assert today_score(10.0, None, TODAY, "2026-09-20") == 30.0
    # priority 10 + external today 30 = 40
    assert today_score(10.0, "2026-09-20", TODAY, "2026-09-20") == 40.0


def test_needs_decision_due_past():
    task = {
        "status": "Next",
        "deadline": None,
        "review_deadline": "2026-09-18",
    }
    assert needs_decision(task, TODAY) is True


def test_needs_decision_skips_waiting_and_future():
    waiting = {
        "status": "Waiting",
        "deadline": "2026-09-10",
        "review_deadline": None,
    }
    future = {
        "status": "Next",
        "deadline": (TODAY + timedelta(days=3)).isoformat(),
        "review_deadline": None,
    }
    assert needs_decision(waiting, TODAY) is False
    assert needs_decision(future, TODAY) is False
