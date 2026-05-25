#!/usr/bin/env python3
"""Rewrite task ``project:`` frontmatter from bare slug alias to hub filename.

Before:  ``project: "[[strategy]]"``
After:   ``project: "[[Strategy]]"``  (target = ``02-PROJEKTY/Strategy.md``)

The display value of the wikilink becomes the human-readable hub name in any
Obsidian view (Bases tables, hub embeds, backlinks panel) while clicks still
resolve to the hub charter file (not the slug folder).

Mapping is read from ``OBSIDIAN/00-System/migration-mapping.json`` (falls back
to ``scripts/migration-mapping.json``). Idempotent — links that already point
to the hub filename are left untouched. The ``slug:`` field is preserved as
primary key for Bases filters / lifecycle scripts.

Targets (default):
  - OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md
  - OBSIDIAN/07-ARCHIV/tasks-done/<slug>/*.md

Usage:
  python3 scripts/backfill_task_project_link.py            # dry-run
  python3 scripts/backfill_task_project_link.py --write    # actually edit files
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VAULT_DEFAULT = REPO_ROOT / "OBSIDIAN"
MAPPING_VAULT = VAULT_DEFAULT / "00-System" / "migration-mapping.json"
MAPPING_REPO = REPO_ROOT / "scripts" / "migration-mapping.json"

PROJECT_LINE_RE = re.compile(r'^project\s*:\s*"\[\[(?P<target>[^\]]+)\]\]"\s*$')
SLUG_LINE_RE = re.compile(r"^slug\s*:\s*(?P<slug>\S+)\s*$")


@dataclass
class Plan:
    path: Path
    line_idx: int
    old_target: str
    new_target: str
    slug: str


def load_mapping() -> dict[str, str]:
    """slug → hub_basename (without .md)."""
    for src in (MAPPING_VAULT, MAPPING_REPO):
        if src.exists():
            data = json.loads(src.read_text(encoding="utf-8"))
            return {
                row["slug"]: row["hub_filename"].removesuffix(".md")
                for row in data
                if row.get("slug") and row.get("hub_filename")
            }
    raise FileNotFoundError("migration-mapping.json not found in vault or scripts/")


def split_frontmatter(text: str) -> tuple[list[str], list[str], int] | None:
    """Return (frontmatter_lines, body_lines, fm_end_line_idx_inclusive)."""
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return None
    lines = text.splitlines(keepends=False)
    if lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :], i
    return None


def iter_task_files(vault: Path) -> list[Path]:
    files: list[Path] = []
    for sub in ("02-PROJEKTY", "07-ARCHIV/tasks-done"):
        root = vault / sub
        if not root.exists():
            continue
        for p in root.rglob("*.md"):
            parts = p.parts
            if sub == "02-PROJEKTY" and "tasks" not in parts:
                continue
            files.append(p)
    return sorted(files)


def build_plan(path: Path, mapping: dict[str, str]) -> Plan | str | None:
    """Plan, skip reason str, or None for already-correct files."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        return f"unicode-error: {e}"
    parts = split_frontmatter(text)
    if parts is None:
        return "no-frontmatter"
    fm_lines, _body, _end = parts

    slug = None
    project_idx = -1
    project_target = None
    for i, line in enumerate(fm_lines):
        if (m := SLUG_LINE_RE.match(line)):
            slug = m.group("slug").strip().strip('"').strip("'")
        if project_idx == -1 and (m := PROJECT_LINE_RE.match(line)):
            project_idx = i
            project_target = m.group("target").strip()

    if project_idx == -1:
        return "no-project-line"
    if slug is None:
        return "no-slug-field"
    if slug not in mapping:
        return f"slug-not-in-mapping:{slug}"

    new_target = mapping[slug]
    if project_target == new_target:
        return None
    return Plan(
        path=path,
        line_idx=project_idx,
        old_target=project_target,
        new_target=new_target,
        slug=slug,
    )


def apply_plan(plan: Plan) -> None:
    text = plan.path.read_text(encoding="utf-8")
    parts = split_frontmatter(text)
    assert parts is not None
    fm_lines, body_lines, _end = parts
    fm_lines[plan.line_idx] = f'project: "[[{plan.new_target}]]"'
    rebuilt = "---\n" + "\n".join(fm_lines) + "\n---\n" + "\n".join(body_lines)
    if not rebuilt.endswith("\n"):
        rebuilt += "\n"
    plan.path.write_text(rebuilt, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply changes (default: dry-run)")
    parser.add_argument("--root", type=Path, default=VAULT_DEFAULT, help="vault root (defaults to OBSIDIAN/)")
    parser.add_argument("--samples", type=int, default=8, help="sample count to print")
    args = parser.parse_args()

    vault = args.root.resolve()
    if not vault.exists():
        print(f"vault not found: {vault}", file=sys.stderr)
        return 2

    mapping = load_mapping()
    print(f"loaded {len(mapping)} slug → hub mappings")

    files = iter_task_files(vault)
    plans: list[Plan] = []
    skips: dict[str, list[Path]] = {}
    for f in files:
        result = build_plan(f, mapping)
        if result is None:
            continue
        if isinstance(result, Plan):
            plans.append(result)
        else:
            skips.setdefault(result, []).append(f)

    print(f"task files scanned:  {len(files)}")
    print(f"already-correct:     {len(files) - len(plans) - sum(len(v) for v in skips.values())}")
    print(f"to-patch:            {len(plans)}")
    for reason, paths in sorted(skips.items()):
        print(f"skipped ({reason}): {len(paths)}")
        for p in paths[:5]:
            print(f"   - {p.relative_to(vault)}")

    if plans:
        print("\nsamples:")
        for p in plans[: args.samples]:
            rel = p.path.relative_to(vault)
            print(f"  {rel}")
            print(f"    [[{p.old_target}]]  →  [[{p.new_target}]]   (slug={p.slug})")

    if not args.write:
        print("\n(dry-run; re-run with --write to apply)")
        return 0

    print("\napplying patches…")
    for plan in plans:
        apply_plan(plan)
    print(f"patched {len(plans)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
