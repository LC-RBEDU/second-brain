"""Open descendants under a task this batch closes. Uses the vault already held."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from hierarchy import parse_parent_id  # noqa: E402
from task_export import export_tasks  # noqa: E402

from app.errors import BrainClientError

_OPEN = frozenset({"Doing", "Next", "Backlog", "Waiting"})
_TERMINAL = frozenset({"Done", "Cancelled"})


def assert_no_open_child(vault: Any, closing: list[tuple[str, str]]) -> None:
    """400 when a Done/Cancelled result still has an open descendant in the export.

    ``closing`` is ``(id, resulting status)`` for this batch. A terminal row in the
    export is a hop, not a failures parent, unless this batch is the one closing it.
    The library export reads ``vault``; it does not open a second session.
    """
    roots = [task_id for task_id, status in closing if status in _TERMINAL and task_id]
    if not roots:
        return
    covered = set(roots)
    snapshot = export_tasks(vault, include_closed_days=7)
    children: dict[str | None, list[str]] = {}
    status_of: dict[str, str] = {}
    for row in snapshot.get("tasks") or []:
        task_id = str(row.get("id") or "")
        if not task_id:
            continue
        status_of[task_id] = str(row.get("status") or "")
        parent = parse_parent_id(row.get("parent"))
        children.setdefault(parent, []).append(task_id)

    failures: list[dict[str, Any]] = []
    for root in roots:
        found: list[str] = []
        stack = list(children.get(root, []))
        seen: set[str] = set()
        while stack:
            child_id = stack.pop()
            if child_id in seen:
                continue
            seen.add(child_id)
            if child_id in covered or status_of.get(child_id) in _TERMINAL:
                stack.extend(children.get(child_id, []))
                continue
            if status_of.get(child_id) in _OPEN:
                found.append(child_id)
                stack.extend(children.get(child_id, []))
        if not found:
            continue
        failures.append({"parent_id": root, "child_ids": sorted(set(found))})

    if not failures:
        return
    failures.sort(key=lambda item: item["parent_id"])
    if len(failures) == 1:
        detail = {
            "parent_id": failures[0]["parent_id"],
            "child_ids": failures[0]["child_ids"],
        }
    else:
        detail = {"failures": failures}
    raise BrainClientError(
        message="open_child_under_closed_parent",
        status_code=400,
        error_reason="open_child_under_closed_parent",
        detail=detail,
    )
