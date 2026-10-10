#!/usr/bin/env python3
"""Dispatch due reminders: Grok → Claude → Slack (F2-i / A48 / C4)."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from reminder_chat_delivery import (  # noqa: E402
    deliver_chat_chain,
    max_attempts,
    next_attempt_at,
)
from reminders import (  # noqa: E402
    CANCELLED_DIR,
    FAILED_DIR,
    PENDING_DIR,
    SENT_DIR,
    format_deliver_at,
    format_slack_text,
    is_due,
    reminder_error,
    slugify_filename,
)
from slack_client import post_message, resolve_dm_channel  # noqa: E402
from vault_factory import open_vault  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def _list_pending(vault) -> list[tuple[str, dict]]:
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


def _move_json(vault, src_rel: str, dest_dir: str, reminder_id: str) -> str:
    dest_rel = f"{dest_dir}/{slugify_filename(reminder_id)}"
    vault.mkdir_p(dest_dir)
    vault.move(src_rel, dest_rel)
    return dest_rel


def _writers_paused() -> bool:
    raw = (os.environ.get("VAULT_WRITERS_PAUSED") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def main() -> None:
    # --- 0a: short vault session — list due only ---
    due: list[tuple[str, dict]] = []
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print(
                "reminders_dispatch: vault session skipped "
                f"({getattr(vault, 'skip_reason', None)}) — 0 sends"
            )
            return
        now = datetime.now(TZ)
        for rel, reminder in _list_pending(vault):
            if is_due(reminder, now, tz=TZ):
                due.append((rel, dict(reminder)))

    if not due:
        print(f"reminders_dispatch: no due ({datetime.now(TZ).isoformat()})")
        return

    # --- 0a′: PAUSED before any HTTP (A61 / R31) ---
    if _writers_paused():
        print("reminders_dispatch: VAULT_WRITERS_PAUSED=1 — 0 HTTP, no attempt++")
        return

    # --- 0b: HTTP outside flock (Grok → Claude → Slack) ---
    slack_token = (os.environ.get("SLACK_BOT_TOKEN") or "").strip()
    dm_cache: dict[str, str] = {}
    outcomes: list[tuple[str, dict, bool, list]] = []

    for rel, reminder in due:
        ok, results = deliver_chat_chain(
            reminder,
            env=os.environ,
            slack_token=slack_token,
            format_text=format_slack_text,
            post_message=post_message,
            resolve_dm_channel=resolve_dm_channel,
            dm_channel_cache=dm_cache,
        )
        for r in results:
            tag = "ok" if r.ok else ("skip" if r.skipped else "fail")
            print(
                f"reminders_dispatch: {reminder.get('id')} {r.channel}={tag} {r.detail}"
            )
        outcomes.append((rel, reminder, ok, results))

    # --- 0c: short vault session — archive / backoff / FAILED ---
    sent = failed = moved_failed = 0
    k_max = max_attempts()
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print(
                "reminders_dispatch: vault skipped on archive pass — "
                "delivery may retry (at-least-once)"
            )
            return
        now = datetime.now(TZ)
        vault.mkdir_p(SENT_DIR)
        vault.mkdir_p(FAILED_DIR)
        vault.mkdir_p(CANCELLED_DIR)

        for rel, reminder, ok, results in outcomes:
            rid = str(reminder.get("id") or Path(rel).stem)
            if ok:
                reminder["status"] = "sent"
                reminder["sent_at"] = format_deliver_at(now, tz=TZ)
                reminder["delivery_channel"] = next(
                    (r.channel for r in results if r.ok), "unknown"
                )
                dest = _move_json(vault, rel, SENT_DIR, rid)
                vault.write_json(dest, reminder)
                sent += 1
                continue

            # all-fail — stay pending + backoff (A51); after K → Failed
            attempts = int(reminder.get("attempt_count") or 0) + 1
            reminder["attempt_count"] = attempts
            err_parts = [
                f"{r.channel}:{r.detail}" for r in results if not r.ok
            ]
            reminder["last_error"] = "; ".join(err_parts) or "all channels failed"
            reminder["error"] = reminder["last_error"]  # dual-write for legacy readers
            reminder["failed_at"] = format_deliver_at(now, tz=TZ)

            if attempts >= k_max:
                reminder["status"] = "failed"
                dest = _move_json(vault, rel, FAILED_DIR, rid)
                vault.write_json(dest, reminder)
                moved_failed += 1
                print(f"reminders_dispatch: {rid} → FAILED_DIR after {attempts} attempts")
            else:
                reminder["status"] = "pending"
                reminder["next_attempt_at"] = next_attempt_at(now, attempts, TZ)
                try:
                    meta = vault.stat(rel)
                    vault.write_json(rel, reminder, expect_mtime=meta.modified_time)
                except Exception:  # noqa: BLE001
                    vault.write_json(rel, reminder)
                failed += 1
                print(
                    f"reminders_dispatch: {rid} backoff attempt={attempts} "
                    f"next={reminder['next_attempt_at']} err={reminder_error(reminder)}"
                )

    print(
        f"reminders_dispatch: done sent={sent} backoff={failed} "
        f"failed_dir={moved_failed} due={len(due)}"
    )


if __name__ == "__main__":
    main()
