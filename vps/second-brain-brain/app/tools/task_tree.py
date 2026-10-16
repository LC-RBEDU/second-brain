"""list_children and get_tree for an epic or a story."""
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

from task_query import children_of, tree_for  # noqa: E402

from app.errors import BrainClientError
from app.tools.task_catalog import load_tasks
from app.vault_deps import brain_vault


def list_children(*, task_id: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    ref = (task_id or "").strip()
    with brain_vault(mode="read", env=env) as vault:
        tasks = load_tasks(vault)
    return {"id": ref, "children": children_of(tasks, ref)}


def get_tree(*, task_id: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    ref = (task_id or "").strip()
    with brain_vault(mode="read", env=env) as vault:
        tasks = load_tasks(vault)
    tree = tree_for(tasks, ref)
    if tree is None:
        raise BrainClientError(message="not_found", status_code=404, error_reason="not_found")
    return tree
