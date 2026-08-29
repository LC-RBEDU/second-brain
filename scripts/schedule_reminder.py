#!/usr/bin/env python3
"""Schedule a Slack reminder via vault queue (00-System/Reminders-Pending/)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
_LIB = REPO / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from reminders import (  # noqa: E402
    CANCELLED_DIR,
    PENDING_DIR,
    build_reminder,
    parse_deliver_at,
    slugify_filename,
)

TZ = ZoneInfo("Europe/Prague")
DEFAULT_VAULT = Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"


def vault_path() -> Path:
    import os

    return Path(os.environ.get("SECOND_BRAIN_VAULT", str(DEFAULT_VAULT)))


def cmd_schedule(args: argparse.Namespace) -> int:
    deliver = parse_deliver_at(args.at, tz=TZ)
    reminder = build_reminder(
        message=args.message,
        deliver_at=deliver,
        task_ref=args.task_ref,
        source=args.source,
    )
    pending = vault_path() / PENDING_DIR
    pending.mkdir(parents=True, exist_ok=True)
    out = pending / slugify_filename(reminder["id"])
    if out.exists():
        print(f"error: file already exists: {out}", file=sys.stderr)
        return 1
    out.write_text(json.dumps(reminder, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(reminder["id"])
    print(f"deliver_at: {reminder['deliver_at']}")
    print(f"path: {out}")
    print("Slack DM pošle cron reminders_dispatch.py (VPS, každé 2 min).")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    pending = vault_path() / PENDING_DIR
    if not pending.is_dir():
        print("(empty)")
        return 0
    files = sorted(pending.glob("*.json"))
    if not files:
        print("(empty)")
        return 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "pending":
            continue
        print(f"{data.get('id')} | {data.get('deliver_at')} | {data.get('message', '')[:80]}")
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    pending = vault_path() / PENDING_DIR
    matches = list(pending.glob(f"*{args.id}*.json"))
    if not matches:
        print(f"error: no pending reminder matching {args.id}", file=sys.stderr)
        return 1
    cancelled_dir = vault_path() / CANCELLED_DIR
    cancelled_dir.mkdir(parents=True, exist_ok=True)
    for path in matches:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "cancelled"
        data["cancelled_at"] = datetime.now(TZ).isoformat(timespec="seconds")
        dest = cancelled_dir / path.name
        dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path.unlink()
        print(f"cancelled: {data.get('id')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule Slack reminders for MrLUC cron")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("schedule", help="Create pending reminder")
    p_add.add_argument("--at", required=True, help='Deliver time, e.g. "2026-09-02 08:00" or ISO')
    p_add.add_argument("--message", required=True, help="Slack message body")
    p_add.add_argument("--task-ref", default=None, help="Optional task label (ID — title)")
    p_add.add_argument("--source", default="cursor-agent")
    p_add.set_defaults(func=cmd_schedule)

    p_list = sub.add_parser("list", help="List pending reminders")
    p_list.set_defaults(func=cmd_list)

    p_cancel = sub.add_parser("cancel", help="Cancel by reminder id substring")
    p_cancel.add_argument("id", help="Reminder id or unique substring")
    p_cancel.set_defaults(func=cmd_cancel)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
