"""Find and resolve task files, including the 90-day checkbox alias."""
from __future__ import annotations

from typing import Any

from hierarchy import parse_parent_id
from promoted_alias import alias_state

OPEN_STATUSES = frozenset({"Doing", "Next", "Backlog", "Waiting"})
FIND_DEFAULT_LIMIT = 20
FIND_MAX_LIMIT = 50


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _date10(value: Any) -> str | None:
    text = _text(value)
    if not text or text.lower() in {"none", "null"}:
        return None
    return text[:10]


def _fm(task: Any) -> dict[str, Any]:
    fm = getattr(task, "frontmatter", None)
    if isinstance(fm, dict):
        return fm
    return task if isinstance(task, dict) else {}


def _body(task: Any) -> str:
    body = getattr(task, "body", None)
    if isinstance(body, str):
        return body
    return str(task.get("body") or "") if isinstance(task, dict) else ""


def _path(task: Any) -> str:
    rel = getattr(task, "rel_path", None)
    if rel:
        return str(rel)
    return str(task.get("path") or task.get("rel_path") or "") if isinstance(task, dict) else ""


def card(task: Any) -> dict[str, Any]:
    fm = _fm(task)
    focus = _text(fm.get("focus"))
    promoted = _text(fm.get("promoted_from"))
    return {
        "id": _text(fm.get("id")),
        "title": _text(fm.get("title")),
        "type": _text(fm.get("type")) or "task",
        "status": _text(fm.get("status")),
        "parent": parse_parent_id(fm.get("parent")),
        "project": _text(fm.get("slug")),
        "deadline": _date10(fm.get("deadline")),
        "review_deadline": _date10(fm.get("review_deadline")),
        "focus": focus or None,
        "path": _path(task),
        "promoted_from": promoted or None,
    }


def _matches_query(task: Any, query: str) -> bool:
    needle = query.casefold()
    fm = _fm(task)
    hay = f"{_text(fm.get('title'))}\n{_body(task)}".casefold()
    return needle in hay


def find_tasks(
    tasks: list[Any],
    *,
    query: str | None = None,
    task_id: str | None = None,
    project: str | None = None,
    work_type: str | None = None,
    parent: str | None = None,
    status: list[str] | None = None,
    agent: str | None = None,
    deadline_from: str | None = None,
    deadline_to: str | None = None,
    focus: str | None = None,
    limit: int = FIND_DEFAULT_LIMIT,
    alias: str = "inactive",
) -> list[dict[str, Any]]:
    cap = FIND_DEFAULT_LIMIT if limit is None else max(1, min(int(limit), FIND_MAX_LIMIT))
    wanted_status = {item for item in (status or []) if item}
    out: list[dict[str, Any]] = []
    for task in tasks:
        row = card(task)
        if task_id:
            direct = row["id"] == task_id
            aliased = alias == "active" and row["promoted_from"] == task_id
            if not direct and not aliased:
                continue
        if query and not _matches_query(task, query):
            continue
        if project and row["project"] != project:
            continue
        if work_type and row["type"] != work_type:
            continue
        if parent and row["parent"] != parent:
            continue
        if wanted_status and row["status"] not in wanted_status:
            continue
        if agent is not None and _text(_fm(task).get("agent")) != agent:
            continue
        if deadline_from and (row["deadline"] or "") < deadline_from:
            continue
        if deadline_to and (row["deadline"] or "9999-99-99") > deadline_to:
            continue
        if focus is not None and (row["focus"] or "") != focus:
            continue
        out.append(row)
        if len(out) >= cap:
            break
    return out


def resolve_task(tasks: list[Any], ref: str, *, applied_at, today) -> tuple[Any | None, str | None, str | None]:
    """Return ``(task, resolved_from, error)``.

    ``error`` is ``alias_expired``, ``alias_inactive``, ``alias_ambiguous``, or ``not_found``.
    A real file id resolves even when the alias window is closed.
    """
    for task in tasks:
        if _text(_fm(task).get("id")) == ref:
            return task, None, None
    promoted = [task for task in tasks if _text(_fm(task).get("promoted_from")) == ref]
    state = alias_state(today, applied_at)
    if state == "active":
        if len(promoted) == 1:
            return promoted[0], ref, None
        if len(promoted) > 1:
            return None, None, "alias_ambiguous"
        return None, None, "not_found"
    if promoted and state == "expired":
        return None, None, "alias_expired"
    if promoted and state == "inactive":
        return None, None, "alias_inactive"
    return None, None, "not_found"


def file_project(task: Any) -> str:
    parts = _path(task).split("/")
    if len(parts) >= 2 and parts[0] == "02-PROJEKTY":
        return parts[1]
    return ""


def children_of(tasks: list[Any], parent_id: str) -> list[dict[str, Any]]:
    rows = []
    for task in tasks:
        row = card(task)
        if row["parent"] == parent_id:
            rows.append({
                "id": row["id"],
                "title": row["title"],
                "status": row["status"],
                "deadline": row["deadline"],
                "project": file_project(task),
            })
    return rows


def open_descendant_count(tasks: list[Any], root_id: str) -> int:
    count = 0
    stack = [root_id]
    seen = {root_id}
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        row = card(task)
        if row["parent"]:
            by_parent.setdefault(row["parent"], []).append(row)
    while stack:
        current = stack.pop()
        for child in by_parent.get(current, []):
            if child["id"] in seen:
                continue
            seen.add(child["id"])
            stack.append(child["id"])
            if child["status"] in OPEN_STATUSES:
                count += 1
    return count


def tree_for(tasks: list[Any], root_id: str) -> dict[str, Any] | None:
    root = next((task for task in tasks if card(task)["id"] == root_id), None)
    if root is None:
        return None
    row = card(root)
    kids = children_of(tasks, root_id)
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "deadline": row["deadline"],
        "project": file_project(root),
        "open_descendants": open_descendant_count(tasks, root_id),
        "children": [
            {
                **child,
                "open_descendants": open_descendant_count(tasks, child["id"]),
            }
            for child in kids
        ],
    }
