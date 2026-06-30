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
from triage_complexity import has_attachments_markers  # noqa: E402
from triage_commitments import purge_dropped_sent_inbox  # noqa: E402
from triage_slack_relevance import evaluate_slack_inbox_relevance, is_slack_inbox  # noqa: E402
from triage_run import iter_inbox_items, _open_pending_source_files  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    items = iter_inbox_items(vault)
    items = purge_dropped_sent_inbox(vault, items)
    pending = _open_pending_source_files(vault)
    if pending:
        items = [(r, b) for r, b in items if r not in pending]

    now = datetime.now(TZ).isoformat()
    if not items:
        print(f"inbox_inventory: empty ({now})")
        return

    print(f"inbox_inventory: {len(items)} files ({now})")
    with_attachments = 0
    for rel, body in items[:20]:
        extras: list[str] = []
        if has_attachments_markers(body):
            extras.append("attachments→DEEP")
            with_attachments += 1
        if is_slack_inbox(rel):
            rel_result = evaluate_slack_inbox_relevance(rel, body)
            if rel_result:
                extras.append(f"slack→{rel_result.route.upper()}")
        flag = f" [{', '.join(extras)}]" if extras else ""
        print(f"  - {rel}{flag}")
    if len(items) > 20:
        print(f"  ... +{len(items) - 20} more")
    if with_attachments:
        print(f"inbox_inventory: {with_attachments} with ## Přílohy (DEEP triage)")


if __name__ == "__main__":
    main()
