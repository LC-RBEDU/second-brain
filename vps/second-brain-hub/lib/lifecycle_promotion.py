"""Shared helpers for lifecycle cron jobs (ASAP backfill, Waiting defaults)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from today_priority import TOP_PRIORITY_TODAY_LIMIT, today_score

DEFAULT_WAIT_UNTIL_DAYS = 3
TARGET_ASAP_COUNT = TOP_PRIORITY_TODAY_LIMIT


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


def select_next_for_asap_promotion(
    next_tasks: list[Any],
    *,
    today: date,
    current_asap_count: int,
    target_asap: int = TARGET_ASAP_COUNT,
) -> list[Any]:
    """Pick Next tasks to promote so open ASAP count reaches target (max target)."""
    need = max(0, target_asap - current_asap_count)
    if need <= 0 or not next_tasks:
        return []

    def score_key(task: Any) -> float:
        fm = task.frontmatter if hasattr(task, "frontmatter") else task
        return task_today_score(fm, today)

    ranked = sorted(next_tasks, key=score_key, reverse=True)
    return ranked[:need]
