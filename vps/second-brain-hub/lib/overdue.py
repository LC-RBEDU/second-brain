"""Overdue logging rules — one line per deadline, one escalation, then silence.

Kept separate from the cron job so the behaviour is unit-testable without Drive.

Markers embed the deadline value:

    [lifecycle_overdue_flag:2026-07-18]
    [lifecycle_overdue_escalate:2026-07-18]

so that rescheduling a task and missing the new date logs again, while an
unchanged deadline never repeats itself.
"""
from __future__ import annotations

import re
from datetime import date

ESCALATE_AFTER_DAYS = 14

FLAG_MARKER = "lifecycle_overdue_flag"
ESCALATE_MARKER = "lifecycle_overdue_escalate"

# Pre-v2 lines carried no deadline in the marker: "[lifecycle_overdue_flag]".
# They still count as "already flagged" so the cleanup does not start over.
LEGACY_FLAG_RE = re.compile(r"OVERDUE — deadline (\d{4}-\d{2}-\d{2}) prošel\.\s*\[lifecycle_overdue_flag\]")


def flag_marker(deadline: date) -> str:
    return f"[{FLAG_MARKER}:{deadline.isoformat()}]"


def escalate_marker(deadline: date) -> str:
    return f"[{ESCALATE_MARKER}:{deadline.isoformat()}]"


def days_overdue(deadline: date, today: date) -> int:
    return (today - deadline).days


def has_first_flag(body: str, deadline: date) -> bool:
    if flag_marker(deadline) in body:
        return True
    return any(m.group(1) == deadline.isoformat() for m in LEGACY_FLAG_RE.finditer(body))


def has_escalation(body: str, deadline: date) -> bool:
    return escalate_marker(deadline) in body


def needs_first_flag(body: str, deadline: date) -> bool:
    return not has_first_flag(body, deadline)


def needs_escalation(body: str, deadline: date, today: date) -> bool:
    if has_escalation(body, deadline):
        return False
    return days_overdue(deadline, today) >= ESCALATE_AFTER_DAYS


def first_breach_line(today_str: str, deadline: date) -> str:
    return (
        f"- {today_str}: OVERDUE — deadline {deadline.isoformat()} prošel. "
        f"{flag_marker(deadline)}\n"
    )


def escalation_line(today_str: str, deadline: date, today: date) -> str:
    n = days_overdue(deadline, today)
    return (
        f"- {today_str}: OVERDUE **{n} dní** — deadline {deadline.isoformat()} prošel a "
        f"nic se nezměnilo. Rozhodni: nový termín, nebo deadline pryč (nebyl to závazek "
        f"vůči nikomu venku). {escalate_marker(deadline)}\n"
    )
