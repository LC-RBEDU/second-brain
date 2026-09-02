"""TOP priority dnes — eligibility + today_score (SSOT for agent-context.json).

Priority model v2 — "what now" is answered by the focus week, not by a status:

- ``top_priority_today`` — tasks whose ``focus`` is the current ISO week (max 5).
  Nothing else qualifies, and no cron may add to it: focus is a human choice.
- ``top_priority`` — the wider queue (focus + Doing + Next), sorted the same way.

Urgency bonuses (on top of priority_score = (I*C)/E):
- deadline today: +30
- deadline tomorrow: +15
- overdue (deadline < today): +5

The overdue bonus used to be +35, which made a task climb the list the longer it
rotted. It now only breaks ties, so an expired deadline is visible without
outranking work that is actually due.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from focus import (
    FOCUS_INELIGIBLE_STATUSES,
    FOCUS_LIMIT,
    STATUS_DOING,
    STATUS_NEXT,
    is_focus_current,
)
from hierarchy import is_focusable

URGENCY_BONUS_OVERDUE = 5
URGENCY_BONUS_TODAY = 30
URGENCY_BONUS_TOMORROW = 15

TOP_PRIORITY_TODAY_LIMIT = FOCUS_LIMIT
TOP_PRIORITY_LIMIT = 15

QUEUE_STATUSES = frozenset({STATUS_DOING, STATUS_NEXT})


def _task_get(task: Any, key: str, default=None):
    if isinstance(task, dict):
        return task.get(key, default)
    fm = getattr(task, "frontmatter", None)
    if isinstance(fm, dict) and key in fm and not hasattr(task, key):
        return fm.get(key, default)
    return getattr(task, key, default)


def parse_deadline(deadline: str | None, today: date) -> date | None:
    if not deadline:
        return None
    try:
        return date.fromisoformat(str(deadline)[:10])
    except ValueError:
        return None


def urgency_bonus(deadline: str | None, today: date) -> float:
    dl = parse_deadline(deadline, today)
    if dl is None:
        return 0.0
    if dl < today:
        return float(URGENCY_BONUS_OVERDUE)
    if dl == today:
        return float(URGENCY_BONUS_TODAY)
    if dl == today + timedelta(days=1):
        return float(URGENCY_BONUS_TOMORROW)
    return 0.0


def today_score(priority_score: float, deadline: str | None, today: date) -> float:
    return round(float(priority_score) + urgency_bonus(deadline, today), 2)


def is_focus_eligible(task: Any, today: date) -> bool:
    """True when the task carries the current focus week and is actionable.

    Epics never qualify — focus belongs on stories (or flat tasks).
    """
    if not is_focusable(task):
        return False
    if _task_get(task, "status") in FOCUS_INELIGIBLE_STATUSES:
        return False
    return is_focus_current(_task_get(task, "focus"), today)


def is_queue_eligible(task: Any, today: date) -> bool:
    """True for the wider list: focused work plus everything queued as Doing/Next.

    Epics stay out of ``top_priority`` — they are roadmap containers, not queue items.
    """
    if not is_focusable(task):
        return False
    if is_focus_eligible(task, today):
        return True
    return _task_get(task, "status") in QUEUE_STATUSES


def _priority_score(task: Any) -> float:
    ps = _task_get(task, "priority_score")
    if ps is not None:
        return float(ps)
    ice_i = _task_get(task, "ice_i", 5) or 5
    ice_c = _task_get(task, "ice_c", 5) or 5
    ice_e = max(_task_get(task, "ice_e", 5) or 1, 1)
    return round((ice_i * ice_c) / ice_e, 2)


def enrich_task_dict(task_dict: dict, today: date) -> dict:
    ps = float(task_dict.get("priority_score") or 0)
    dl = task_dict.get("deadline")
    out = dict(task_dict)
    out["urgency_bonus"] = urgency_bonus(dl, today)
    out["today_score"] = today_score(ps, dl, today)
    return out


def _to_enriched(task: Any, ts: float, today: date) -> dict:
    if isinstance(task, dict):
        base = dict(task)
        base.setdefault("priority_score", _priority_score(task))
    else:
        base = task.to_dict() if hasattr(task, "to_dict") else dict(task.frontmatter)
    base["today_score"] = ts
    base["urgency_bonus"] = urgency_bonus(base.get("deadline"), today)
    return base


def select_top_priority(
    open_tasks: list[Any],
    today: date,
    *,
    today_limit: int = TOP_PRIORITY_TODAY_LIMIT,
    general_limit: int = TOP_PRIORITY_LIMIT,
) -> tuple[list[dict], list[dict]]:
    """Return (top_priority_today, top_priority) as enriched dicts.

    ``top_priority_today`` holds only tasks focused on the current ISO week.
    When nothing is focused it stays empty on purpose — the suggester
    (``lifecycle_focus_suggest``) offers candidates instead of promoting them.
    """

    def scored(tasks: list[Any]) -> list[tuple[Any, float]]:
        pairs = [
            (t, today_score(_priority_score(t), _task_get(t, "deadline"), today))
            for t in tasks
        ]
        pairs.sort(key=lambda pair: -pair[1])
        return pairs

    focused = scored([t for t in open_tasks if is_focus_eligible(t, today)])
    queued = scored([t for t in open_tasks if is_queue_eligible(t, today)])

    top_today = [_to_enriched(t, ts, today) for t, ts in focused[:today_limit]]
    top_general = [_to_enriched(t, ts, today) for t, ts in queued[:general_limit]]
    return top_today, top_general
