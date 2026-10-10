"""Invalidate agent-context trio before mutate (A21) — delete-if-exists ×3."""
from __future__ import annotations

from typing import Any

from agent_context_build import (
    OUTPUT_CHARTERS_REL,
    OUTPUT_LIGHT_REL,
    OUTPUT_REL,
)
from drive_io import DriveNotFoundError

TOMBSTONE_PATHS: tuple[str, ...] = (
    OUTPUT_REL,
    OUTPUT_LIGHT_REL,
    OUTPUT_CHARTERS_REL,
)


def delete_context_tombstone(vault: Any) -> list[str]:
    """Delete full/light/charters if present. Returns deleted relative paths."""
    deleted: list[str] = []
    for rel in TOMBSTONE_PATHS:
        try:
            if hasattr(vault, "exists") and not vault.exists(rel):
                continue
            vault.delete(rel, permanent=True)
            deleted.append(rel)
        except DriveNotFoundError:
            continue
    return deleted
