"""bulk_update — one session. A deadline error writes nothing. Focus is refused."""
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

from context_tombstone import delete_context_tombstone  # noqa: E402
from deadline_order import evaluate_deadline_order, node_from_frontmatter  # noqa: E402
from task_query import card  # noqa: E402

from app.errors import BrainClientError
from app.policy import FOCUS_PROPOSAL_MESSAGE
from app.tools.task_catalog import load_tasks
from app.tools.update_task import render_frontmatter_patch
from app.vault_deps import brain_vault


def bulk_update(
    *,
    updates: list[dict[str, Any]],
    allow_parent_shift: bool = False,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not updates:
        raise BrainClientError(message="empty updates", status_code=400, error_reason="empty_updates")
    for item in updates:
        if "focus" in (item.get("patch") or {}):
            raise BrainClientError(
                message=FOCUS_PROPOSAL_MESSAGE,
                status_code=403,
                error_reason="focus_requires_proposal",
            )
    mode = "read" if dry_run else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        tasks = load_tasks(vault)
        by_id = {card(task)["id"]: task for task in tasks}
        resolved: list[tuple[Any, dict[str, Any]]] = []
        deadline_patches: dict[str, str | None] = {}
        for item in updates:
            task_id = str(item.get("id") or "")
            task = by_id.get(task_id)
            if task is None:
                raise BrainClientError(message=f"not_found {task_id}", status_code=404, error_reason="not_found")
            patch = dict(item.get("patch") or {})
            resolved.append((task, patch))
            if "deadline" in patch:
                raw = patch.get("deadline")
                deadline_patches[task_id] = None if raw in (None, "") else str(raw)
        if deadline_patches:
            nodes = [node_from_frontmatter(task.frontmatter) for task in tasks]
            order = evaluate_deadline_order(nodes, deadline_patches, allow_parent_shift=allow_parent_shift)
            if not order.get("ok", False):
                raise BrainClientError(
                    message="deadline_order",
                    status_code=409,
                    error_reason="deadline_order",
                    detail=order,
                )
        written: list[dict[str, str]] = []
        if dry_run:
            return {"dry_run": True, "written": [], "count": len(resolved)}
        delete_context_tombstone(vault)
        for task, patch in resolved:
            text, _meta = vault.read_text(task.rel_path)
            vault.write_text(task.rel_path, render_frontmatter_patch(text, patch))
            written.append({"id": card(task)["id"], "path": task.rel_path})
        return {"dry_run": False, "written": written, "count": len(written)}
