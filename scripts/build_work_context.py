#!/usr/bin/env python3
"""Build per-project work-context bundle (.md) for agent execution support.

Pre-resolves hub charter + tasks + materials (incl. extracted text) + outputs
+ archive sources referenced by tasks.

Usage:
  python3 scripts/build_work_context.py rb-universe-development
  python3 scripts/build_work_context.py --all
  python3 scripts/build_work_context.py finance --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip3 install pyyaml\n")
    sys.exit(1)

# Reuse parsers from build_agent_context
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import (  # noqa: E402
    DEFAULT_VAULT,
    FRONTMATTER_RE,
    HUB_TITLE_RE,
    collect_projects,
    collect_tasks,
    parse_frontmatter,
    _list_str,
)

SECTION_EXTRACT = "## Extrahovaný text"
MAX_BODY_CHARS = 120_000
MAX_MATERIAL_CHARS = 40_000


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 40] + "\n\n… _(zkráceno)_\n"


def _section(body: str, heading: str) -> str:
    pat = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    m = pat.search(body)
    if not m:
        return ""
    rest = body[m.end() :]
    nxt = re.search(r"^##\s+\S", rest, re.MULTILINE)
    block = rest[: nxt.start()] if nxt else rest
    return block.strip()


def _resolve_wikilink_path(vault: Path, link: str) -> Path | None:
    link = link.strip().strip('"').strip("'")
    if link.startswith("http"):
        return None
    bare = link.replace("[[", "").replace("]]", "").split("|")[0].strip()
    if not bare:
        return None
    candidates = [
        vault / "02-PROJEKTY" / bare,
        vault / "07-ARCHIV" / bare,
        vault / "05-RESOURCES" / bare,
    ]
    for c in candidates:
        if c.is_file():
            return c
        if c.with_suffix(".md").is_file():
            return c.with_suffix(".md")
    for base in (vault / "02-PROJEKTY", vault / "07-ARCHIV", vault / "05-RESOURCES"):
        if not base.exists():
            continue
        for hit in base.rglob(f"{bare}.md"):
            return hit
        for hit in base.rglob(bare):
            if hit.is_file():
                return hit
    return None


def _load_source_archive(vault: Path, source: str) -> str:
    p = _resolve_wikilink_path(vault, source)
    if not p or not p.exists():
        return f"_(source nenalezeno: {source})_"
    try:
        _, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        return _truncate(body.strip(), MAX_MATERIAL_CHARS)
    except OSError:
        return f"_(source unreadable: {source})_"


def _collect_materials(vault: Path, slug: str, tasks: list) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    mat_dir = vault / "02-PROJEKTY" / slug / "materials"
    if mat_dir.exists():
        for md in sorted(mat_dir.rglob("*.md")):
            rel = str(md.relative_to(vault))
            if rel in seen:
                continue
            seen.add(rel)
            try:
                fm, body = parse_frontmatter(md.read_text(encoding="utf-8"))
            except OSError:
                continue
            title = fm.get("title") or md.stem
            out.append((rel, f"### {title}\n\n{_truncate(body.strip(), MAX_MATERIAL_CHARS)}"))

    for t in tasks:
        if t.slug != slug:
            continue
        for mat in t.materials or []:
            p = _resolve_wikilink_path(vault, mat)
            if not p:
                continue
            rel = str(p.relative_to(vault)) if p.is_relative_to(vault) else str(p)
            if rel in seen:
                continue
            seen.add(rel)
            try:
                fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            except OSError:
                continue
            title = fm.get("title") or p.stem
            out.append((rel, f"### {title}\n\n{_truncate(body.strip(), MAX_MATERIAL_CHARS)}"))

    return out


def _collect_outputs(vault: Path, slug: str) -> list[str]:
    root = vault / "02-PROJEKTY" / slug
    if not root.exists():
        return []
    skip = {"tasks", "materials"}
    out: list[str] = []
    for p in sorted(root.iterdir()):
        if p.name.startswith(".") or p.name in skip:
            continue
        if p.is_file() and p.suffix.lower() in (".md", ".mermaid", ".json", ".py", ".ts"):
            out.append(p.name)
    return out


def build_work_context_md(vault: Path, slug: str) -> str | None:
    hub_path = None
    hub_fm: dict[str, Any] = {}
    hub_body = ""
    for hub in (vault / "02-PROJEKTY").glob("*.md"):
        try:
            text = hub.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, body = parse_frontmatter(text)
        if (fm.get("type") or "").lower() != "project":
            continue
        if (fm.get("slug") or hub.stem) == slug:
            hub_path = hub
            hub_fm, hub_body = fm, body
            break
    if not hub_path:
        return None

    title_m = HUB_TITLE_RE.search(hub_body)
    title = title_m.group(1).strip() if title_m else hub_path.stem
    active = [t for t in collect_tasks(vault, archive=False) if t.slug == slug and t.status != "Done"]

    lines = [
        "---",
        f"slug: {slug}",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "type: work-context",
        "---",
        "",
        f"# Work context — {title}",
        "",
        f"**Hub:** `02-PROJEKTY/{hub_path.name}`",
        "",
        "## Sources (hub frontmatter)",
        "",
        f"- sources: {_list_str(hub_fm.get('sources'))}",
        f"- notebooklm: {_list_str(hub_fm.get('notebooklm'))}",
        f"- workspace: {json.dumps(hub_fm.get('workspace') or {}, ensure_ascii=False)}",
        "",
    ]

    for sec in ("## Scope", "## Kontext", "## Zdroje dat", "## Otevřené otázky"):
        content = _section(hub_body, sec)
        if content:
            lines.extend([sec, "", content, ""])

    lines.extend(["## Aktivní tasky", ""])
    for t in sorted(active, key=lambda x: (-x.priority_score, x.id)):
        lines.append(f"- **{t.id} — {t.title}** ({t.status}, score={t.priority_score})")
        if t.materials:
            lines.append(f"  - materials: {', '.join(t.materials)}")
        if getattr(t, "source", None):
            lines.append(f"  - source: {t.source}")
    lines.append("")

    lines.extend(["## Task těla", ""])
    for t in sorted(active, key=lambda x: x.id):
        tp = vault / t.rel_path
        if not tp.exists():
            continue
        try:
            _, body = parse_frontmatter(tp.read_text(encoding="utf-8"))
        except OSError:
            continue
        lines.extend([f"### {t.id} — {t.title}", "", _truncate(body.strip(), 8000), ""])

    materials = _collect_materials(vault, slug, active)
    if materials:
        lines.extend(["## Materiály", ""])
        for rel, block in materials:
            lines.extend([f"<!-- {rel} -->", block, ""])

    sources_seen: set[str] = set()
    for t in active:
        src = getattr(t, "source", None)
        if not src or src in sources_seen:
            continue
        sources_seen.add(src)
        lines.extend([f"## Archivní zdroj — {src}", "", _load_source_archive(vault, src), ""])

    outputs = _collect_outputs(vault, slug)
    if outputs:
        lines.extend(["## Outputs (root projektu)", ""])
        for o in outputs:
            lines.append(f"- `{o}`")
        lines.append("")

    return _truncate("\n".join(lines), MAX_BODY_CHARS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", nargs="?", default="")
    parser.add_argument("--all", action="store_true", help="Build for all active projects")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    out_dir = args.vault / "00-System" / "Work-Context"
    slugs: list[str] = []
    if args.all:
        slugs = [p.slug for p in collect_projects(args.vault) if p.status in ("active", "")]
    elif args.slug:
        slugs = [args.slug]
    else:
        parser.print_help()
        return 1

    n = 0
    for slug in slugs:
        md = build_work_context_md(args.vault, slug)
        if not md:
            sys.stderr.write(f"SKIP unknown slug: {slug}\n")
            continue
        out = out_dir / f"{slug}.md"
        if args.dry_run:
            print(f"DRY {out}: {len(md)} chars")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"work-context: {slug} → {out.relative_to(args.vault)}")
        n += 1
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
