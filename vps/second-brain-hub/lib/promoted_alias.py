"""Old checkbox ids resolve only inside the migration window.

The clock starts at ``applied_at`` in ``00-System/task-promotion-applied.json``
(Europe/Prague calendar date). Day 90 inclusive still resolves. Day 91 does not.
A missing file means the migration has not been applied, so the alias is inactive.
``promoted_from`` stays on the task either way.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

ANCHOR_REL = "00-System/task-promotion-applied.json"
WINDOW_DAYS = 90
PRAGUE = ZoneInfo("Europe/Prague")


def prague_today(now: datetime | None = None) -> date:
    current = now or datetime.now(PRAGUE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=PRAGUE)
    return current.astimezone(PRAGUE).date()


def parse_applied_at(payload: Any) -> date | None:
    if not isinstance(payload, dict):
        return None
    raw = payload.get("applied_at")
    if raw is None:
        return None
    text = str(raw).strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_applied_at(vault: Any) -> date | None:
    try:
        text, _meta = vault.read_text(ANCHOR_REL)
    except Exception:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parse_applied_at(payload)


def alias_state(today: date, applied_at: date | None) -> str:
    """``active``, ``expired``, or ``inactive`` (no anchor)."""
    if applied_at is None:
        return "inactive"
    if today <= applied_at + timedelta(days=WINDOW_DAYS):
        return "active"
    return "expired"


def alias_is_active(today: date, applied_at: date | None) -> bool:
    return alias_state(today, applied_at) == "active"
