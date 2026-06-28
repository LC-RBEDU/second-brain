#!/usr/bin/env python3
"""Shared vault reference resolution, wikilink parsing, and material identity (VC7)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
HEADING_RE = re.compile(r"^##\s+\S", re.MULTILINE)

CANONICAL_HUB_SECTIONS = (
    "## Cíl",
    "## Scope",
    "## Definition of done",
    "## People",
    "## Kontext",
    "## Zdroje dat",
    "## Otevřené otázky",
)

ALLOWED_EXTRA_HUB_SECTIONS = (
    "## Stav (auto)",
    "## Aktivní úkoly",
    "## Materiály",
    "## Výstupy",
    "## Recently done",
    "## Progress",
)

# Raw source material_kind values (negative filter in Bases hides these)
SOURCE_MATERIAL_KINDS = frozenset(
    {
        "sembly",
        "gdoc",
        "slack",
        "slack-capture",
        "email",
        "meeting-notes",
    }
)

SECTION_SHRUTI = "## Shrnutí"
SECTION_EXTRACT = "## Extrahovaný text"
SECTION_TLDR = "## TL;DR"

MAX_LAYER_B_CHARS = 500_000
MAX_LAYER_B_NODES = 60


@dataclass
class ResolvedNode:
    rel_path: str
    node_type: str  # task | material | hub | archive | resource | unknown
    slug: str | None = None
    title: str = ""
    body: str = ""
    frontmatter: dict[str, Any] = field(default_factory=dict)


def parse_wikilinks(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def strip_wikilink(link: str) -> str:
    s = link.strip().strip('"').strip("'")
    if s.startswith("[[") and s.endswith("]]"):
        s = s[2:-2]
    return s.split("|")[0].strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section_text(body: str, heading: str) -> str | None:
    pat = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    m = pat.search(body)
    if not m:
        return None
    rest = body[m.end() :]
    nxt = HEADING_RE.search(rest)
    block = (rest[: nxt.start()] if nxt else rest).strip()
    return block or None


def material_summary(body: str, max_fallback: int = 1200) -> str:
    """Layer B summary with degrading fallback until VC7-9 backfill."""
    for heading in (SECTION_SHRUTI, SECTION_TLDR):
        block = section_text(body, heading)
        if block:
            return block
    lines = body.splitlines()
    teaser_lines: list[str] = []
    for line in lines:
        if line.startswith("> "):
            teaser_lines.append(line[2:].strip())
        elif teaser_lines and line.strip() and not line.startswith("#"):
            break
    if teaser_lines:
        return "\n".join(f"- {t}" if not t.startswith("-") else t for t in teaser_lines)
    extracted = section_text(body, SECTION_EXTRACT)
    if extracted:
        return extracted[:max_fallback] + ("…" if len(extracted) > max_fallback else "")
    stripped = body.strip()
    if len(stripped) <= max_fallback:
        return stripped
    return stripped[: max_fallback - 20] + "…"


def hub_section_headings(body: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"^##\s+.+$", body, re.MULTILINE)]


def validate_hub_charter(body: str, hub_filename: str) -> list[str]:
    """Warn-only charter validator (VC7-6). Does not rewrite content."""
    warnings: list[str] = []
    headings = hub_section_headings(body)
    heading_set = set(headings)
    for required in CANONICAL_HUB_SECTIONS:
        if required not in heading_set:
            warnings.append(f"{hub_filename}: chybí povinná sekce {required}")
    legacy = (
        "## Lidé / spolupráce",
        "## Hranice / vymezení",
        "## Metriky / KPI",
        "## Lidé",
    )
    for leg in legacy:
        if leg in heading_set:
            warnings.append(f"{hub_filename}: legacy sekce {leg} — přejmenuj na kanonickou")
    allowed = set(CANONICAL_HUB_SECTIONS) | set(ALLOWED_EXTRA_HUB_SECTIONS)
    for h in headings:
        if h.startswith("## Tým"):
            continue
        if h not in allowed and not h.startswith("## Tým"):
            if h not in legacy:
                warnings.append(f"{hub_filename}: neznámá extra sekce {h}")
    return warnings


def resolve_path(
    vault: Path,
    link: str,
    *,
    prefer_active_materials: bool = True,
) -> Path | None:
    """Resolve wikilink/path; active materials/ beats 07-ARCHIV/materials/."""
    link = strip_wikilink(link)
    if not link or link.startswith("http"):
        return None

    if "/" in link or link.endswith(".md"):
        direct = vault / link
        if direct.is_file():
            return direct
        if direct.with_suffix(".md").is_file():
            return direct.with_suffix(".md")

    bare = Path(link).stem if link.endswith(".md") else link
    search_roots: list[Path] = []
    if prefer_active_materials:
        search_roots.append(vault / "02-PROJEKTY")
    search_roots.extend(
        [
            vault / "05-RESOURCES",
            vault / "07-ARCHIV",
            vault / "02-PROJEKTY",
            vault / "01-INBOX",
        ]
    )

    hits: list[Path] = []
    seen: set[Path] = set()
    for base in search_roots:
        if not base.exists():
            continue
        for pat in (f"{bare}.md", bare):
            for hit in base.rglob(pat):
                if hit.is_file() and hit.suffix.lower() in (".md",) and hit not in seen:
                    seen.add(hit)
                    hits.append(hit)

    if not hits:
        return None

    def rank(p: Path) -> tuple[int, str]:
        s = str(p)
        if "/materials/" in s and "/07-ARCHIV/" not in s:
            return (0, s)
        if "/07-ARCHIV/materials/" in s:
            return (2, s)
        if "/tasks/" in s:
            return (1, s)
        return (3, s)

    hits.sort(key=rank)
    return hits[0]


def load_node(vault: Path, path: Path, parse_frontmatter: Callable[[str], tuple[dict, str]]) -> ResolvedNode | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm, body = parse_frontmatter(text)
    try:
        rel = str(path.relative_to(vault))
    except ValueError:
        rel = str(path)
    node_type = str(fm.get("type") or "unknown").lower()
    slug = fm.get("slug")
    if isinstance(slug, str):
        slug = slug.strip()
    title = str(fm.get("title") or path.stem)
    return ResolvedNode(
        rel_path=rel,
        node_type=node_type,
        slug=slug,
        title=title,
        body=body,
        frontmatter=fm,
    )


def extract_references_from_task(fm: dict, body: str) -> list[str]:
    refs: list[str] = []
    for key in ("materials", "blocked_by", "project"):
        val = fm.get(key)
        if isinstance(val, list):
            refs.extend(str(x) for x in val)
        elif val:
            refs.append(str(val))
    src = fm.get("source")
    if src:
        refs.append(str(src))
    refs.extend(parse_wikilinks(body))
    return refs


def extract_references_from_material(fm: dict, body: str) -> list[str]:
    refs: list[str] = []
    for key in ("projects", "areas"):
        val = fm.get(key)
        if isinstance(val, list):
            refs.extend(str(x) for x in val)
        elif val:
            refs.append(str(val))
    refs.extend(parse_wikilinks(body))
    return refs


def build_reference_index(
    vault: Path,
    *,
    parse_frontmatter: Callable[[str], tuple[dict, str]],
    list_tasks: Callable[[], list[Any]],
    list_archived_tasks: Callable[[], list[Any]] | None = None,
) -> dict[str, Any]:
    """Build backlinks map for build_work_context (VC7-3)."""
    backlinks: dict[str, list[str]] = {}
    nodes: dict[str, dict[str, Any]] = {}

    def add_backlink(target: str, source_id: str) -> None:
        key = strip_wikilink(target)
        if not key:
            return
        backlinks.setdefault(key, [])
        if source_id not in backlinks[key]:
            backlinks[key].append(source_id)

    def scan_file(path: Path, source_id: str, refs: list[str]) -> None:
        for ref in refs:
            add_backlink(ref, source_id)
        nodes[source_id] = {
            "rel_path": str(path.relative_to(vault)) if path.is_relative_to(vault) else str(path),
            "references": [strip_wikilink(r) for r in refs],
        }

    for task in list_tasks():
        tp = vault / task.rel_path
        if not tp.exists():
            continue
        try:
            fm, body = parse_frontmatter(tp.read_text(encoding="utf-8"))
        except OSError:
            continue
        refs = extract_references_from_task(fm, body)
        scan_file(tp, task.id, refs)

    if list_archived_tasks:
        for task in list_archived_tasks():
            tp = vault / task.rel_path
            if not tp.exists():
                continue
            try:
                fm, body = parse_frontmatter(tp.read_text(encoding="utf-8"))
            except OSError:
                continue
            refs = extract_references_from_task(fm, body)
            scan_file(tp, task.id, refs)

    mat_dirs = [
        vault / "02-PROJEKTY",
        vault / "05-RESOURCES",
        vault / "07-ARCHIV" / "materials",
    ]
    for base in mat_dirs:
        if not base.exists():
            continue
        for md in base.rglob("*.md"):
            if "/tasks/" in str(md):
                continue
            try:
                fm, body = parse_frontmatter(md.read_text(encoding="utf-8"))
            except OSError:
                continue
            if (fm.get("type") or "").lower() not in ("material", "attachment"):
                if "/materials/" not in str(md) and "05-RESOURCES" not in str(md):
                    continue
            try:
                rel = str(md.relative_to(vault))
            except ValueError:
                rel = str(md)
            refs = extract_references_from_material(fm, body)
            scan_file(md, rel, refs)

    return {
        "version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "backlinks": backlinks,
        "nodes": nodes,
    }


def write_reference_index(vault: Path, index: dict[str, Any]) -> Path:
    out = vault / "00-System" / "reference-index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load_reference_index(vault: Path) -> dict[str, Any]:
    p = vault / "00-System" / "reference-index.json"
    if not p.exists():
        return {"backlinks": {}, "nodes": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"backlinks": {}, "nodes": {}}
