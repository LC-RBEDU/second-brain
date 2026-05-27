#!/usr/bin/env python3
"""Clear waitUntil on tasks that are not in status Waiting.

Invariant: waitUntil is meaningful only while status == Waiting.
When lifecycle_waiting_to_asap flips Waiting → ASAP, waitUntil is cleared there too;
this job catches manual status edits (ASAP, Next, Done, …) that left waitUntil set.

Idempotent. CAS-aware.
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
from task_io import iter_active_tasks, parse_iso_date, update_task  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def should_clear_wait_until(status: str, wait_until_value: object) -> bool:
    """Return True if waitUntil should be removed from frontmatter."""
    if status == "Waiting":
        return False
    return parse_iso_date(wait_until_value) is not None or bool(
        wait_until_value and str(wait_until_value).strip()
    )


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today_str = datetime.now(TZ).date().isoformat()
    cleared = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        wu = task.frontmatter.get("waitUntil")
        if not should_clear_wait_until(task.status, wu):
            continue

        wu_str = wu.isoformat() if hasattr(wu, "isoformat") else str(wu)
        log = (
            f"- {today_str}: Cleared waitUntil={wu_str} "
            f"(status={task.status}, field only valid for Waiting). "
            f"[lifecycle_waituntil_hygiene]\n"
        )
        ok = update_task(
            vault,
            task,
            new_frontmatter={"waitUntil": None},
            today_str=today_str,
            body_append=log,
        )
        if ok:
            cleared += 1
            print(f"  ✓ {task.rel_path} cleared waitUntil (status={task.status})")
        else:
            skipped += 1

    print(f"lifecycle_waituntil_hygiene: cleared={cleared}, conflicts/skipped={skipped}")


if __name__ == "__main__":
    main()
