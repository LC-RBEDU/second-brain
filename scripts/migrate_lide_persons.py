#!/usr/bin/env python3
"""Migrate 05-RESOURCES/lide person profiles to F6.4 template structure (idempotent).

Usage:
  python3 scripts/migrate_lide_persons.py
  python3 scripts/migrate_lide_persons.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIDE = REPO / "OBSIDIAN" / "05-RESOURCES" / "lide"
SKIP = {"_ŠABLONA-person.md", "_index.md"}

sys.path.insert(0, str(REPO / "scripts"))
from lide_person_template import normalize_person_file  # noqa: E402
from sync_lide_people import KNOWN_META, NICKNAMES  # noqa: E402


def migrate_file(path: Path, dry_run: bool) -> bool:
    new_text = normalize_person_file(
        path,
        known_meta=KNOWN_META.get(path.stem),
        nicknames=NICKNAMES.get(path.stem),
    )
    old = path.read_text(encoding="utf-8")
    if new_text == old:
        return False
    if dry_run:
        print(f"would migrate: {path.name}")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"migrated: {path.name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not LIDE.is_dir():
        print(f"ERROR: {LIDE} missing", file=sys.stderr)
        return 1
    n = 0
    for p in sorted(LIDE.glob("*.md")):
        if p.name in SKIP:
            continue
        if migrate_file(p, args.dry_run):
            n += 1
    print(f"migrate_lide_persons: {n} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
