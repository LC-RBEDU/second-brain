"""Shared materials frontmatter normalize (create + update_task)."""
from __future__ import annotations

from typing import Any


def normalize_materials(raw: Any) -> list[str]:
    """Coerce materials to a deduped list of non-empty strings (order preserved)."""
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [line.strip() for line in raw.splitlines()]
    elif isinstance(raw, list):
        items = [str(item).strip() for item in raw]
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
