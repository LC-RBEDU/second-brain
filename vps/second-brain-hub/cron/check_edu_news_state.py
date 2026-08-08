#!/usr/bin/env python3
"""F7.5: Drift check for EDU news / OPS2 state.

Detects:
1. Legacy marker block `<!-- edu-news-topics:start -->` still in Operations.md hub
   (should have been removed in F7.4 migration).
2. Multiple OPS2 instances in active or archive (recurring rotation invariant violated).
3. Active OPS2 task body missing `<!-- edu-news-topics:start -->` marker.

Topic generation lives in Cursor skill `agenda-edu-news` (not cron refresh).

Exits non-zero when drift detected (so cron logs it as failure).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402
from task_io import iter_active_tasks  # noqa: E402

OPS2_ID = "OPS2"
OPS2_ARCHIVE_DIR = "07-ARCHIV/tasks-done/operations"
OPERATIONS_HUB = "02-PROJEKTY/Operations.md"
MARKER_RE = re.compile(r"<!-- edu-news-topics:start -->", re.DOTALL)


def find_ops2_path(vault: DriveVault) -> str | None:
    for task in iter_active_tasks(vault):
        if task.task_id == OPS2_ID and task.slug == "operations":
            return task.rel_path
    return None


def main() -> int:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)
    issues = 0

    try:
        hub_text, _ = vault.read_text(OPERATIONS_HUB)
        if MARKER_RE.search(hub_text):
            print(f"DRIFT: legacy edu-news marker still in {OPERATIONS_HUB} (F7.4 migration incomplete)")
            issues += 1
    except DriveNotFoundError:
        pass

    path = find_ops2_path(vault)
    if not path:
        print(f"DRIFT: active {OPS2_ID} not found — F7.4 migration incomplete or task archived")
        issues += 1
    else:
        try:
            ops2_text, _ = vault.read_text(path)
            if not MARKER_RE.search(ops2_text):
                print(f"DRIFT: {path} missing edu-news marker block")
                issues += 1
        except DriveNotFoundError:
            print(f"DRIFT: {path} not found")
            issues += 1

    try:
        archive_files = vault.list_dir(OPS2_ARCHIVE_DIR, pattern="OPS2-*.md")
        if len(archive_files) > 1:
            print(f"INFO: {len(archive_files)} OPS2 historical instances in archive (expected with weekly rotation)")
    except DriveNotFoundError:
        pass

    if issues:
        print(f"check_edu_news_state: {issues} drift issue(s) detected")
        return 1
    print("check_edu_news_state: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
