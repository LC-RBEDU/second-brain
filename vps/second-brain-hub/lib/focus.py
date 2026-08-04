"""Focus week + status vocabulary — SSOT for priority model v2.

Priority is split across three independent axes instead of a single `status` column:

- ``status``   — do I do it at all?  Next / Backlog / Waiting / Doing / Done / Cancelled
- ``deadline`` — when must it be done?  Only a real external commitment.
- ``focus``    — what am I working on now?  ISO week string, e.g. ``2026-W32``.

``focus`` is chosen by the human and is the one field cron jobs must never write.
A task drops out of focus by itself when the week rolls over, so a stalled pick
does not need cleaning up.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

FOCUS_LIMIT = 5

STATUS_DOING = "Doing"
STATUS_NEXT = "Next"
STATUS_BACKLOG = "Backlog"
STATUS_WAITING = "Waiting"
STATUS_DONE = "Done"
STATUS_CANCELLED = "Cancelled"

VALID_STATUSES = frozenset(
    {STATUS_DOING, STATUS_NEXT, STATUS_BACKLOG, STATUS_WAITING, STATUS_DONE, STATUS_CANCELLED}
)

# Closed for good — excluded from open-task counts, hub state and context.
TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED})

# Never surfaced as "what now", even when the task carries a current focus week.
FOCUS_INELIGIBLE_STATUSES = frozenset(
    {STATUS_DONE, STATUS_CANCELLED, STATUS_WAITING, STATUS_BACKLOG}
)

AGENT_NONE = "none"
AGENT_ASSIST = "assist"
AGENT_SOLO = "solo"
AGENT_VALUES = frozenset({AGENT_NONE, AGENT_ASSIST, AGENT_SOLO})

ISO_WEEK_RE = re.compile(r"^(\d{4})-W(\d{1,2})$")


def iso_week(day: date) -> str:
    """Return the ISO week label for a date, e.g. ``2026-W32``."""
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def current_focus_week(today: date) -> str:
    return iso_week(today)


def parse_focus(value: Any) -> str | None:
    """Normalise a focus value to ``YYYY-Www`` or return None when unusable."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"null", "none", ""}:
        return None
    m = ISO_WEEK_RE.match(s)
    if not m:
        return None
    year, week = m.group(1), int(m.group(2))
    if not 1 <= week <= 53:
        return None
    return f"{year}-W{week:02d}"


def is_focus_current(value: Any, today: date) -> bool:
    focus = parse_focus(value)
    return focus is not None and focus == current_focus_week(today)


def is_terminal(status: Any) -> bool:
    return str(status or "") in TERMINAL_STATUSES


def normalise_agent(value: Any) -> str:
    s = str(value or "").strip().lower()
    return s if s in AGENT_VALUES else AGENT_NONE
