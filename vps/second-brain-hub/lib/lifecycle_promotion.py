"""Shared helpers for lifecycle cron jobs (focus suggestions, Waiting defaults).

Nothing here writes to ``focus``. The suggester ranks candidates and hands them
to agent-context; picking the week's focus stays a human decision.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from focus import FOCUS_LIMIT, is_focus_current
from today_priority import today_score

DEFAULT_WAIT_UNTIL_DAYS = 3
FOCUS_TARGET = FOCUS_LIMIT


def priority_score_from_frontmatter(fm: dict[str, Any]) -> float:
    ice_i = int(fm.get("ice_i") or 5)
    ice_c = int(fm.get("ice_c") or 5)
    ice_e = max(int(fm.get("ice_e") or 5), 1)
    return round((ice_i * ice_c) / ice_e, 2)


def deadline_str(fm: dict[str, Any]) -> str | None:
    dl = fm.get("deadline")
    if dl is None:
        return None
    if hasattr(dl, "isoformat"):
        return dl.isoformat()[:10]
    s = str(dl).strip()
    return s[:10] if s and s.lower() != "null" else None


def task_today_score(fm: dict[str, Any], today: date) -> float:
    return today_score(priority_score_from_frontmatter(fm), deadline_str(fm), today)


def has_wait_until_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def default_wait_until(today: date, *, days: int = DEFAULT_WAIT_UNTIL_DAYS) -> date:
    return today + timedelta(days=days)


def _frontmatter(task: Any) -> dict[str, Any]:
    if hasattr(task, "to_dict"):
        return task.to_dict()
    fm = task.frontmatter if hasattr(task, "frontmatter") else task
    return fm if isinstance(fm, dict) else {}


def count_focused(tasks: list[Any], today: date) -> int:
    return sum(
        1 for t in tasks if is_focus_current(_frontmatter(t).get("focus"), today)
    )


def select_focus_suggestions(
    candidates: list[Any],
    *,
    today: date,
    current_focus_count: int,
    target: int = FOCUS_TARGET,
) -> list[Any]:
    """Rank candidates to fill the remaining focus slots. Never mutates tasks."""
    need = max(0, target - current_focus_count)
    if need <= 0 or not candidates:
        return []

    ranked = sorted(
        candidates,
        key=lambda t: task_today_score(_frontmatter(t), today),
        reverse=True,
    )
    return ranked[:need]
