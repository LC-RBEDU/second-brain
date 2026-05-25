"""Unit tests for `lifecycle_recurring.compute_next_deadline` and the
`last-weekday-before-day` helper functions.

The `last-weekday-before-day` frequency is a monthly anchor where the
deadline is the largest date in a month with day-of-month ≤ (day - 1)
that falls on the configured weekday. Useful e.g. for the CFO commentary
that must arrive on the last Friday before the 15th-of-the-month
strategic meeting.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_CRON = Path(__file__).resolve().parents[1] / "cron"
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

import lifecycle_recurring as mod  # noqa: E402


# ---------------------------------------------------------------------------
# next_last_weekday_before_day — core scenarios from the spec
# ---------------------------------------------------------------------------


def test_last_weekday_before_day_basic_friday_before_15th():
    """Test 1: today=2026-05-26, day=15, weekday=friday → 2026-06-12.

    In June 2026 the 15th is a Monday, so the last Friday with date ≤ 14
    is the 12th.
    """
    today = date(2026, 5, 26)
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2026, 6, 12)


def test_last_weekday_before_day_advances_to_next_month_when_current_passed():
    """Test 2: today=2026-06-13, day=15, weekday=friday → 2026-07-10.

    June target was 2026-06-12 which is already in the past relative to
    2026-06-13, so the function must advance one month. In July 2026 the
    15th is a Wednesday, so the last Friday with date ≤ 14 is the 10th.
    """
    today = date(2026, 6, 13)
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2026, 7, 10)


def test_last_weekday_before_day_skips_month_when_today_equals_anchor():
    """Test 3: today=2026-08-15, day=15, weekday=friday → 2026-09-11.

    In August 2026 the 15th is a Saturday and the last Friday with date ≤ 14
    is the 14th — but today is already the 15th, strictly past the August
    anchor. Function must roll over to September; in September 2026 the 15th
    is a Tuesday, so the last Friday with date ≤ 14 is the 11th.
    """
    today = date(2026, 8, 15)
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2026, 9, 11)


# ---------------------------------------------------------------------------
# Edge cases — month boundary, today equal to target, year roll-over
# ---------------------------------------------------------------------------


def test_last_weekday_before_day_today_equals_target_advances():
    """If today == this month's target, it is not strictly in the future,
    so we must return next month's target.
    """
    today = date(2026, 6, 12)  # the June target itself
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2026, 7, 10)


def test_last_weekday_before_day_today_before_target_returns_same_month():
    """If today is in the same month but before this month's target,
    we must return the same-month target."""
    today = date(2026, 6, 5)  # before 2026-06-12
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2026, 6, 12)


def test_last_weekday_before_day_year_rollover():
    """December → January roll-over still works correctly."""
    today = date(2026, 12, 20)
    # In January 2027 the 15th is a Friday — so the last Friday with date ≤ 14
    # is January 8 (Friday). Wait: Jan 2027 — let me check.
    # 2027-01-01 is a Friday. So Fridays in Jan 2027 ≤ 14: Jan 1, Jan 8.
    # → target = Jan 8, 2027.
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=4)
    assert out == date(2027, 1, 8)


def test_last_weekday_before_day_other_weekday():
    """Wednesday instead of Friday — sanity check the weekday_idx wiring."""
    # In June 2026 the 15th is a Monday. Wednesdays in June 2026 ≤ 14:
    # June 3, June 10. → target = June 10.
    today = date(2026, 5, 26)
    out = mod.next_last_weekday_before_day(today, day=15, weekday_idx=2)  # wednesday
    assert out == date(2026, 6, 10)


def test_last_weekday_before_day_cap_to_month_length():
    """day=31 in February should not crash — cutoff caps at Feb 28/29."""
    today = date(2026, 1, 30)
    # In Feb 2026 the cutoff caps at 28. Fridays in Feb 2026 ≤ 28:
    # Feb 6, 13, 20, 27. → target = Feb 27.
    out = mod.next_last_weekday_before_day(today, day=31, weekday_idx=4)
    assert out == date(2026, 2, 27)


# ---------------------------------------------------------------------------
# compute_next_deadline integration — exercises the YAML frontmatter path
# ---------------------------------------------------------------------------


def test_compute_next_deadline_routes_to_last_weekday_before_day():
    """`compute_next_deadline` should dispatch on `frequency` and call
    the new rule with the correct args.
    """
    rec = {
        "frequency": "last-weekday-before-day",
        "day": 15,
        "weekday": "friday",
    }
    out = mod.compute_next_deadline(rec, last_deadline=None, today=date(2026, 5, 26))
    assert out == date(2026, 6, 12)


def test_compute_next_deadline_misconfigured_falls_back_safely():
    """Missing weekday → fallback to +30 days so the cron still rotates
    the task and surfaces the problem (rather than crashing the whole run)."""
    rec = {"frequency": "last-weekday-before-day", "day": 15}
    today = date(2026, 5, 26)
    out = mod.compute_next_deadline(rec, last_deadline=None, today=today)
    assert (out - today).days == 30


def test_compute_next_deadline_existing_frequencies_unchanged():
    """Smoke test that the existing weekday rule still works after the change."""
    rec = {"frequency": "weekday", "weekday": "thursday"}
    today = date(2026, 5, 26)  # Tuesday
    out = mod.compute_next_deadline(rec, last_deadline=None, today=today)
    # Next Thursday after Tuesday 2026-05-26 is 2026-05-28.
    assert out == date(2026, 5, 28)


# ---------------------------------------------------------------------------
# Helper-level test — _last_weekday_before_day_in_month
# ---------------------------------------------------------------------------


def test_last_weekday_before_day_in_month_returns_none_for_day_lte_1():
    """day must be ≥ 2 (else cutoff < 1 — no valid date)."""
    assert mod._last_weekday_before_day_in_month(2026, 6, 1, 4) is None
    assert mod._last_weekday_before_day_in_month(2026, 6, 0, 4) is None
