#!/usr/bin/env python3
"""F3 meeting_prep_dispatch — look-ahead window; --dry-run = 0 write/Grok (B37/A34)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from vault_factory import open_vault  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
CAL_PATH = "00-System/calendar-events.json"


def _window_minutes() -> int:
    raw = (os.environ.get("MEETING_PREP_WINDOW_MINUTES") or "70").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 70


def _load_events(vault) -> list[dict]:
    if not vault.exists(CAL_PATH):
        return []
    try:
        text, _ = vault.read_text(CAL_PATH)
        data = json.loads(text)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    return list(data.get("events") or data.get("items") or [])


def _parse_start(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)
    except ValueError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--brain-url", default=os.environ.get("BRAIN_PUBLIC_URL", ""))
    args = parser.parse_args()
    now = datetime.now(TZ)
    window = _window_minutes()
    horizon = now + timedelta(minutes=window)

    with open_vault() as vault:
        events = _load_events(vault)

    candidates = []
    for ev in events:
        eid = str(ev.get("id") or ev.get("event_id") or "")
        start = _parse_start(str(ev.get("start") or ev.get("starts_at") or ""))
        if not eid or not start:
            continue
        if now <= start <= horizon:
            candidates.append(
                {
                    "event_id": eid,
                    "title": ev.get("title") or ev.get("summary") or "",
                    "starts_at": start.isoformat(),
                }
            )

    print(
        f"meeting_prep_dispatch: window={window}m candidates={len(candidates)} "
        f"dry_run={args.dry_run}"
    )
    for c in candidates:
        if args.dry_run:
            print(f"  [dry] would prepare/send event_id={c['event_id']} (0 vault write, 0 Grok)")
            continue
        # Live path: call Brain prepare_meeting (service token) — optional in F3 if URL set.
        brain = (args.brain_url or "").rstrip("/")
        token = (os.environ.get("BRAIN_SERVICE_TOKEN") or "").strip()
        if not brain or not token:
            print(f"  ! skip {c['event_id']}: BRAIN_PUBLIC_URL/TOKEN missing")
            continue
        import urllib.request

        body = json.dumps(
            {
                "event_id": c["event_id"],
                "title": c["title"],
                "starts_at": c["starts_at"],
                "force": False,
                "deliver": True,
                "dry_run": False,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{brain}/v1/prepare_meeting",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                print(f"  ✓ {c['event_id']} http={resp.getcode()}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {c['event_id']}: {exc}")


if __name__ == "__main__":
    main()
