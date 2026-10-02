"""TOP priority dnes — eligibility + rank_key (SSOT for agent-context.json).

Priority model v2.2 — "what now" is answered by the focus week, not by a status:

- ``top_priority_today`` — tasks whose ``focus`` is the current ISO week (max 5).
  Nothing else qualifies, and no cron may add to it: focus is a human choice.
- ``top_priority`` — the wider queue (focus + Doing + Next), sorted the same way.

Dates (exclusive):
- ``deadline`` — hard external commitment only; when set, ``review_deadline`` is ignored
- ``review_deadline`` — own soft date — only when there is no ``deadline``
- ``due`` — ``deadline`` if present, else ``review_deadline`` (Rozhodni / due_soon)

Ranking (not urgency bonuses):
- Bucket 0: hard ``deadline`` <= today + DEADLINE_HORIZON_DAYS (incl. overdue)
- Bucket 1: everything else (``review_deadline`` does not affect order)
- Within bucket 0: deadline ASC, then rank_score DESC
- Within bucket 1: rank_score DESC only (sentinel date on the date axis)

``rank_score`` = priority_score + company_bonus (+5 if company_priorities has a
non-empty stripped string). Snapshot arrays are pre-sorted; do not re-sort by
``today_score`` (alias of ``rank_score``).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from focus import (
    FOCUS_INELIGIBLE_STATUSES,
    FOCUS_LIMIT,
    STATUS_DOING,
    STATUS_NEXT,
    STATUS_WAITING,
    is_focus_current,
    is_terminal,
)
from hierarchy import is_focusable

DEADLINE_HORIZON_DAYS = 7
COMPANY_PRIORITY_BONUS = 5.0

# Legacy constants kept for importers / docs scrub; unused in ranking.
URGENCY_BONUS_OVERDUE = 5
URGENCY_BONUS_TODAY = 30
URGENCY_BONUS_TOMORROW = 15
URGENCY_BONUS_REVIEW_TODAY = 20
URGENCY_BONUS_REVIEW_TOMORROW = 10

TOP_PRIORITY_TODAY_LIMIT = FOCUS_LIMIT
TOP_PRIORITY_LIMIT = 15

QUEUE_STATUSES = frozenset({STATUS_DOING, STATUS_NEXT})

# Project hub ``status`` (not task status). Empty/missing counts as active.
ACTIVE_PROJECT_STATUSES = frozenset({"active", ""})

_EMPTY_MARKERS = frozenset({"", "—", "-", "~", "null", "none", "n/a"})


def is_active_project_status(status: str | None) -> bool:
    """True when a project hub should feed TOP / Rozhodni / focus suggestions."""
    return str(status or "active").strip().lower() in ACTIVE_PROJECT_STATUSES


def paused_project_slugs(projects: list[Any]) -> set[str]:
    """Slugs whose hub ``status`` is not active (typically ``paused``)."""
    out: set[str] = set()
    for p in projects:
        if isinstance(p, dict):
            slug = p.get("slug")
            status = p.get("status")
        else:
            slug = getattr(p, "slug", None)
            status = getattr(p, "status", None)
        if slug and not is_active_project_status(status):
            out.add(str(slug))
    return out


def exclude_paused_project_tasks(
    tasks: list[Any],
    paused_slugs: set[str],
) -> list[Any]:
    """Drop tasks whose ``slug`` belongs to a paused (non-active) project."""
    if not paused_slugs:
        return list(tasks)
    return [t for t in tasks if _task_get(t, "slug") not in paused_slugs]


def _task_get(task: Any, key: str, default=None):
    if isinstance(task, dict):
        return task.get(key, default)
    fm = getattr(task, "frontmatter", None)
    if isinstance(fm, dict) and key in fm and not hasattr(task, key):
        return fm.get(key, default)
    return getattr(task, key, default)


def parse_deadline(deadline: str | None, today: date | None = None) -> date | None:
    """Parse ISO date string. ``today`` is unused; kept for call-site compatibility."""
    del today  # API compatibility with older callers
    if not deadline:
        return None
    try:
        return date.fromisoformat(str(deadline)[:10])
    except ValueError:
        return None


def effective_due(
    deadline: str | None,
    review_deadline: str | None = None,
) -> date | None:
    """``due`` = deadline if set, else review_deadline (exclusive axes)."""
    dl = parse_deadline(deadline)
    if dl is not None:
        return dl
    return parse_deadline(review_deadline)


def company_priorities_list(task: Any) -> list[str]:
    """Normalize ``company_priorities`` from task / frontmatter to a string list."""
    raw = _task_get(task, "company_priorities")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    return []


def company_bonus(task: Any) -> float:
    """+COMPANY_PRIORITY_BONUS if any non-empty stripped entry (no FS check)."""
    for item in company_priorities_list(task):
        s = str(item).strip().strip("\"'")
        if s.lower() in _EMPTY_MARKERS:
            continue
        if s:
            return float(COMPANY_PRIORITY_BONUS)
    return 0.0


def in_deadline_bucket(deadline: str | None, today: date) -> bool:
    """True when hard deadline is set and deadline <= today + horizon (incl. overdue)."""
    dl = parse_deadline(deadline)
    if dl is None:
        return False
    return dl <= today + timedelta(days=DEADLINE_HORIZON_DAYS)


def rank_score(task: Any) -> float:
    """priority_score + company_bonus (no urgency)."""
    return round(_priority_score(task) + company_bonus(task), 2)


def rank_key(task: Any, today: date) -> tuple[int, date, float]:
    """Sort key: ascending — deadline bucket first, then deadline ASC, then score DESC."""
    dl = parse_deadline(_task_get(task, "deadline"))
    rs = rank_score(task)
    if dl is not None and in_deadline_bucket(_task_get(task, "deadline"), today):
        return (0, dl, -rs)
    return (1, date.max, -rs)


def today_score(
    priority_score: float,
    deadline: str | None,
    today: date,
    review_deadline: str | None = None,
    company_priorities: list[str] | None = None,
) -> float:
    """Alias of rank_score for call sites that still pass ICE parts.

    ``deadline`` / ``review_deadline`` / ``today`` ignored for ranking (kept for API).
    """
    del deadline, today, review_deadline
    bonus = 0.0
    if company_priorities:
        bonus = company_bonus({"company_priorities": company_priorities})
    return round(float(priority_score) + bonus, 2)


def urgency_bonus(
    deadline: str | None,
    today: date,
    review_deadline: str | None = None,
) -> float:
    """Deprecated: ranking no longer uses urgency. Always 0."""
    del deadline, today, review_deadline
    return 0.0


def needs_decision(task: Any, today: date) -> bool:
    """True when due < today and the item is actionable (not Waiting/terminal)."""
    status = str(_task_get(task, "status") or "")
    if is_terminal(status) or status == STATUS_WAITING:
        return False
    due = effective_due(
        _task_get(task, "deadline"),
        _task_get(task, "review_deadline"),
    )
    return due is not None and due < today


def is_focus_eligible(task: Any, today: date) -> bool:
    """True when the task carries the current focus week and is actionable.

    Epics never qualify as queue work — focus on epics is etapa 3 (expand children).
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
    out = dict(task_dict)
    out.setdefault("priority_score", _priority_score(out))
    if "company_priorities" not in out:
        out["company_priorities"] = company_priorities_list(out)
    dl = out.get("deadline")
    rd = out.get("review_deadline")
    due = effective_due(dl, rd)
    out["due"] = due.isoformat() if due else None
    cb = company_bonus(out)
    rs = round(float(out["priority_score"]) + cb, 2)
    out["company_bonus"] = cb
    out["rank_score"] = rs
    out["today_score"] = rs
    out["in_deadline_bucket"] = in_deadline_bucket(dl, today)
    out["urgency_bonus"] = 0.0
    return out


def _to_enriched(task: Any, today: date) -> dict:
    if isinstance(task, dict):
        base = dict(task)
        base.setdefault("priority_score", _priority_score(task))
        if "company_priorities" not in base:
            base["company_priorities"] = company_priorities_list(task)
    else:
        base = task.to_dict() if hasattr(task, "to_dict") else dict(task.frontmatter)
        base.setdefault("priority_score", _priority_score(task))
        if "company_priorities" not in base:
            base["company_priorities"] = company_priorities_list(task)
    return enrich_task_dict(base, today)


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
    Arrays are pre-sorted by ``rank_key`` (ascending).
    """

    def ranked(tasks: list[Any]) -> list[Any]:
        return sorted(tasks, key=lambda t: rank_key(t, today))

    focused = ranked([t for t in open_tasks if is_focus_eligible(t, today)])
    queued = ranked([t for t in open_tasks if is_queue_eligible(t, today)])

    top_today = [_to_enriched(t, today) for t in focused[:today_limit]]
    top_general = [_to_enriched(t, today) for t in queued[:general_limit]]
    return top_today, top_general
