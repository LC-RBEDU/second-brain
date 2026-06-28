#!/usr/bin/env python3
"""Audit material link integrity (VC7-8).

Rules:
- 02-PROJEKTY/<slug>/materials/*.md must be referenced by a task or hub → else orphan
- 05-RESOURCES/*.md standalone is OK (info only, not orphan error)

Usage:
  python3 scripts/audit_material_links.py
  python3 scripts/audit_material_links.py --vault PATH
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import DEFAULT_VAULT, collect_tasks, parse_frontmatter  # noqa: E402
from vault_reference import parse_wikilinks, strip_wikilink  # noqa: E402


def _collect_references(vault: Path) -> set[str]:
    refs: set[str] = set()
    for task in collect_tasks(vault, archive=False) + collect_tasks(vault, archive=True):
        tp = vault / task.rel_path
        if not tp.exists():
            continue
        try:
            fm, body = parse_frontmatter(tp.read_text(encoding="utf-8"))
        except OSError:
            continue
        for m in fm.get("materials") or []:
            refs.add(strip_wikilink(str(m)))
            refs.add(Path(str(m)).stem)
        for wl in parse_wikilinks(body):
            refs.add(strip_wikilink(wl))
    for hub in (vault / "02-PROJEKTY").glob("*.md"):
        try:
            _, body = parse_frontmatter(hub.read_text(encoding="utf-8"))
        except OSError:
            continue
        for wl in parse_wikilinks(body):
            refs.add(strip_wikilink(wl))
    return refs


def audit(vault: Path) -> dict:
    refs = _collect_references(vault)
    orphans: list[str] = []
    resources_unlinked: list[str] = []
    missing_type: list[str] = []

    for slug_dir in (vault / "02-PROJEKTY").iterdir():
        if not slug_dir.is_dir():
            continue
        mat_dir = slug_dir / "materials"
        if not mat_dir.exists():
            continue
        for md in mat_dir.rglob("*.md"):
            try:
                rel = str(md.relative_to(vault))
                fm, _ = parse_frontmatter(md.read_text(encoding="utf-8"))
            except OSError:
                continue
            if (fm.get("type") or "").lower() != "material":
                missing_type.append(rel)
            stem = md.stem
            linked = stem in refs or any(stem in r or r in stem for r in refs)
            if not linked:
                orphans.append(rel)

    res_root = vault / "05-RESOURCES"
    if res_root.exists():
        for md in res_root.rglob("*.md"):
            try:
                fm, _ = parse_frontmatter(md.read_text(encoding="utf-8"))
            except OSError:
                continue
            projs = fm.get("projects") or []
            if not projs:
                resources_unlinked.append(str(md.relative_to(vault)))

    return {
        "orphans": orphans,
        "missing_type_material": missing_type,
        "resources_unlinked_info": resources_unlinked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    args = parser.parse_args()
    if not args.vault.exists():
        sys.stderr.write(f"ERROR: vault not found: {args.vault}\n")
        return 1

    report = audit(args.vault)
    orphans = report["orphans"]
    missing = report["missing_type_material"]
    print(f"orphans (project materials): {len(orphans)}")
    for o in orphans[:50]:
        print(f"  ORPHAN {o}")
    print(f"missing type:material: {len(missing)}")
    for m in missing[:30]:
        print(f"  MISSING_TYPE {m}")
    print(f"resources unlinked (info): {len(report['resources_unlinked_info'])}")
    return 1 if orphans else 0


if __name__ == "__main__":
    sys.exit(main())
