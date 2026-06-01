#!/usr/bin/env python3
"""Set default waitUntil on Waiting tasks that have no reactivation date.

When status is Waiting but waitUntil is empty, the task would never auto-flip
to ASAP (lifecycle_waiting_to_asap requires waitUntil <= today).

Default: today + 3 days (same as agenda-status-update „ztím čekat").
CAS-aware. Idempotent once waitUntil is set.

Schedule: every 2 hours at :02 (after waiting_to_asap, before waituntil_hygiene).
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
from lifecycle_promotion import (  # noqa: E402
    DEFAULT_WAIT_UNTIL_DAYS,
    default_wait_until,
    has_wait_until_value,
)
from task_io import iter_active_tasks, update_task  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date()
    today_str = today.isoformat()
    wu = default_wait_until(today)
    wu_str = wu.isoformat()
    set_count = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if task.status != "Waiting":
            continue
        if has_wait_until_value(task.frontmatter.get("waitUntil")):
            continue

        log = (
            f"- {today_str}: Set waitUntil={wu_str} "
            f"(Waiting without date; default +{DEFAULT_WAIT_UNTIL_DAYS}d). "
            f"[lifecycle_waiting_default_waituntil]\n"
        )
        ok = update_task(
            vault,
            task,
            new_frontmatter={"waitUntil": wu_str},
            today_str=today_str,
            body_append=log,
        )
        if ok:
            set_count += 1
            print(f"  ✓ {task.rel_path} waitUntil → {wu_str}")
        else:
            skipped += 1

    print(
        f"lifecycle_waiting_default_waituntil: set={set_count}, "
        f"conflicts/skipped={skipped}"
    )


if __name__ == "__main__":
    main()
