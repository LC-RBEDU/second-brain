"""Parent deadline must not be earlier than an open descendant's deadline.

Same calendar day is allowed. A node with no deadline is outside the rule
and does not hide a dated descendant from a higher ancestor. Clearing a
deadline is allowed. ``review_deadline`` is not an input.

The check looks at the tree after the proposed patches. ``allow_parent_shift``
does not skip the inequality: a parent may move later only when the flag is
set, and the resulting dates still have to hold.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from hierarchy import parse_parent_id

OPEN_STATUSES = frozenset({"Doing", "Next", "Backlog", "Waiting"})


@dataclass(frozen=True)
class DeadlineNode:
    id: str
    parent_id: str | None
    status: str
    deadline: str | None = None


@dataclass(frozen=True)
class DeadlineConflict:
    parent_id: str
    parent_deadline: str
    child_id: str
    child_deadline: str

    def as_dict(self) -> dict[str, str]:
        return {
            "parent_id": self.parent_id,
            "parent_deadline": self.parent_deadline,
            "child_id": self.child_id,
            "child_deadline": self.child_deadline,
        }


def node_from_frontmatter(fm: dict[str, Any]) -> DeadlineNode:
    raw_deadline = fm.get("deadline")
    text = "" if raw_deadline is None else str(raw_deadline).strip()
    return DeadlineNode(
        id=str(fm.get("id") or ""),
        parent_id=parse_parent_id(fm.get("parent")),
        status=str(fm.get("status") or ""),
        deadline=text[:10] if text and text.lower() not in {"none", "null"} else None,
    )


def parse_deadline(value: Any) -> date | None:
    """First 10 ISO characters, or None when the value is empty."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null"}:
        return None
    head = text[:10]
    try:
        return datetime.strptime(head, "%Y-%m-%d").date()
    except ValueError:
        return None


def _iso(value: date) -> str:
    return value.isoformat()


def _index(nodes: list[DeadlineNode]) -> dict[str, DeadlineNode]:
    return {node.id: node for node in nodes}


def _children_by_parent(nodes: list[DeadlineNode]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for node in nodes:
        if node.parent_id:
            out.setdefault(node.parent_id, []).append(node.id)
    return out


def _apply(nodes: list[DeadlineNode], patches: dict[str, str | None]) -> list[DeadlineNode]:
    applied: list[DeadlineNode] = []
    for node in nodes:
        if node.id not in patches:
            applied.append(node)
            continue
        raw = patches[node.id]
        applied.append(
            DeadlineNode(
                id=node.id,
                parent_id=node.parent_id,
                status=node.status,
                deadline=None if raw is None or str(raw).strip() == "" else str(raw).strip()[:10],
            )
        )
    return applied


def _open_dated_descendants(
    node_id: str,
    by_id: dict[str, DeadlineNode],
    children: dict[str, list[str]],
) -> list[DeadlineNode]:
    found: list[DeadlineNode] = []
    stack = list(children.get(node_id, []))
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        node = by_id[current]
        stack.extend(children.get(current, []))
        if node.status not in OPEN_STATUSES:
            continue
        if parse_deadline(node.deadline) is None:
            continue
        found.append(node)
    return found


def conflicts_in_tree(nodes: list[DeadlineNode]) -> list[DeadlineConflict]:
    """Every open dated descendant that sits after an ancestor's deadline."""
    by_id = _index(nodes)
    children = _children_by_parent(nodes)
    found: list[DeadlineConflict] = []
    for node in nodes:
        parent_day = parse_deadline(node.deadline)
        if parent_day is None:
            continue
        for child in _open_dated_descendants(node.id, by_id, children):
            child_day = parse_deadline(child.deadline)
            if child_day is None or child_day <= parent_day:
                continue
            found.append(
                DeadlineConflict(
                    parent_id=node.id,
                    parent_deadline=_iso(parent_day),
                    child_id=child.id,
                    child_deadline=_iso(child_day),
                )
            )
    return found


def _later_parent_ids(
    before: list[DeadlineNode],
    after: list[DeadlineNode],
) -> list[str]:
    previous = _index(before)
    later: list[str] = []
    for node in after:
        old = parse_deadline(previous[node.id].deadline)
        new = parse_deadline(node.deadline)
        if old is not None and new is not None and new > old:
            later.append(node.id)
        elif old is None and new is not None:
            # Setting a deadline that was empty is not a shift of an existing one.
            continue
    return later


def _options(conflicts: list[DeadlineConflict]) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    seen_child: set[tuple[str, str]] = set()
    parents: dict[str, date] = {}
    for row in conflicts:
        key = (row.child_id, row.parent_deadline)
        if key not in seen_child:
            seen_child.add(key)
            options.append(
                {
                    "action": "move_child_earlier",
                    "child_id": row.child_id,
                    "date": row.parent_deadline,
                }
            )
        child_day = parse_deadline(row.child_deadline)
        if child_day is None:
            continue
        current = parents.get(row.parent_id)
        if current is None or child_day > current:
            parents[row.parent_id] = child_day
    for parent_id, day in parents.items():
        options.append(
            {
                "action": "move_parent_later",
                "parent_id": parent_id,
                "date": _iso(day),
                "requires": "allow_parent_shift",
            }
        )
    return options


def evaluate_deadline_order(
    nodes: list[DeadlineNode],
    patches: dict[str, str | None] | None = None,
    *,
    allow_parent_shift: bool = False,
) -> dict[str, Any]:
    """Return ``{"ok": True}`` or a ``deadline_order`` payload. Nothing is written."""
    patches = patches or {}
    proposed = _apply(nodes, patches)
    tree_conflicts = conflicts_in_tree(proposed)
    shift_ids = [item for item in _later_parent_ids(nodes, proposed) if item in patches]
    if shift_ids and not allow_parent_shift and not tree_conflicts:
        # Moving a parent later needs explicit consent even when the new day
        # already satisfies the inequality. A leaf with no dated descendant is
        # not that case.
        by_id = _index(proposed)
        before = _index(nodes)
        children = _children_by_parent(proposed)
        for parent_id in shift_ids:
            dated = _open_dated_descendants(parent_id, by_id, children)
            if not dated:
                continue
            latest = max(dated, key=lambda item: parse_deadline(item.deadline) or date.min)
            latest_day = parse_deadline(latest.deadline)
            old_day = parse_deadline(before[parent_id].deadline)
            if latest_day is None or old_day is None:
                continue
            tree_conflicts.append(
                DeadlineConflict(
                    parent_id=parent_id,
                    parent_deadline=_iso(old_day),
                    child_id=latest.id,
                    child_deadline=_iso(latest_day),
                )
            )
    if not tree_conflicts:
        return {"ok": True}
    return {
        "ok": False,
        "code": "deadline_order",
        "conflicts": [row.as_dict() for row in tree_conflicts],
        "options": _options(tree_conflicts),
    }
