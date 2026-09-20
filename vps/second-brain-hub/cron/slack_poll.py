#!/usr/bin/env python3
"""Poll Slack mentions, Later (is:saved) and DMs into 01-INBOX/slack/.

Writes the whole thread, not the tagging line. First run sets a watermark
and does not backfill. Active 08:00–24:00 Europe/Prague.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from assistant_window import in_active_window  # noqa: E402
from drive_io import DriveNotFoundError, DriveVault, credentials_from_env  # noqa: E402
from run_lock import try_lock  # noqa: E402
from slack_client import (  # noqa: E402
    SlackAPIError,
    conversation_replies,
    download_private_file,
    search_messages,
    user_display_name,
)
from slack_poll_core import (  # noqa: E402
    INBOX_DIR,
    LUKAS_USER_ID,
    STATE_REL,
    PollState,
    advance_seen,
    bootstrap_state,
    format_thread_markdown,
    inbox_filename,
    select_threads,
    thread_key,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
LOCK = "/tmp/second-brain-slack-poll.lock"


def _queries(user_id: str) -> list[tuple[str, str]]:
    return [
        ("mention", f"<@{user_id}>"),
        ("saved_later", "is:saved"),
        ("dm", "is:dm"),
        ("gdm", "is:mpim"),
    ]


def _save_attachments(token: str, vault: DriveVault, messages: list[dict], stem: str) -> list[str]:
    lines: list[str] = []
    n = 0
    for msg in messages:
        for file in msg.get("files") or []:
            name = str(file.get("name") or "attachment")
            url = str(file.get("url_private_download") or file.get("url_private") or "")
            permalink = str(file.get("permalink") or url)
            if not url:
                if permalink:
                    lines.append(f"- [{name}]({permalink})")
                continue
            n += 1
            safe = name.replace("/", "-")
            rel = f"{INBOX_DIR}/{stem}__{n}-{safe}"
            try:
                data = download_private_file(token, url)
                meta = vault.write_bytes(rel, data, mime_type=str(file.get("mimetype") or "application/octet-stream"))
                link = f"https://drive.google.com/file/d/{meta.id}/view"
                lines.append(f"- [{name}]({link})")
            except (SlackAPIError, OSError) as exc:
                print(f"slack_poll: attachment skip {name}: {exc}")
                if permalink:
                    lines.append(f"- [{name}]({permalink})")
    return lines


def main() -> None:
    now = datetime.now(TZ)
    if not in_active_window(now):
        print(f"slack_poll: outside 08:00–24:00 ({now.isoformat()}) — skip")
        return
    lock = try_lock(LOCK)
    if lock is None:
        print("slack_poll: previous run still going — skip")
        return
    try:
        _run(now)
    finally:
        lock.close()


def _run(now: datetime) -> None:
    token = (os.environ.get("SLACK_USER_TOKEN") or "").strip()
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not token:
        print("slack_poll: SLACK_USER_TOKEN not set — skip")
        return
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")

    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)
    try:
        raw, _ = vault.read_json(STATE_REL)
        state = PollState.from_json(raw if isinstance(raw, dict) else {})
    except DriveNotFoundError:
        state = PollState()

    if not state.bootstrapped:
        state = bootstrap_state(now)
        vault.write_json(STATE_REL, state.to_json())
        print(f"slack_poll: bootstrapped watermark={state.watermark_ts} (no backfill)")
        return

    user_id = (os.environ.get("SLACK_LUKAS_USER_ID") or LUKAS_USER_ID).strip()
    grouped: dict[str, list] = {}
    for kind, query in _queries(user_id):
        try:
            grouped[kind] = search_messages(token, query, count=20)
        except SlackAPIError as exc:
            print(f"slack_poll: search {kind} failed: {exc}")
            grouped[kind] = []

    hits = select_threads(grouped, state, now=now)
    if not hits:
        print(f"slack_poll: no new threads ({now.isoformat()})")
        return

    written = 0
    for hit in hits:
        try:
            messages = conversation_replies(token, hit.channel_id, hit.thread_ts)
        except SlackAPIError as exc:
            print(f"slack_poll: replies {thread_key(hit.channel_id, hit.thread_ts)}: {exc}")
            continue
        if not messages:
            messages = [{"ts": hit.latest_ts, "text": "", "user": ""}]
        for msg in messages:
            uid = str(msg.get("user") or "")
            if uid and uid not in state.names:
                try:
                    state.names[uid] = user_display_name(token, uid, state.names)
                except SlackAPIError:
                    state.names[uid] = uid
        when = datetime.fromtimestamp(float(hit.thread_ts), tz=timezone.utc).astimezone(TZ)
        filename = inbox_filename(when, hit.channel_name, hit.thread_ts)
        rel = f"{INBOX_DIR}/{filename}"
        prev = state.seen.get(thread_key(hit.channel_id, hit.thread_ts)) or {}
        if prev.get("rel"):
            rel = prev["rel"]
        stem = Path(rel).stem
        attachments = _save_attachments(token, vault, messages, stem)
        md = format_thread_markdown(hit, messages, state.names, tz=TZ, attachment_lines=attachments)
        expect = None
        try:
            expect = vault.stat(rel).modified_time
        except DriveNotFoundError:
            expect = None
        except Exception:
            expect = None
        try:
            vault.write_text(rel, md, expect_mtime=expect)
        except Exception as exc:  # noqa: BLE001
            print(f"slack_poll: write {rel} failed ({exc}); retry without CAS")
            vault.write_text(rel, md)
        advance_seen(state, hit, rel)
        vault.write_json(STATE_REL, state.to_json())
        written += 1
        print(f"slack_poll: wrote {rel} kind={hit.kind}")
    print(f"slack_poll: done written={written}")


if __name__ == "__main__":
    main()
