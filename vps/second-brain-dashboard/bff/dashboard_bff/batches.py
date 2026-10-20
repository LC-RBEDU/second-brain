"""Pack a cleanup into Brain batches. A family stays in one batch. Cap is 80."""

from __future__ import annotations

from typing import Any


class BatchRejected(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


def _families(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ids = [str(item["id"]) for item in items]
    parent = {node: node for node in ids}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    known = set(ids)
    for item in items:
        child = str(item["id"])
        above = str(item.get("parent") or "")
        if above in known:
            parent[find(child)] = find(above)
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(find(str(item["id"])), []).append(item)
    return list(groups.values())


def pack_batches(
    items: list[dict[str, Any]],
    *,
    limit: int = 40,
    cap: int = 80,
) -> list[list[dict[str, Any]]]:
    if len(items) > cap or any(len(group) > cap for group in _families(items)):
        raise BatchRejected("batch_too_large")
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for group in _families(items):
        if len(group) > limit:
            if current:
                chunks.append(current)
                current = []
            chunks.append(group)
            continue
        if current and len(current) + len(group) > limit:
            chunks.append(current)
            current = []
        current.extend(group)
    if current:
        chunks.append(current)
    return chunks
