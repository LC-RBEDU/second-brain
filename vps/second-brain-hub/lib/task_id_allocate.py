"""Allocate next free task ID — ceiling scan over vault API (never recycle).

Port of scripts/next_task_id.py L61–162 for Brain / hub callers that hold a vault.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

TASK_DIRS = ("02-PROJEKTY", "07-ARCHIV")
MAPPING_REL = "00-System/migration-mapping.json"

# The level letter is not part of the counter: RBU-E69 and RBU-S70 share one
# sequence, so promoting a story to an epic never frees a number for reuse.
ID_RE = re.compile(r"^([A-Z]+)(?:-[EST])?(\d+)[a-z]?$")
LEVEL_LETTER = {"epic": "E", "story": "S", "task": "T"}


@dataclass(frozen=True)
class _Entry:
    name: str
    rel_path: str


def _frontmatter_text(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?\n)---", text, re.S)
    if not m:
        return {}
    try:
        import yaml

        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def _safe_read_text(vault: Any, rel: str) -> str:
    try:
        text, _meta = vault.read_text(rel)
        return text
    except Exception:
        return ""


def _safe_list_md(vault: Any, top: str) -> list[_Entry]:
    if hasattr(vault, "exists") and not vault.exists(top):
        return []
    try:
        metas = vault.list_dir(top, pattern="*.md", recursive=True)
    except Exception:
        return []
    out: list[_Entry] = []
    for m in metas:
        name = getattr(m, "name", None) or Path(getattr(m, "rel_path", "")).name
        rel = getattr(m, "rel_path", None) or f"{top}/{name}"
        if not str(name).endswith(".md"):
            continue
        out.append(_Entry(name=str(name), rel_path=str(rel)))
    return out


def _iter_all_md(vault: Any) -> Iterable[_Entry]:
    """Best-effort vault-wide .md listing (wikilink scan)."""
    # Prefer listing from known tops + 00-System rather than requiring root list.
    seen: set[str] = set()
    for top in (*TASK_DIRS, "00-System", "01-INBOX", "03-AREAS", "05-RESOURCES"):
        for entry in _safe_list_md(vault, top):
            if entry.rel_path in seen:
                continue
            seen.add(entry.rel_path)
            yield entry


def prefix_for_slug(vault: Any, slug: str) -> str:
    """Prefix from migration-mapping.json; fall back to initials of the slug."""
    try:
        if hasattr(vault, "exists") and not vault.exists(MAPPING_REL):
            mapping: list = []
        else:
            data, _ = vault.read_json(MAPPING_REL)
            mapping = data if isinstance(data, list) else []
    except Exception:
        mapping = []
    for entry in mapping:
        if isinstance(entry, dict) and entry.get("slug") == slug and entry.get("id_prefix"):
            return str(entry["id_prefix"])
    return "".join(part[0] for part in slug.split("-") if part).upper()[:3]


def ceiling_for_prefix(vault: Any, prefix: str) -> tuple[int, str]:
    """Highest number ever used with this prefix, and where it was seen."""
    best, where = 0, "(nic nenalezeno)"
    exact = re.compile(rf"\b{re.escape(prefix)}(?:-[EST])?(\d+)\b")

    def consider(n: int, src: str) -> None:
        nonlocal best, where
        if n > best:
            best, where = n, src

    for top in TASK_DIRS:
        for entry in _safe_list_md(vault, top):
            m = exact.match(entry.name)
            if m:
                consider(int(m.group(1)), f"soubor {entry.name}")
            tid = str(_frontmatter_text(_safe_read_text(vault, entry.rel_path)).get("id") or "")
            m = ID_RE.match(tid)
            if m and m.group(1) == prefix:
                consider(int(m.group(2)), f"frontmatter {entry.name}")

    mention_re = re.compile(
        rf"\[\[{re.escape(prefix)}(?:-[EST])?(\d+)(?:[\s|\]—-]|\s+[—-])"
    )
    for entry in _iter_all_md(vault):
        text = _safe_read_text(vault, entry.rel_path)
        for m in mention_re.finditer(text):
            consider(int(m.group(1)), f"wikilink v {entry.rel_path}")

    return best, where


def next_id(vault: Any, slug: str) -> tuple[str, str]:
    prefix = prefix_for_slug(vault, slug)
    ceiling, where = ceiling_for_prefix(vault, prefix)
    return f"{prefix}{ceiling + 1}", where


def peek_ids(vault: Any, slug: str, count: int) -> list[tuple[str, str]]:
    """Next ``count`` bare ids from one ceiling read. Nothing is written."""
    if count < 1:
        return []
    prefix = prefix_for_slug(vault, slug)
    ceiling, where = ceiling_for_prefix(vault, prefix)
    return [(f"{prefix}{ceiling + offset}", where) for offset in range(1, count + 1)]


def with_level(task_id: str, level: str) -> str:
    """Insert the hierarchy level into an ID: RBU73 + story -> RBU-S73."""
    m = re.match(r"^([A-Z]+)(?:-[EST])?(\d+)$", task_id)
    if not m:
        return task_id
    return f"{m.group(1)}-{LEVEL_LETTER[level]}{m.group(2)}"


def find_duplicates(vault: Any) -> dict[str, list[str]]:
    """IDs claimed by more than one task file (rel paths)."""
    rotation = re.compile(r"^[A-Z]+(?:-[EST])?\d+-\d{4}-\d{2}-\d{2}\.md$")
    claims: dict[str, list[str]] = defaultdict(list)
    for top in TASK_DIRS:
        for entry in _safe_list_md(vault, top):
            parent = str(Path(entry.rel_path).parent)
            if "/tasks" not in parent and "tasks-done" not in parent:
                continue
            tid = str(_frontmatter_text(_safe_read_text(vault, entry.rel_path)).get("id") or "")
            if tid:
                claims[tid].append(entry.rel_path)

    out: dict[str, list[str]] = {}
    for tid, paths in claims.items():
        if len(paths) < 2:
            continue
        if sum(1 for p in paths if not rotation.match(Path(p).name)) <= 1:
            continue
        out[tid] = sorted(paths)
    return out


class PathVault:
    """Minimal vault facade over a local Path root (Mac CLI)."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def exists(self, rel_path: str) -> bool:
        return (self.root / rel_path).exists()

    def read_text(self, rel_path: str, *, encoding: str = "utf-8") -> tuple[str, None]:
        return (self.root / rel_path).read_text(encoding=encoding, errors="ignore"), None

    def read_json(self, rel_path: str) -> tuple[Any, None]:
        text, _ = self.read_text(rel_path)
        return json.loads(text), None

    def list_dir(
        self,
        rel_path: str,
        *,
        pattern: str | None = None,
        recursive: bool = False,
        include_folders: bool = False,
    ) -> list[_Entry]:
        _ = include_folders
        base = self.root / rel_path
        if not base.is_dir():
            return []
        paths = base.rglob("*") if recursive else base.iterdir()
        out: list[_Entry] = []
        for path in paths:
            if not path.is_file():
                continue
            if pattern == "*.md" and path.suffix != ".md":
                continue
            rel = str(path.relative_to(self.root))
            out.append(_Entry(name=path.name, rel_path=rel))
        return out
