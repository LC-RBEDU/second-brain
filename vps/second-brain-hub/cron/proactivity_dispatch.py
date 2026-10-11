#!/usr/bin/env python3
"""F3 proactivity — 3 windows: morning / due / evening (R11). No propose/apply."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from push_dispatch import as_dict, dispatch_proactivity  # noqa: E402
from vault_factory import open_vault  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def _trigger_for(now: datetime, explicit: str | None) -> str:
    if explicit:
        return explicit
    h = now.hour
    if h <= 9:
        return "morning"
    if h >= 17:
        return "evening"
    return "due"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--trigger",
        choices=("morning", "due", "evening"),
        default=None,
        help="Force trigger slot (default: by clock)",
    )
    args = parser.parse_args()
    now = datetime.now(TZ)
    trigger = _trigger_for(now, args.trigger)

    slack_n = 0
    with open_vault() as vault:
        try:
            metas = vault.list_dir("01-INBOX/slack", pattern="*.md", recursive=True)
            slack_n = len(list(metas))
        except Exception:
            slack_n = 0

    preview = {
        "trigger": trigger,
        "slack_dump_count": slack_n,
        "message": "jdi do live triáže",
        "propose": False,
        "batch_id": None,
    }
    print(f"proactivity_dispatch: trigger={trigger} preview={preview} dry_run={args.dry_run}")

    # F4 A16/B26: CTA = live triáž (eyes/gear); dump count není provozní signál.
    msg = f"{trigger}: jdi do live triáže (Slack live — :eyes: / :gear:)"
    result = dispatch_proactivity(msg, dry_run=args.dry_run)
    print(f"  deliver={as_dict(result)}")
    if args.dry_run:
        print("  [dry] 0 OS push, 0 Slack send, 0 chat deliver, 0 propose")
        return
    # No propose / batch_id (Q11).


if __name__ == "__main__":
    main()
