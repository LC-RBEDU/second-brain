"""Refuse a write that would create a project folder without a hub charter."""
from __future__ import annotations

import re
from typing import Any

from app.errors import BrainClientError


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    return text[: end + 4]


def require_project(vault: Any, slug: str) -> str:
    """Return the hub file stem. Unknown slug and a directory error both refuse the write."""
    try:
        metas = vault.list_dir("02-PROJEKTY", pattern="*.md", recursive=False)
    except Exception as exc:
        raise BrainClientError(
            message="unknown project; a new hub is only created by an explicit command",
            status_code=400,
            error_reason="unknown_project",
            detail={"errors": ["unknown_project"]},
        ) from exc
    wanted = re.compile(
        rf"(?m)^slug:\s*(?:\"{re.escape(slug)}\"|'{re.escape(slug)}'|{re.escape(slug)})\s*$"
    )
    stems: list[str] = []
    for meta in metas:
        name = str(getattr(meta, "name", "") or "")
        rel = getattr(meta, "rel_path", "")
        if not rel or not name or "/" in name:
            continue
        try:
            text, _ = vault.read_text(rel)
        except Exception:
            continue
        if wanted.search(_frontmatter(text)):
            stems.append(name[:-3] if name.endswith(".md") else name)
    if not stems:
        raise BrainClientError(
            message="unknown project; a new hub is only created by an explicit command",
            status_code=400,
            error_reason="unknown_project",
            detail={"errors": ["unknown_project"]},
        )
    if len(stems) > 1:
        raise BrainClientError(
            message="hub_ambiguous",
            status_code=400,
            error_reason="hub_ambiguous",
            detail={"errors": ["hub_ambiguous"]},
        )
    return stems[0]


def folder_slug_from_path(path: str) -> str:
    parts = (path or "").split("/")
    if len(parts) >= 3 and parts[0] == "02-PROJEKTY" and parts[2] == "tasks":
        return parts[1]
    return ""
