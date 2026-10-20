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
from deadline_order import DeadlineNode, evaluate_deadline_order, node_from_frontmatter  # noqa: E402
from drive_io import DriveConflictError  # noqa: E402
from hierarchy import parse_parent_id  # noqa: E402
from task_query import card  # noqa: E402

from app.errors import BrainClientError
from app.policy import FOCUS_PROPOSAL_MESSAGE
from app.tools.open_child import assert_no_open_child
from app.tools.task_catalog import load_tasks
from app.tools.parent_link import check_overlay, needs_forest
from app.tools.update_task import render_frontmatter_patch
from app.vault_deps import brain_vault

_BATCH_CAP = 80
_TERMINAL = frozenset({"Done", "Cancelled"})


def _prepare_patch(task: Any, patch: dict[str, Any]) -> dict[str, Any]:
    prepared = {key: value for key, value in patch.items() if key != "updated"}
    deadline = prepared.get("deadline")
    if "deadline" in prepared and deadline not in (None, ""):
        prepared["review_deadline"] = ""
    status = str(prepared.get("status") or task.frontmatter.get("status") or "")
    if status == "Waiting":
        wait = prepared.get("waitUntil", task.frontmatter.get("waitUntil"))
        if wait in (None, ""):
            raise BrainClientError(
                message="waiting_no_waituntil",
                status_code=400,
                error_reason="waiting_no_waituntil",
            )
    return prepared


def _reject_oid(vault: Any, resolved: list[tuple[Any, dict[str, Any]]], updates: list[dict[str, Any]]) -> None:
    supplied = [item for item in updates if item.get("expect_oid") is not None]
    if not supplied:
        return
    if len(supplied) != len(updates):
        raise BrainClientError(
            message="missing_expect_oid",
            status_code=400,
            error_reason="missing_expect_oid",
        )
    by_id = {str(item.get("id") or ""): item for item in updates}
    failures: list[dict[str, str]] = []
    for task, _patch in resolved:
        task_id = card(task)["id"]
        expect = by_id.get(task_id, {}).get("expect_oid")
        _text, meta = vault.read_text(task.rel_path)
        oid = getattr(meta, "oid", None)
        if expect is not None and oid is not None and str(oid) != str(expect):
            failures.append({"id": task_id, "path": task.rel_path, "oid": str(oid)})
    if not failures:
        return
    failures.sort(key=lambda item: item["id"])
    raise BrainClientError(
        message="oid_mismatch",
        status_code=409,
        error_reason="oid_mismatch",
        detail={"failures": failures},
    )


def bulk_update(
    *,
    updates: list[dict[str, Any]],
    allow_parent_shift: bool = False,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not updates:
        raise BrainClientError(message="empty updates", status_code=400, error_reason="empty_updates")
    if len(updates) > _BATCH_CAP:
        raise BrainClientError(message="batch_too_large", status_code=400, error_reason="batch_too_large")
    seen_ids: set[str] = set()
    for item in updates:
        task_id = str(item.get("id") or "")
        if task_id in seen_ids:
            raise BrainClientError(message="duplicate_id", status_code=400, error_reason="duplicate_id")
        seen_ids.add(task_id)
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
        forest_items: list[dict[str, Any]] = []
        deadline_patches: dict[str, str | None] = {}
        parent_ids_before: dict[str, str | None] = {}
        touched: set[str] = set()
        for item in updates:
            task_id = str(item.get("id") or "")
            task = by_id.get(task_id)
            if task is None:
                raise BrainClientError(message=f"not_found {task_id}", status_code=404, error_reason="not_found")
            patch = _prepare_patch(task, dict(item.get("patch") or {}))
            resolved.append((task, patch))
            if needs_forest(patch):
                forest_items.append({"id": task_id, "patch": patch})
            if "parent" in patch:
                parent_ids_before[task_id] = parse_parent_id(task.frontmatter.get("parent"))
            if "deadline" in patch:
                touched.add(task_id)
                raw = patch.get("deadline")
                deadline_patches[task_id] = None if raw in (None, "") else str(raw)
        normalized: dict[str, dict[str, Any]] = {}
        if forest_items:
            # A pure Done in the same request still changes the overlay, so a
            # child closed here does not block turning its story into an epic.
            normalized = check_overlay(
                tasks,
                [{"id": card(task)["id"], "patch": patch} for task, patch in resolved],
            )
            resolved = [
                (task, normalized.get(card(task)["id"], patch))
                for task, patch in resolved
            ]
            for task, patch in resolved:
                task_id = card(task)["id"]
                if task_id in parent_ids_before and parse_parent_id(patch.get("parent")) != parent_ids_before[task_id]:
                    touched.add(task_id)
        if touched:
            nodes = [node_from_frontmatter(task.frontmatter) for task in tasks]
            if normalized:
                nodes = [
                    DeadlineNode(
                        node.id,
                        parse_parent_id(normalized[node.id].get("parent"))
                        if node.id in normalized and "parent" in normalized[node.id]
                        else node.parent_id,
                        node.status,
                        node.deadline,
                    )
                    for node in nodes
                ]
            order = evaluate_deadline_order(
                nodes,
                deadline_patches,
                allow_parent_shift=allow_parent_shift,
                touched_ids=touched,
            )
            if not order.get("ok", False):
                raise BrainClientError(
                    message="deadline_order",
                    status_code=409,
                    error_reason="deadline_order",
                    detail=order,
                )
        closing = [
            (card(task)["id"], str(patch.get("status") or task.frontmatter.get("status") or ""))
            for task, patch in resolved
            if str(patch.get("status") or "") in _TERMINAL
        ]
        assert_no_open_child(vault, closing)
        _reject_oid(vault, resolved, updates)
        written: list[dict[str, str]] = []
        if dry_run:
            return {"dry_run": True, "written": [], "count": len(resolved)}
        delete_context_tombstone(vault)
        expect_by_id = {
            str(item.get("id") or ""): item.get("expect_oid")
            for item in updates
            if item.get("expect_oid") is not None
        }
        try:
            for task, patch in resolved:
                task_id = card(task)["id"]
                text, _meta = vault.read_text(task.rel_path)
                kwargs: dict[str, Any] = {}
                if task_id in expect_by_id:
                    kwargs["expect_oid"] = expect_by_id[task_id]
                vault.write_text(task.rel_path, render_frontmatter_patch(text, patch), **kwargs)
                written.append({"id": task_id, "path": task.rel_path})
        except DriveConflictError as exc:
            conflict_oid = getattr(exc, "oid", None)
            raise BrainClientError(
                message=str(exc),
                status_code=409,
                error_reason="oid_mismatch",
                detail={
                    "failures": [
                        {
                            "id": card(task)["id"],
                            "path": task.rel_path,
                            "oid": str(conflict_oid or ""),
                        }
                    ]
                },
            ) from exc
        return {"dry_run": False, "written": written, "count": len(written)}
