"""get_task — one file by id, or by an old checkbox id inside the alias window."""
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

import logging

from deadline_order import conflicts_in_tree, node_from_frontmatter  # noqa: E402
from task_query import card, children_of, resolve_task  # noqa: E402

log = logging.getLogger(__name__)

from app.errors import BrainClientError
from app.tools.task_catalog import alias_clock, load_tasks, log_section
from app.vault_deps import brain_vault

_STATUS = {
    "alias_expired": 404,
    "alias_inactive": 404,
    "alias_ambiguous": 409,
    "not_found": 404,
}

_WHY = {
    "not_found": (
        "v aktivních souborech 02-PROJEKTY/*/tasks/ tenhle id není "
        "(archiv Done/Cancelled get_task nečte)"
    ),
    "alias_expired": "staré checkbox id je mimo 90denní alias okno",
    "alias_inactive": "alias okno není aktivní",
    "alias_ambiguous": "staré id sedí na víc než jeden úkol",
}


def get_task(*, task_id: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    ref = (task_id or "").strip()
    if not ref:
        raise BrainClientError(
            message="missing_id: id required",
            status_code=400,
            error_reason="missing_id",
        )
    with brain_vault(mode="read", env=env) as vault:
        today, applied = alias_clock(vault)
        tasks = load_tasks(vault)
        nodes = [node_from_frontmatter(item.frontmatter) for item in tasks]
        conflicts = conflicts_in_tree(nodes)
        if conflicts:
            log.warning("deadline_order read %s", [row.as_dict() for row in conflicts])
        task, resolved_from, error = resolve_task(tasks, ref, applied_at=applied, today=today)
    if error or task is None:
        reason = error or "not_found"
        why = _WHY.get(reason, reason)
        raise BrainClientError(
            message=f"{reason}: {ref}. {why}",
            status_code=_STATUS.get(reason, 404),
            error_reason=reason,
        )
    row = card(task)
    row["frontmatter"] = dict(task.frontmatter)
    row["body"] = task.body
    row["children"] = children_of(tasks, row["id"])
    row["log"] = log_section(task.body)
    if resolved_from:
        row["resolved_from"] = resolved_from
    return row
