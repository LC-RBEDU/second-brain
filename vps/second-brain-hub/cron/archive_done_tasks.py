#!/usr/bin/env python3
"""F6.4: Archive Done tasks from 02-PROJEKTY/<slug>/tasks/ → 07-ARCHIV/tasks-done/<slug>/.

For each `status: Done` or `status: Cancelled` task .md:
1. Move file from `02-PROJEKTY/<slug>/tasks/<filename>` to `07-ARCHIV/tasks-done/<slug>/<filename>`
2. Skip if archive target already exists (idempotent)

Recurring tasks: SKIP archiving (lifecycle_recurring.py handles them — creates next instance).

Defaults: archive Done tasks immediately. Override grace period via --keep-days N
(don't archive if updated within N days — useful for "stay visible briefly" behavior).

After archive, hub `open_tasks_count` is NOT auto-updated — hub frontmatter is best-effort
and Bases dashboard counts tasks dynamically anyway.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402
from task_io import iter_active_tasks, parse_iso_date, ARCHIV_DIR  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-days",
        type=int,
        default=0,
        help="Skip closed tasks updated within N days (default 0 = archive immediately)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date()
    cutoff = today - timedelta(days=args.keep_days) if args.keep_days else today
    archived = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if not task.is_terminal:
            continue
        # Skip recurring tasks (they're rotated by lifecycle_recurring, not archived here)
        if task.frontmatter.get("recurring"):
            continue
        # Grace period
        if args.keep_days:
            updated = parse_iso_date(task.frontmatter.get("updated"))
            if updated and updated > cutoff:
                continue

        slug = task.slug or "unknown"
        filename = task.rel_path.rsplit("/", 1)[-1]
        target = f"{ARCHIV_DIR}/{slug}/{filename}"

        # Skip if target already exists
        try:
            existing = vault.stat(target)
            if existing:
                print(f"  - skip (target exists): {target}")
                skipped += 1
                continue
        except DriveNotFoundError:
            pass

        if args.dry_run:
            print(f"  [dry] {task.rel_path} → {target}")
        else:
            vault.mkdir_p(f"{ARCHIV_DIR}/{slug}")
            try:
                vault.move(task.rel_path, target)
                print(f"  ✓ {task.rel_path} → {target}")
                archived += 1
            except Exception as e:
                print(f"  ! move failed: {task.rel_path} → {target}: {e}")
                skipped += 1

    print(f"archive_done_tasks: archived={archived}, skipped={skipped}, dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
