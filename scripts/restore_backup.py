#!/usr/bin/env python3
"""Restore vault files from OBSIDIAN_BACKUP/<ts>/ (VC7).

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
from safe_write import backup_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", help="Backup folder name under OBSIDIAN_BACKUP/")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    backup_dir = backup_root(args.vault) / args.timestamp
    if not backup_dir.exists():
        legacy = args.vault / "07-ARCHIV" / "_backups" / args.timestamp
        if legacy.exists():
            backup_dir = legacy
        else:
            sys.stderr.write(f"ERROR: backup not found: {backup_dir}\n")
            return 1

    restored = 0
    for src in backup_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(backup_dir)
        dest = args.vault / rel
        if args.dry_run:
            print(f"DRY restore {rel}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"restored {rel}")
        restored += 1
    print(f"{'would restore' if args.dry_run else 'restored'}: {restored} files from {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
