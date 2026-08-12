#!/usr/bin/env python3
"""Keep `## Operativní kroky` sorted in every active task.

Order: open steps first, ascending by subtask number, then completed ones the
same way. `### ` subheadings inside the section stay put and act as boundaries.

The rewrite is cosmetic, so it deliberately does NOT touch `updated:` and does
not append a log line — otherwise every reorder would look like task activity
and pollute "Poslední aktivita tasku" / recently done.

CAS-aware: skip on conflict (user is editing). Idempotent.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, credentials_from_env  # noqa: E402
from operational_steps import sort_operational_steps  # noqa: E402
from task_io import iter_active_tasks, serialize_task  # noqa: E402


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    sorted_count = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        new_body, changed = sort_operational_steps(task.body)
        if not changed:
            continue
        try:
            vault.write_text(
                task.rel_path,
                serialize_task(task.frontmatter, new_body),
                expect_mtime=task.meta.modified_time if task.meta else None,
            )
        except Exception as exc:  # noqa: BLE001 — conflict or transient API error
            skipped += 1
            print(f"  ! {task.rel_path}: {exc}")
            continue
        sorted_count += 1
        print(f"  ✓ {task.rel_path}")

    print(f"lifecycle_sort_steps: sorted={sorted_count}, conflicts/skipped={skipped}")


if __name__ == "__main__":
    main()
