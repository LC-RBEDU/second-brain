#!/usr/bin/env python3
"""Promote highest-scoring Next tasks to ASAP when fewer than 3 open ASAP tasks.

Keeps dashboard TOP 3 (All-tasks.base#TopPrioDnes) populated during work hours.
Sort key: today_score (ICE + deadline urgency), same as Bases formula.

Only promotes from status Next; clears waitUntil on promotion.
CAS-aware. Idempotent when ASAP count already >= 3.

Schedule: hourly 10:00–23:00 and 00:00–02:00 (Europe/Prague).
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
    TARGET_ASAP_COUNT,
    select_next_for_asap_promotion,
    task_today_score,
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

    tasks = list(iter_active_tasks(vault))
    asap_tasks = [t for t in tasks if t.status == "ASAP"]
    next_tasks = [t for t in tasks if t.status == "Next"]

    to_promote = select_next_for_asap_promotion(
        next_tasks,
        today=today,
        current_asap_count=len(asap_tasks),
        target_asap=TARGET_ASAP_COUNT,
    )

    promoted = 0
    skipped = 0

    if not to_promote:
        print(
            f"lifecycle_asap_backfill: asap={len(asap_tasks)} "
            f"(target>={TARGET_ASAP_COUNT}), promoted=0"
        )
        return

    for task in to_promote:
        ts = task_today_score(task.frontmatter, today)
        log = (
            f"- {today_str}: Next → ASAP (backfill TOP {TARGET_ASAP_COUNT}; "
            f"today_score={ts}). [lifecycle_asap_backfill]\n"
        )
        ok = update_task(
            vault,
            task,
            new_status="ASAP",
            new_frontmatter={"waitUntil": None},
            today_str=today_str,
            body_append=log,
        )
        if ok:
            promoted += 1
            print(
                f"  ✓ {task.rel_path} Next → ASAP "
                f"(today_score={ts}, asap was {len(asap_tasks)}/{TARGET_ASAP_COUNT})"
            )
        else:
            skipped += 1

    print(
        f"lifecycle_asap_backfill: asap_before={len(asap_tasks)}, "
        f"promoted={promoted}, conflicts/skipped={skipped}"
    )


if __name__ == "__main__":
    main()
