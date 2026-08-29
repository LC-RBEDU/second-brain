#!/usr/bin/env python3
"""Dispatch due Slack reminders from 00-System/Reminders-Pending/."""
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
from reminders import (  # noqa: E402
    CANCELLED_DIR,
    PENDING_DIR,
    SENT_DIR,
    format_deliver_at,
    format_slack_text,
    is_due,
    slugify_filename,
)
from slack_client import SlackAPIError, post_message, resolve_dm_channel  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def _list_pending(vault: DriveVault) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    try:
        metas = vault.list_dir(PENDING_DIR, pattern="*.json", recursive=False)
    except Exception:
        return out
    for meta in metas:
        rel = meta.rel_path
        if not rel.endswith(".json"):
            continue
        try:
            data, _ = vault.read_json(rel)
        except Exception as exc:  # noqa: BLE001
            print(f"reminders_dispatch: skip unreadable {rel}: {exc}")
            continue
        if isinstance(data, dict):
            out.append((rel, data))
    out.sort(key=lambda x: x[1].get("deliver_at") or "")
    return out


def _move_json(vault: DriveVault, src_rel: str, dest_dir: str, reminder_id: str) -> str:
    dest_rel = f"{dest_dir}/{slugify_filename(reminder_id)}"
    vault.mkdir(dest_dir)
    vault.move(src_rel, dest_rel)
    return dest_rel


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    token = (os.environ.get("SLACK_BOT_TOKEN") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    if not token:
        print("reminders_dispatch: SLACK_BOT_TOKEN not set — skip")
        return

    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)
    now = datetime.now(TZ)
    pending = _list_pending(vault)
    if not pending:
        print(f"reminders_dispatch: no pending ({now.isoformat()})")
        return

    dm_channel: str | None = None
    sent = failed = skipped = 0

    for rel, reminder in pending:
        if not is_due(reminder, now, tz=TZ):
            skipped += 1
            continue

        rid = str(reminder.get("id") or Path(rel).stem)
        target = reminder.get("target") or {"type": "dm"}
        text = format_slack_text(reminder)

        try:
            if target.get("type") == "channel":
                channel = (target.get("channel_id") or "").strip()
                if not channel:
                    raise ValueError("channel target missing channel_id")
            else:
                if dm_channel is None:
                    dm_channel = resolve_dm_channel(token)
                channel = dm_channel
            ts = post_message(token, channel, text)
            reminder["status"] = "sent"
            reminder["sent_at"] = format_deliver_at(now, tz=TZ)
            reminder["slack_ts"] = ts
            dest = _move_json(vault, rel, SENT_DIR, rid)
            vault.write_json(dest, reminder)
            sent += 1
            print(f"reminders_dispatch: sent {rid} → Slack ts={ts}")
        except (SlackAPIError, ValueError) as exc:
            reminder["status"] = "failed"
            reminder["failed_at"] = format_deliver_at(now, tz=TZ)
            reminder["error"] = str(exc)
            try:
                meta = vault.stat(rel)
                vault.write_json(rel, reminder, expect_mtime=meta.modified_time)
            except Exception:  # noqa: BLE001
                vault.write_json(rel, reminder)
            failed += 1
            print(f"reminders_dispatch: failed {rid}: {exc}")

    print(
        f"reminders_dispatch: done sent={sent} failed={failed} "
        f"skipped_not_due={skipped} pending_total={len(pending)}"
    )


if __name__ == "__main__":
    main()
