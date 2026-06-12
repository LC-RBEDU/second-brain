#!/usr/bin/env python3
"""Minimal INBOX inventory — no proposals, just list unprocessed files on Drive."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
_CRON = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

from drive_io import DriveVault, credentials_from_env  # noqa: E402
from triage_run import iter_inbox_items, _open_pending_source_files  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    items = iter_inbox_items(vault)
    pending = _open_pending_source_files(vault)
    if pending:
        items = [(r, b) for r, b in items if r not in pending]

    now = datetime.now(TZ).isoformat()
    if not items:
        print(f"inbox_inventory: empty ({now})")
        return

    print(f"inbox_inventory: {len(items)} files ({now})")
    for rel, _ in items[:20]:
        print(f"  - {rel}")
    if len(items) > 20:
        print(f"  ... +{len(items) - 20} more")


if __name__ == "__main__":
    main()
