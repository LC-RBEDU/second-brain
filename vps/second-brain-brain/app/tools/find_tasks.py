"""find_tasks — filter active task files. Empty result is an empty list."""
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

from promoted_alias import alias_state  # noqa: E402
from task_query import find_tasks as find_in  # noqa: E402

from app.tools.task_catalog import alias_clock, load_tasks
from app.vault_deps import brain_vault


def find_tasks(
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
    limit: int = 20,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    with brain_vault(mode="read", env=env) as vault:
        today, applied = alias_clock(vault)
        rows = find_in(
            load_tasks(vault),
            query=query,
            task_id=task_id,
            project=project,
            work_type=work_type,
            parent=parent,
            status=status,
            agent=agent,
            deadline_from=deadline_from,
            deadline_to=deadline_to,
            focus=focus,
            limit=limit,
            alias=alias_state(today, applied),
        )
    return {"tasks": rows}
