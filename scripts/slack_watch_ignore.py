#!/usr/bin/env python3
"""Mark a Slack thread ignored on the VPS watchlist (stop continuous refetch).

Usage:
  python3 scripts/slack_watch_ignore.py <channel_id> <thread_ts>

For flat IM/MPIM watches use thread_ts = 0.

Requires Drive env (VAULT_DRIVE_ID + GOOGLE_DRIVE_OAUTH_JSON) like other vault scripts.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_LIB = _REPO / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveConflictError, DriveNotFoundError, DriveVault, credentials_from_env  # noqa: E402
from slack_poll_core import STATE_REL, PollState, mark_ignored, thread_key  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Ignore Slack watchlist thread")
    ap.add_argument("channel_id")
    ap.add_argument("thread_ts", help="Thread root ts, or 0 for flat IM/MPIM")
    args = ap.parse_args()

    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        print("VAULT_DRIVE_ID not set", file=sys.stderr)
        return 2

    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    expect = None
    try:
        raw, meta = vault.read_json(STATE_REL)
        state = PollState.from_json(raw if isinstance(raw, dict) else {})
        expect = meta.modified_time
    except DriveNotFoundError:
        state = PollState(bootstrapped=True)

    entry = mark_ignored(state, args.channel_id, args.thread_ts)
    key = thread_key(args.channel_id, args.thread_ts)

    for attempt in range(3):
        try:
            vault.write_json(STATE_REL, state.to_json(), expect_mtime=expect)
            break
        except DriveConflictError:
            raw, meta = vault.read_json(STATE_REL)
            state = PollState.from_json(raw if isinstance(raw, dict) else {})
            mark_ignored(state, args.channel_id, args.thread_ts)
            expect = meta.modified_time
        except DriveNotFoundError:
            vault.write_json(STATE_REL, state.to_json())
            break
    else:
        print("CAS failed after retries", file=sys.stderr)
        return 1

    print(f"ignored={key} kind={entry.kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
