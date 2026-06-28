#!/usr/bin/env python3
"""Restore vault files from 07-ARCHIV/_backups/<ts>/ (VC7).

Usage:
  python3 scripts/restore_backup.py 20260628-120000
  python3 scripts/restore_backup.py 20260628-120000 --dry-run
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import DEFAULT_VAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Backup folder name under 07-ARCHIV/_backups/")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    backup_root = args.vault / "07-ARCHIV" / "_backups" / args.timestamp
    if not backup_root.exists():
        sys.stderr.write(f"ERROR: backup not found: {backup_root}\n")
        return 1

    restored = 0
    for src in backup_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(backup_root)
        dest = args.vault / rel
        if args.dry_run:
            print(f"DRY restore {rel}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"restored {rel}")
        restored += 1
    print(f"{'would restore' if args.dry_run else 'restored'}: {restored} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
