#!/usr/bin/env python3
"""Allocate the next free task ID for a project — scan-then-max, never recycle.

    python3 scripts/next_task_id.py <slug>          # → e.g. "F42"
    python3 scripts/next_task_id.py <slug> --why    # + where the ceiling came from
    python3 scripts/next_task_id.py --check         # report duplicate IDs, exit 1 if any

Why this exists as a script and not as prose in a spec: every duplicate ID in
this vault was created by hand during triage, by a human or an agent following
the algorithm from memory. The rules were right; nothing enforced them. A
command that answers "what is the next ID" removes the step where the mistake
happens.

Two failure modes it has to survive, both observed:

1. **An earlier task already sits in the archive.** Scanning only
   `02-PROJEKTY/<slug>/tasks/` reuses the ID of anything already closed.
2. **The task file no longer exists at all.** A deleted task (S21, PD5) leaves
   no frontmatter to scan, so max+1 hands its ID to something else while
   wikilinks and generated notes still point at the old meaning. Ceiling is
   therefore taken from *any* mention of the ID in the vault — wikilink targets
   and filenames included — not just from live frontmatter.

Rule of thumb that keeps this cheap: cancel tasks (`status: Cancelled`), do not
delete them. A cancelled task stays in the archive and defends its own ID.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1] / "OBSIDIAN"
TASK_DIRS = ("02-PROJEKTY", "07-ARCHIV")
MAPPING_REL = "00-System/migration-mapping.json"
PENDING_REL = "00-System/Triage-Pending"

ID_RE = re.compile(r"^([A-Z]+)(\d+)[a-z]?$")


def _frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?\n)---", text, re.S)
    if not m:
        return {}
    try:
        import yaml

        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def prefix_for_slug(slug: str) -> str:
    """Prefix from migration-mapping.json; fall back to initials of the slug."""
    mapping_path = VAULT / MAPPING_REL
    if mapping_path.exists():
        try:
            for entry in json.loads(mapping_path.read_text(encoding="utf-8")):
                if entry.get("slug") == slug and entry.get("id_prefix"):
                    return entry["id_prefix"]
        except Exception:
            pass
    return "".join(part[0] for part in slug.split("-") if part).upper()[:3]


def ceiling_for_prefix(prefix: str) -> tuple[int, str]:
    """Highest number ever used with this prefix, and where it was seen.

    Looks at frontmatter ids, task filenames and wikilink targets, so an ID
    survives even when its file is gone.
    """
    best, where = 0, "(nic nenalezeno)"
    exact = re.compile(rf"\b{re.escape(prefix)}(\d+)\b")

    def consider(n: int, src: str) -> None:
        nonlocal best, where
        if n > best:
            best, where = n, src

    for top in TASK_DIRS:
        for path in (VAULT / top).rglob("*.md"):
            m = exact.match(path.name)
            if m:
                consider(int(m.group(1)), f"soubor {path.name}")
            tid = str(_frontmatter(path).get("id") or "")
            m = ID_RE.match(tid)
            if m and m.group(1) == prefix:
                consider(int(m.group(2)), f"frontmatter {path.name}")

    # Mentions anywhere — catches IDs whose task file was deleted. Deliberately
    # broad: skipping a number costs nothing (IDs are opaque), handing out a
    # number that still means something else costs an afternoon of link repair.
    mention_re = re.compile(rf"\b{re.escape(prefix)}(\d+)\b")
    for path in VAULT.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in mention_re.finditer(text):
            consider(int(m.group(1)), f"zmínka v {path.relative_to(VAULT)}")

    pending = VAULT / PENDING_REL
    if pending.is_dir():
        for jf in pending.glob("*.json"):
            try:
                blob = jf.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in exact.finditer(blob):
                consider(int(m.group(1)), f"pending triáž {jf.name}")

    return best, where


def next_id(slug: str) -> tuple[str, str]:
    prefix = prefix_for_slug(slug)
    ceiling, where = ceiling_for_prefix(prefix)
    return f"{prefix}{ceiling + 1}", where


def find_duplicates() -> dict[str, list[Path]]:
    """IDs claimed by more than one task file.

    Rotated rituals legitimately share an ID across archived instances
    (`<ID>-YYYY-MM-DD.md`), so at most one non-rotation file may claim it.
    """
    rotation = re.compile(r"^[A-Z]+\d+-\d{4}-\d{2}-\d{2}\.md$")
    claims: dict[str, list[Path]] = defaultdict(list)
    for top in TASK_DIRS:
        for path in (VAULT / top).rglob("*.md"):
            if "/tasks" not in str(path.parent) and "tasks-done" not in str(path.parent):
                continue
            tid = str(_frontmatter(path).get("id") or "")
            if tid:
                claims[tid].append(path)

    out = {}
    for tid, paths in claims.items():
        if len(paths) < 2:
            continue
        if sum(1 for p in paths if not rotation.match(p.name)) <= 1:
            continue  # ritual rotation, fine
        out[tid] = sorted(paths)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="project slug, e.g. finance")
    ap.add_argument("--why", action="store_true", help="show where the ceiling came from")
    ap.add_argument("--check", action="store_true", help="report duplicate IDs and exit 1 if any")
    args = ap.parse_args()

    if args.check:
        dups = find_duplicates()
        if not dups:
            print("✓ žádné duplicitní task ID")
            return 0
        print(f"✗ duplicitní task ID: {len(dups)}")
        for tid, paths in sorted(dups.items()):
            print(f"  {tid}")
            for p in paths:
                print(f"    {p.relative_to(VAULT)}")
        return 1

    if not args.slug:
        ap.error("chybí slug (nebo použij --check)")

    new_id, where = next_id(args.slug)
    print(new_id if not args.why else f"{new_id}   (strop podle: {where})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
