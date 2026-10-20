"""TOP priority dnes — eligibility + rank_key (SSOT for agent-context.json).

Priority model v2.2 — "what now" is answered by the focus week, not by a status:

- ``top_priority_today`` — tasks/stories whose ``focus`` is the current ISO week
  (max ``FOCUS_TASK_LIMIT`` = 10). Epics are capped separately (``FOCUS_EPIC_LIMIT`` = 5)
  and never appear here. No cron may add focus: it is a human choice.
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
    FOCUS_TASK_LIMIT,
    STATUS_DOING,
    STATUS_NEXT,
    STATUS_WAITING,
    is_focus_current,
    is_terminal,
)
from hierarchy import (
    TYPE_TASK,
    is_epic,
    is_focusable,
    is_story,
    parse_parent_id,
    work_type_of,
)

DEADLINE_HORIZON_DAYS = 7
COMPANY_PRIORITY_BONUS = 5.0

# Legacy constants kept for importers / docs scrub; unused in ranking.
URGENCY_BONUS_OVERDUE = 5
URGENCY_BONUS_TODAY = 30
URGENCY_BONUS_TOMORROW = 15
URGENCY_BONUS_REVIEW_TODAY = 20
URGENCY_BONUS_REVIEW_TOMORROW = 10

TOP_PRIORITY_TODAY_LIMIT = FOCUS_TASK_LIMIT
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
    """True when a past review date is the only due and the item is actionable.

    A hard deadline is Overdue, not this lane. Waiting and terminal statuses
    stay out even when review_deadline is in the past.
    """
    status = str(_task_get(task, "status") or "")
    if is_terminal(status) or status == STATUS_WAITING:
        return False
    if parse_deadline(_task_get(task, "deadline")) is not None:
        return False
    review = parse_deadline(_task_get(task, "review_deadline"))
    return review is not None and review < today


def is_focus_eligible(task: Any, today: date) -> bool:
    """True when the task carries the current focus week and is actionable.

    Epics never qualify as queue work — focus on epics is etapa 3 (expand children).
    """
    if not is_focusable(task):
        return False
    if _task_get(task, "status") in FOCUS_INELIGIBLE_STATUSES:
        return False
    return is_focus_current(_task_get(task, "focus"), today)


def _rel_path(task: Any) -> str | None:
    rel = _task_get(task, "rel_path") or (
        getattr(task, "rel_path", None) if not isinstance(task, dict) else task.get("rel_path")
    )
    return str(rel) if rel is not None else None


def _task_id(task: Any) -> str | None:
    tid = _task_get(task, "id") or _task_get(task, "task_id")
    return str(tid) if tid is not None else None


def _excluded(
    task: Any,
    *,
    exclude_path: str | None,
    exclude_id: str | None,
) -> bool:
    if exclude_path is not None and _rel_path(task) == str(exclude_path):
        return True
    if exclude_id is not None and _task_id(task) == str(exclude_id):
        return True
    return False


def would_consume_focus_slot(task: Any, paused_slugs: set[str] | None = None) -> bool:
    """True if setting *current* focus on this story/task would take a task slot.

    Ignores the current ``focus`` field — used by ``set_focus`` before write.
    Epics never consume task slots (see ``would_consume_epic_focus_slot``).
    """
    slug = str(_task_get(task, "slug") or "")
    if paused_slugs and slug in paused_slugs:
        return False
    if not is_focusable(task):
        return False
    if _task_get(task, "status") in FOCUS_INELIGIBLE_STATUSES:
        return False
    return True


def would_consume_epic_focus_slot(
    task: Any, paused_slugs: set[str] | None = None
) -> bool:
    """True if setting *current* focus on this epic would take an epic slot."""
    slug = str(_task_get(task, "slug") or "")
    if paused_slugs and slug in paused_slugs:
        return False
    if not is_epic(task):
        return False
    if _task_get(task, "status") in FOCUS_INELIGIBLE_STATUSES:
        return False
    return True


def is_epic_focus_eligible(task: Any, today: date) -> bool:
    """Epic with current focus week and actionable status (not in TOP queue)."""
    if not is_epic(task):
        return False
    if _task_get(task, "status") in FOCUS_INELIGIBLE_STATUSES:
        return False
    return is_focus_current(_task_get(task, "focus"), today)


def count_focus_slots(
    tasks: list[Any],
    today: date,
    *,
    paused_slugs: set[str] | None = None,
    exclude_path: str | None = None,
    exclude_id: str | None = None,
) -> int:
    """Count task/story focus slots: ``is_focus_eligible`` ∩ ¬paused (± exclude).

    SSOT for Brain ``set_focus`` task limit and ``stats.focus_count``.
    """
    filtered = exclude_paused_project_tasks(tasks, paused_slugs or set())
    hidden = parents_with_open_task_children(filtered)
    n = 0
    for t in filtered:
        if _excluded(t, exclude_path=exclude_path, exclude_id=exclude_id):
            continue
        if _story_hidden_by_open_child(t, hidden):
            continue
        if is_focus_eligible(t, today):
            n += 1
    return n


def count_focus_epic_slots(
    tasks: list[Any],
    today: date,
    *,
    paused_slugs: set[str] | None = None,
    exclude_path: str | None = None,
    exclude_id: str | None = None,
) -> int:
    """Count epic focus slots for the current week (± exclude)."""
    filtered = exclude_paused_project_tasks(tasks, paused_slugs or set())
    n = 0
    for t in filtered:
        if _excluded(t, exclude_path=exclude_path, exclude_id=exclude_id):
            continue
        if is_epic_focus_eligible(t, today):
            n += 1
    return n


_OPEN_CHILD_STATUSES = frozenset({"Doing", "Next", "Backlog", "Waiting"})


def parents_with_open_task_children(tasks: list[Any]) -> set[str]:
    """Story ids that still have an open ``type: task`` child."""
    parents: set[str] = set()
    for task in tasks:
        if work_type_of(task) != TYPE_TASK:
            continue
        if str(_task_get(task, "status") or "") not in _OPEN_CHILD_STATUSES:
            continue
        parent = parse_parent_id(_task_get(task, "parent"))
        if parent:
            parents.add(parent)
    return parents


def _story_hidden_by_open_child(task: Any, open_child_parents: set[str] | None) -> bool:
    if not open_child_parents or not is_story(task):
        return False
    task_id = _task_id(task)
    return bool(task_id and task_id in open_child_parents)


def is_queue_eligible(
    task: Any,
    today: date,
    *,
    open_child_parents: set[str] | None = None,
) -> bool:
    """True for the wider list: focused work plus everything queued as Doing/Next.

    Epics stay out of ``top_priority``. A story with an open child task stays out too.
    """
    if not is_focusable(task):
        return False
    if _story_hidden_by_open_child(task, open_child_parents):
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

    hidden = parents_with_open_task_children(open_tasks)
    focused = ranked(
        [
            t
            for t in open_tasks
            if is_focus_eligible(t, today) and not _story_hidden_by_open_child(t, hidden)
        ]
    )
    queued = ranked(
        [t for t in open_tasks if is_queue_eligible(t, today, open_child_parents=hidden)]
    )

    top_today = [_to_enriched(t, today) for t in focused[:today_limit]]
    top_general = [_to_enriched(t, today) for t in queued[:general_limit]]
    return top_today, top_general
