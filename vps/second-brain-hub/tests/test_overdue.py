"""Unit tests for overdue logging: log once, escalate once, then stay quiet."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from overdue import (  # noqa: E402
    ESCALATE_AFTER_DAYS,
    days_overdue,
    escalation_line,
    first_breach_line,
    needs_escalation,
    needs_first_flag,
)

DEADLINE = date(2026, 7, 18)


def test_first_breach_logs_once():
    body = "## Poznámky / log\n"
    assert needs_first_flag(body, DEADLINE) is True

    body += first_breach_line("2026-07-19", DEADLINE)
    assert needs_first_flag(body, DEADLINE) is False


def test_legacy_lines_count_as_already_flagged():
    """Pre-v2 spam must not trigger a fresh round of logging."""
    body = (
        "- 2026-07-19: OVERDUE — deadline 2026-07-18 prošel. [lifecycle_overdue_flag]\n"
        "- 2026-07-20: OVERDUE — deadline 2026-07-18 prošel. [lifecycle_overdue_flag]\n"
    )
    assert needs_first_flag(body, DEADLINE) is False


def test_new_deadline_logs_again():
    body = first_breach_line("2026-07-19", DEADLINE)
    assert needs_first_flag(body, date(2026, 8, 15)) is True


def test_escalation_only_after_two_weeks():
    body = first_breach_line("2026-07-19", DEADLINE)
    assert needs_escalation(body, DEADLINE, date(2026, 7, 25)) is False
    assert needs_escalation(body, DEADLINE, date(2026, 8, 1)) is True
    assert ESCALATE_AFTER_DAYS == 14


def test_escalation_logs_once_then_silence():
    today = date(2026, 8, 1)
    body = first_breach_line("2026-07-19", DEADLINE)
    body += escalation_line(today.isoformat(), DEADLINE, today)
    assert needs_escalation(body, DEADLINE, today) is False
    assert needs_escalation(body, DEADLINE, date(2026, 9, 1)) is False


def test_escalation_text_asks_for_a_decision():
    today = date(2026, 8, 1)
    line = escalation_line(today.isoformat(), DEADLINE, today)
    assert "14 dní" in line
    assert "Rozhodni" in line
    assert days_overdue(DEADLINE, today) == 14


def test_no_repeat_across_many_days():
    """The whole point: 20 daily runs must produce 2 lines, not 20."""
    lines = 0
    body = "## Poznámky / log\n"
    for offset in range(20):
        day = date.fromordinal(DEADLINE.toordinal() + 1 + offset)
        if needs_first_flag(body, DEADLINE):
            body += first_breach_line(day.isoformat(), DEADLINE)
            lines += 1
        elif needs_escalation(body, DEADLINE, day):
            body += escalation_line(day.isoformat(), DEADLINE, day)
            lines += 1
    assert lines == 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all passed")
