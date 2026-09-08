#!/usr/bin/env python3
"""Rewrite epic/story IDs so the level is visible in the code itself.

    python3 scripts/migrate_hierarchy_ids.py            # dry run
    python3 scripts/migrate_hierarchy_ids.py --apply    # rename + rewrite

`RBU69` becomes `RBU-E69` and `RBU70` becomes `RBU-S70`: project prefix stays
readable, level is unambiguous, and the number is untouched. Keeping one counter
across levels is deliberate — promoting a story to an epic changes a letter and
never frees a number for reuse, which is how duplicate IDs happened before.

Only IDs of live entities in hierarchical projects are rewritten. Every mention
of them is rewritten everywhere, archive included, or the links would break.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VAULT = REPO / "OBSIDIAN"
HIER_SLUGS = ("rb-universe-development", "finance", "firemni-procesy", "vibe-coding")
LEVEL_LETTER = {"epic": "E", "story": "S", "task": "T"}
SCAN_ROOTS = ("OBSIDIAN", "ŠABLONY", "scripts", "vps", ".cursor")
SCAN_SUFFIXES = {".md", ".base", ".json", ".py", ".mdc", ".js", ".yaml", ".yml"}
# Third-party code shares the token space: pygments' shell lexer lists F19, F26
# and F33 as function keys, and a blind rewrite would corrupt the library.
EXCLUDE_DIR_PARTS = (".venv", "site-packages", "node_modules", ".git")
# One-shot migration scripts are a record of what was done under the old scheme.
# Rewriting IDs in them would make that record describe something that never ran.
EXCLUDE_NAMES = {
    "migrate_hierarchy_ids.py",
    "migrate_rbu_hierarchy.py",
    "migrate_task_ids.py",
    "_apply_hygiene_cleanup.py",
    "_audit_task_hygiene.py",
    "finalize_migration_hygiene.py",
}
ID_RE = re.compile(r"^([A-Z]+)(\d+)$")


def frontmatter(path: Path) -> dict:
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


def build_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for slug in HIER_SLUGS:
        for f in sorted((VAULT / "02-PROJEKTY" / slug / "tasks").glob("*.md")):
            fm = frontmatter(f)
            old = str(fm.get("id") or "")
            m = ID_RE.match(old)
            if not m:
                continue
            letter = LEVEL_LETTER.get(fm.get("type") or "task")
            if not letter:
                continue
            mapping[old] = f"{m.group(1)}-{letter}{m.group(2)}"
    return mapping


def scan_files() -> list[Path]:
    out: list[Path] = []
    for root in SCAN_ROOTS:
        base = REPO / root
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if f.name in EXCLUDE_NAMES:
                continue
            if any(part in EXCLUDE_DIR_PARTS for part in f.parts):
                continue
            out.append(f)
    return out


def make_pattern(mapping: dict[str, str]) -> re.Pattern:
    # longest first so RBU7 never eats the prefix of RBU70
    keys = sorted(mapping, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(map(re.escape, keys)) + r")\b")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    mapping = build_mapping()
    if not mapping:
        print("Nenašel jsem žádné epic/story ID k migraci.", file=sys.stderr)
        return 1
    pat = make_pattern(mapping)

    touched: list[tuple[Path, int]] = []
    total = 0
    for f in scan_files():
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, n = pat.subn(lambda m: mapping[m.group(1)], text)
        if n:
            total += n
            touched.append((f, n))
            if args.apply:
                f.write_text(new, encoding="utf-8")

    renames: list[tuple[Path, Path]] = []
    for slug in HIER_SLUGS:
        for f in sorted((VAULT / "02-PROJEKTY" / slug / "tasks").glob("*.md")):
            m = re.match(r"^([A-Z]+\d+)(\s+—\s+.*)$", f.stem)
            if m and m.group(1) in mapping:
                renames.append((f, f.with_name(mapping[m.group(1)] + m.group(2) + ".md")))

    print(f"entit k přejmenování: {len(mapping)}")
    print(f"výskytů k přepsání:   {total} v {len(touched)} souborech")
    print(f"souborů k přejmenování: {len(renames)}")
    if args.apply:
        for src, dst in renames:
            src.rename(dst)
        mapfile = REPO / "OBSIDIAN/00-System/hierarchy-id-migration.json"
        mapfile.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"hotovo — mapping uložen do {mapfile.relative_to(REPO)}")
    else:
        print("\n(dry run — nic se nezměnilo)")
        for old, new in list(mapping.items())[:8]:
            print(f"   {old:8s} → {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
