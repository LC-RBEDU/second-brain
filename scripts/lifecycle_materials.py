#!/usr/bin/env python3
"""Archive cold materials when no task references them (VC7-8 lifecycle).

Usage:
  python3 scripts/lifecycle_materials.py --dry-run
  python3 scripts/lifecycle_materials.py --apply
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from audit_material_links import _collect_references  # noqa: E402
from build_agent_context import DEFAULT_VAULT, parse_frontmatter  # noqa: E402
from safe_write import backup_files  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        args.dry_run = True

    refs = _collect_references(args.vault)
    archived = 0
    for slug_dir in (args.vault / "02-PROJEKTY").iterdir():
        if not slug_dir.is_dir():
            continue
        mat_dir = slug_dir / "materials"
        if not mat_dir.exists():
            continue
        for md in list(mat_dir.rglob("*.md")):
            stem = md.stem
            if stem in refs or any(stem in r or r in stem for r in refs):
                continue
            dest = args.vault / "07-ARCHIV" / "materials" / slug_dir.name / md.relative_to(mat_dir)
            if args.dry_run:
                print(f"DRY archive {md.relative_to(args.vault)} → {dest.relative_to(args.vault)}")
            else:
                backup_files([md], args.vault)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(md), str(dest))
                print(f"archived {md.relative_to(args.vault)}")
            archived += 1
    print(f"{'would archive' if args.dry_run else 'archived'}: {archived}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
