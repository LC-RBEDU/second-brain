"""Frontmatter dual-read helpers (A7 / B16) — no bulk FM in F2."""
from __future__ import annotations

from typing import Any


def read_aliases(fm: dict[str, Any]) -> list[str]:
    """Dual-read: prefer empty for new writes; accept legacy ``aliases`` if present."""
    raw = fm.get("aliases")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def strip_aliases_for_new_write(fm: dict[str, Any]) -> dict[str, Any]:
    """New task writes omit aliases (A7)."""
    out = dict(fm)
    out.pop("aliases", None)
    return out
