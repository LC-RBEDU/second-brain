#!/usr/bin/env python3
"""Auto-flip task status Waiting → Next when waitUntil <= today.

Scans 02-PROJEKTY/<slug>/tasks/*.md for `status: Waiting` && `waitUntil <= today`.
Patches frontmatter: status → Next, waitUntil → empty, updated → today; appends log.
CAS-aware.

A woken task returns to the queue, not to the top of it — waking up is not the
same as being a priority. Whether it belongs in this week's work is decided by
`focus`, which no cron may write.

waitUntil is only valid for status Waiting; see lifecycle_waituntil_hygiene.py for
tasks flipped manually without clearing the field.

Idempotent. Was `lifecycle_waiting_to_asap.py` before the priority model v2.
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
from focus import STATUS_NEXT, STATUS_WAITING  # noqa: E402
from task_io import iter_active_tasks, update_task, parse_iso_date  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date()
    today_str = today.isoformat()
    flipped = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if task.status != STATUS_WAITING:
            continue
        wu = parse_iso_date(task.frontmatter.get("waitUntil"))
        if wu is None or wu > today:
            continue

        log = (
            f"- {today_str}: Waiting → {STATUS_NEXT} (waitUntil={wu.isoformat()} expired, "
            f"waitUntil cleared). [lifecycle_waiting_to_next]\n"
        )
        ok = update_task(
            vault,
            task,
            new_status=STATUS_NEXT,
            new_frontmatter={"waitUntil": None},
            today_str=today_str,
            body_append=log,
        )
        if ok:
            flipped += 1
            print(f"  ✓ {task.rel_path} Waiting → {STATUS_NEXT} (waited until {wu.isoformat()})")
        else:
            skipped += 1

    print(f"lifecycle_waiting_to_next: flipped={flipped}, conflicts/skipped={skipped}")


if __name__ == "__main__":
    main()
