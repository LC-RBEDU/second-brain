#!/usr/bin/env python3
"""F6.1: Auto-flip task status → Done when all checkboxes are [x].

Scans 02-PROJEKTY/<slug>/tasks/*.md, parses frontmatter + body, finds tasks where:
- status not in (Done, Cancelled) — a cancelled task stays cancelled even
  when its checkboxes are all ticked
- body has ≥1 checkbox in `## Operativní kroky` and all are checked

Patches frontmatter status: Done + updated: today, appends log line.
CAS-aware: skip on conflict (user is editing).

Idempotent — re-running does not double-flip.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, credentials_from_env  # noqa: E402
from task_io import iter_active_tasks, update_task, all_checkboxes_done  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date().isoformat()
    flipped = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if task.is_terminal:
            continue
        if not all_checkboxes_done(task.body):
            continue

        log = f"- {today}: Done — auto (všechny operativní kroky [x]). [lifecycle_done_from_checkboxes]\n"
        ok = update_task(
            vault,
            task,
            new_status="Done",
            today_str=today,
            body_append=log,
        )
        if ok:
            flipped += 1
            print(f"  ✓ {task.rel_path} → Done")
        else:
            skipped += 1

    print(f"lifecycle_done_from_checkboxes: flipped={flipped}, conflicts/skipped={skipped}")


if __name__ == "__main__":
    main()
