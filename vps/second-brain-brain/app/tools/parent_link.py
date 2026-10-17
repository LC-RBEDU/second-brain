"""Parent rules for create, update and bulk. One error shape for every 400."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hierarchy import (
    parent_chain_cycle,
    parent_id_of,
    parent_type_error,
    parse_parent_id,
    work_type_of,
)
from task_query import OPEN_STATUSES

from app.errors import BrainClientError


def client_error(reasons: list[str]) -> BrainClientError:
    unique: list[str] = []
    seen: set[tuple[str, str]] = set()
    for reason in reasons:
        if not reason:
            continue
        unique.append(reason)
    if not unique:
        unique = ["parent_type_error"]
    return BrainClientError(
        message=", ".join(unique),
        status_code=400,
        error_reason=unique[0],
        detail={"errors": unique},
    )


def _task_id(task: Any) -> str:
    fm = getattr(task, "frontmatter", None) or {}
    return str(fm.get("id") or "")


def _status(task: Any) -> str:
    fm = getattr(task, "frontmatter", None) or {}
    return str(fm.get("status") or "")


@dataclass
class OverlayNode:
    id: str
    type: str
    parent_id: str | None
    status: str
    rel_path: str


def resolve_parent_raw(
    raw: Any,
    tasks: list[Any],
    *,
    child_id: str,
    child_type: str,
) -> str:
    """Return ``[[id]]`` or ``\"\"``. Raises 400. Type is checked against ``tasks`` as given."""
    text = "" if raw is None else str(raw).strip()
    parsed = parse_parent_id(text) if text else None
    if not text or parsed is None and not text:
        err = parent_type_error(child_type, child_id, None, None)
        if err:
            raise client_error([err])
        return ""
    wanted = parsed if parsed is not None else text
    matches = [task for task in tasks if _task_id(task) == wanted]
    if not matches:
        raise client_error(["parent_not_found"])
    if len(matches) > 1:
        raise client_error(["parent_ambiguous"])
    parent_type = work_type_of(matches[0])
    err = parent_type_error(child_type, child_id, wanted, parent_type)
    if err:
        raise client_error([err])
    parent_of = {_task_id(task): parent_id_of(task) for task in tasks}
    if parent_chain_cycle(child_id, wanted, parent_of):
        raise client_error(["parent_cycle"])
    return f"[[{wanted}]]"


def _nodes(tasks: list[Any]) -> dict[str, OverlayNode]:
    out: dict[str, OverlayNode] = {}
    for task in tasks:
        task_id = _task_id(task)
        if not task_id or task_id in out:
            continue
        out[task_id] = OverlayNode(
            id=task_id,
            type=work_type_of(task),
            parent_id=parent_id_of(task),
            status=_status(task),
            rel_path=str(getattr(task, "rel_path", "") or ""),
        )
    return out


def _lookup_id(raw: Any, tasks: list[Any]) -> tuple[str | None, str | None]:
    """Return (parent_id, error_reason). Empty raw is (None, None)."""
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None, None
    parsed = parse_parent_id(text)
    wanted = parsed if parsed is not None else text
    matches = [task for task in tasks if _task_id(task) == wanted]
    if not matches:
        return None, "parent_not_found"
    if len(matches) > 1:
        return None, "parent_ambiguous"
    return wanted, None


def needs_forest(patch: dict[str, Any]) -> bool:
    """A pure Done/Cancelled status does not load the task list."""
    if any(key in patch for key in ("parent", "type", "deadline")):
        return True
    if "status" in patch and str(patch.get("status") or "") in OPEN_STATUSES:
        return True
    return False


def check_overlay(
    tasks: list[Any],
    updates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Apply parent/type/status in memory, then raise one 400 with every violation.

    ``updates`` items are ``{"id", "patch"}`` in request order. The returned
    patches have ``parent`` normalised to ``[[id]]`` or ``""`` when that key
    was present. Children that are not in the request are not rewritten.
    """
    nodes = _nodes(tasks)
    normalized: dict[str, dict[str, Any]] = {}
    for item in updates:
        task_id = str(item.get("id") or "")
        patch = dict(item.get("patch") or {})
        node = nodes.get(task_id)
        if node is None:
            raise BrainClientError(
                message=f"not_found {task_id}",
                status_code=404,
                error_reason="not_found",
            )
        if "type" in patch:
            node.type = work_type_of({"type": patch.get("type")})
        if "status" in patch:
            node.status = str(patch.get("status") or "")
        if "parent" in patch:
            parent_id, err = _lookup_id(patch.get("parent"), tasks)
            if err:
                patch["_parent_error"] = err
            else:
                node.parent_id = parent_id
                patch["parent"] = f"[[{parent_id}]]" if parent_id else ""
                if not parent_id:
                    err = parent_type_error(node.type, node.id, None, None)
                    if err:
                        patch["_parent_error"] = err
        normalized[task_id] = patch

    by_parent: dict[str, list[OverlayNode]] = {}
    for node in nodes.values():
        if node.parent_id:
            by_parent.setdefault(node.parent_id, []).append(node)

    reasons: list[str] = []
    seen: set[tuple[str, str]] = set()

    def add(owner: str, reason: str | None) -> None:
        if not reason:
            return
        key = (owner, reason)
        if key in seen:
            return
        seen.add(key)
        reasons.append(reason)

    for item in updates:
        task_id = str(item.get("id") or "")
        patch = normalized[task_id]
        node = nodes[task_id]
        original = item.get("patch") or {}
        type_changed = "type" in original
        parent_changed = "parent" in original
        if parent_changed or type_changed:
            if patch.get("_parent_error"):
                add(task_id, str(patch["_parent_error"]))
            else:
                parent = nodes.get(node.parent_id or "")
                parent_type = parent.type if parent is not None else (None if node.parent_id else None)
                if node.parent_id and parent is None:
                    parent_type = None
                add(
                    task_id,
                    parent_type_error(node.type, node.id, node.parent_id, parent_type),
                )
            if type_changed:
                children = sorted(by_parent.get(task_id, []), key=lambda row: row.id)
                for child in children:
                    if child.status not in OPEN_STATUSES:
                        continue
                    child_parent = nodes.get(child.parent_id or "")
                    child_parent_type = child_parent.type if child_parent is not None else None
                    add(
                        child.id,
                        parent_type_error(
                            child.type, child.id, child.parent_id, child_parent_type
                        ),
                    )
        if "status" in original and node.status in OPEN_STATUSES and not patch.get("_parent_error"):
            parent = nodes.get(node.parent_id or "")
            parent_type = parent.type if parent is not None else (None if node.parent_id else None)
            if node.parent_id and parent is None:
                parent_type = None
            add(
                task_id,
                parent_type_error(node.type, node.id, node.parent_id, parent_type),
            )
        patch.pop("_parent_error", None)
    if reasons:
        raise client_error(reasons)
    return normalized
