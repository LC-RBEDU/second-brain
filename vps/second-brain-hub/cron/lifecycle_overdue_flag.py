#!/usr/bin/env python3
"""Log an overdue task once, then escalate after two weeks of silence.

Does NOT flip status — the user decides whether to reschedule or drop the
deadline. Two log lines per deadline value, ever:

1. first breach   → `[lifecycle_overdue_flag:<deadline>]`
2. 14 days later  → `[lifecycle_overdue_escalate:<deadline>]`, which asks for a
   decision instead of repeating the same fact.

The marker carries the deadline, so moving the deadline and missing it again
produces a fresh pair of lines rather than staying silent forever.

Before the priority model v2 this appended a line every single day: ES5 collected
seventeen identical rows, AF14 thirteen, burying the real log underneath.
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
from focus import is_terminal  # noqa: E402
from overdue import (  # noqa: E402
    ESCALATE_AFTER_DAYS,
    escalation_line,
    first_breach_line,
    needs_escalation,
    needs_first_flag,
)
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
    flagged = 0
    escalated = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if is_terminal(task.status):
            continue
        dl = parse_iso_date(task.frontmatter.get("deadline"))
        if dl is None or dl >= today:
            continue

        if needs_first_flag(task.body, dl):
            log = first_breach_line(today_str, dl)
            kind = "OVERDUE"
        elif needs_escalation(task.body, dl, today):
            log = escalation_line(today_str, dl, today)
            kind = f"ESKALACE ({ESCALATE_AFTER_DAYS}+ dní)"
        else:
            continue

        if update_task(vault, task, today_str=today_str, body_append=log):
            if kind == "OVERDUE":
                flagged += 1
            else:
                escalated += 1
            print(f"  ✓ {task.rel_path} {kind} (deadline {dl.isoformat()})")
        else:
            skipped += 1

    print(
        f"lifecycle_overdue_flag: first={flagged}, escalated={escalated}, "
        f"conflicts/skipped={skipped}"
    )


if __name__ == "__main__":
    main()
