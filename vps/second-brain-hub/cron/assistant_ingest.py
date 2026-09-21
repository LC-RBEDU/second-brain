#!/usr/bin/env python3
"""Ingest INBOX every 1–2 min (08:00–24:00). Pending + drafts. Never add_task."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from assistant_ingest import (  # noqa: E402
    DRAFT_CHANNEL_ID,
    INBOX_DIRS,
    INGEST_STATE_REL,
    PENDING_REL,
    PLAYBOOK_REL,
    PLAYBOOK_TEXT,
    SEND_POLICY_REL,
    SEND_POLICY_TEXT,
    Action,
    InboxItem,
    email_pointer,
    parse_frontmatter,
    plan_actions,
    reply_address,
    set_status,
    slack_draft_payload,
    slack_pointer,
    slack_reply_target,
)
from assistant_window import in_active_window  # noqa: E402
from drive_io import DriveNotFoundError, DriveVault, credentials_from_env  # noqa: E402
from gmail_drafts import build_reply_body, create_reply_draft, credentials_from_env as gmail_creds  # noqa: E402
from reply_compose import compose_reply  # noqa: E402
from run_lock import try_lock  # noqa: E402
from slack_client import (  # noqa: E402
    SlackAPIError,
    conversation_replies,
    open_dm_channel,
    search_messages,
    send_reminder_dm,
)
from slack_poll_core import (  # noqa: E402
    LUKAS_USER_ID,
    reply_seen_key,
    select_reply_hits,
    thread_key,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
LOCK = "/tmp/second-brain-assistant-ingest.lock"


def _load_items(vault: DriveVault) -> list[InboxItem]:
    items: list[InboxItem] = []
    for folder in INBOX_DIRS:
        try:
            metas = vault.list_dir(folder, pattern="*.md", recursive=False)
        except Exception:
            continue
        for meta in metas:
            rel = meta.rel_path if hasattr(meta, "rel_path") else f"{folder}/{meta.name}"
            if "/email/sent/" not in rel and folder.endswith("/sent"):
                rel = f"{folder}/{meta.name}"
            try:
                text, _ = vault.read_text(rel)
            except Exception as exc:  # noqa: BLE001
                print(f"assistant_ingest: unreadable {rel}: {exc}")
                continue
            fm, body = parse_frontmatter(text)
            items.append(InboxItem(rel=rel, fm=fm, body=body))
    return items


def _ensure(vault: DriveVault, rel: str, text: str) -> None:
    try:
        vault.stat(rel)
    except DriveNotFoundError:
        vault.write_text(rel, text, mime_type="text/yaml" if rel.endswith(".yaml") else "text/markdown")
    except Exception:
        return


def _item_key(item: InboxItem) -> str:
    stamp = item.fm.get("slack_ts") or item.fm.get("message_id") or item.fm.get("gmail_thread_id") or ""
    return f"{item.rel}|{stamp}|{item.fm.get('status', '')}"


def _apply(vault: DriveVault, action: Action, token: str, creds, playbook: str) -> str:
    item = action.item
    if action.op == "skip":
        return "skip"
    if action.op == "handle":
        text, meta = vault.read_text(item.rel)
        vault.write_text(item.rel, set_status(text, "handled_by_user"), expect_mtime=meta.modified_time)
        return "handle"
    if action.op not in {"draft_email", "draft_slack"}:
        return "deep"
    text = compose_reply(item, playbook)
    if not text:
        raise RuntimeError(f"reply agent returned empty {item.rel}")
    stamp = datetime.now(TZ).strftime("%Y-%m-%d-%H%M")
    slug = Path(item.rel).stem[:60]
    if action.op == "draft_email":
        to = reply_address(item.fm.get("from") or "")
        if not to:
            print(f"assistant_ingest: no reply address {item.rel}")
            return "skip-no-address"
        subject = item.fm.get("subject") or "bez předmětu"
        body = build_reply_body(
            to=to,
            subject=subject,
            body=text,
            thread_id=item.fm.get("gmail_thread_id") or "",
            in_reply_to=item.fm.get("message_id") or "",
        )
        if creds is None:
            raise RuntimeError("GOOGLE_GMAIL_OAUTH_JSON missing")
        try:
            draft_id = create_reply_draft(creds, body)
        except Exception as exc:  # noqa: BLE001
            print(f"assistant_ingest: gmail draft failed {item.rel}: {exc}")
            raise
        if not draft_id:
            raise RuntimeError(f"gmail draft id empty {item.rel}")
        rel = f"01-INBOX/drafts/{stamp}-{slug}.md"
        vault.write_text(rel, email_pointer(item, text, draft_id))
        return rel
    if action.op == "draft_slack":
        target = slack_reply_target(item)
        if target is None:
            return "skip-no-target"
        channel, thread_ts = target
        permalink = ""
        for line in item.body.splitlines():
            if line.startswith("**Vlákno:**"):
                permalink = line.split("**Vlákno:**", 1)[1].strip()
                break
        draft_channel = (os.environ.get("SLACK_DRAFT_CHANNEL_ID") or DRAFT_CHANNEL_ID).strip()
        payload = slack_draft_payload(text, channel, thread_ts, permalink)
        payload["draft_channel"] = draft_channel
        _post_n8n_slack_draft(payload)
        rel = f"01-INBOX/drafts/{stamp}-{slug}.md"
        vault.write_text(rel, slack_pointer(item, text))
        return rel
    return "deep"


def _post_n8n_slack_draft(payload: dict) -> None:
    url = (os.environ.get("N8N_SLACK_REPLY_WEBHOOK") or "").strip()
    token = (os.environ.get("N8N_SLACK_REPLY_TOKEN") or "").strip()
    if not url or not token:
        raise RuntimeError("N8N_SLACK_REPLY_WEBHOOK missing")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-Reply-Token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 300:
                raise RuntimeError(f"n8n slack draft HTTP {resp.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"n8n slack draft HTTP {exc.code}") from exc


def _playbook(vault: DriveVault) -> str:
    try:
        text, _ = vault.read_text(PLAYBOOK_REL)
    except Exception:
        return PLAYBOOK_TEXT
    return text or PLAYBOOK_TEXT


def _ping(token: str, lines: list[str]) -> None:
    if not token or not lines:
        return
    text = "Hoj, INBOX:\n" + "\n".join(f"• {line}" for line in lines[:8])
    try:
        send_reminder_dm(token, text)
    except (SlackAPIError, ValueError) as exc:
        print(f"assistant_ingest: ping failed: {exc}")


def main() -> None:
    now = datetime.now(TZ)
    if not in_active_window(now):
        print(f"assistant_ingest: outside 08:00–24:00 ({now.isoformat()}) — skip")
        return
    lock = try_lock(LOCK)
    if lock is None:
        print("assistant_ingest: previous run still going — skip")
        return
    try:
        _run(now)
    finally:
        lock.close()


def _run(now: datetime) -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds_drive, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds_drive)
    _ensure(vault, SEND_POLICY_REL, SEND_POLICY_TEXT)
    _ensure(vault, PLAYBOOK_REL, PLAYBOOK_TEXT)

    try:
        raw, _ = vault.read_json(INGEST_STATE_REL)
        state = raw if isinstance(raw, dict) else {}
    except DriveNotFoundError:
        state = {}
    seen = set(state.get("seen") or [])

    items = _load_items(vault)
    if not state.get("bootstrapped"):
        keys = []
        for item in items:
            for op in ("handle", "draft_email", "draft_slack", "deep", "skip"):
                keys.append(_item_key(item) + "|" + op)
        vault.write_json(INGEST_STATE_REL, {"bootstrapped": True, "seen": keys[-4000:]})
        print(f"assistant_ingest: bootstrapped seen={len(keys)} (no backfill)")
        return
    actions = plan_actions(items)
    token = (os.environ.get("SLACK_USER_TOKEN") or "").strip()
    gcreds = gmail_creds()
    fresh: list[Action] = []
    for action in actions:
        key = _item_key(action.item) + "|" + action.op
        if key in seen and action.op != "handle":
            continue
        if action.item.fm.get("status") == "handled_by_user":
            continue
        fresh.append(action)

    ping_lines: list[str] = []
    summary = ["# Assistant inbox", "", f"updated: {now.isoformat()}", ""]
    for action in fresh:
        try:
            result = _apply(vault, action, token, gcreds, _playbook(vault))
        except Exception as exc:  # noqa: BLE001
            print(f"assistant_ingest: {action.op} {action.item.rel}: {exc}")
            continue
        seen.add(_item_key(action.item) + "|" + action.op)
        if action.op in {"draft_email", "deep"}:
            ping_lines.append(f"{action.op}: {Path(action.item.rel).name}")
        summary.append(f"- {action.op} `{action.item.rel}` ({action.reason}) → {result}")
    if fresh:
        vault.write_text(PENDING_REL, "\n".join(summary) + "\n")
        _ping(token, ping_lines)
    if token:
        _draft_live_slack(vault, token, seen, now, items)
    vault.write_json(
        INGEST_STATE_REL,
        {"bootstrapped": True, "seen": sorted(seen)[-4000:]},
    )
    print(f"assistant_ingest: actions={len(fresh)} scanned={len(items)}")


def _archived_thread_keys(items: list[InboxItem]) -> set[str]:
    keys: set[str] = set()
    for item in items:
        if "/slack/" not in item.rel:
            continue
        channel = str(item.fm.get("channel_id") or "").strip()
        thread_ts = str(item.fm.get("thread_ts") or "").strip()
        if not channel:
            found = re.search(r"archives/([A-Z0-9]+)/", item.body)
            channel = found.group(1) if found else ""
        if not thread_ts:
            found = re.search(r"\*\*Thread TS:\*\*\s*`?([0-9.]+)", item.body)
            thread_ts = found.group(1) if found else ""
        if channel and thread_ts:
            keys.add(thread_key(channel, thread_ts))
    return keys


def _draft_live_slack(
    vault: DriveVault,
    token: str,
    seen: set[str],
    now: datetime,
    items: list[InboxItem],
) -> None:
    """Reply cards for mentions and 1:1 DMs. The Later poll stays the archive."""
    grouped: dict[str, list] = {}
    for kind, query in (("mention", f"<@{LUKAS_USER_ID}>"), ("dm", "is:dm")):
        try:
            grouped[kind] = search_messages(token, query, count=100)
        except SlackAPIError as exc:
            print(f"assistant_ingest: slack search {kind}: {exc}")
            grouped[kind] = []
    hits = select_reply_hits(
        grouped,
        seen_keys=seen,
        now=now,
        exclude_channels={DRAFT_CHANNEL_ID},
        archived_keys=_archived_thread_keys(items),
    )
    playbook = _playbook(vault)
    posted: set[str] = set()
    for hit in hits:
        key = reply_seen_key(hit.channel_id, hit.thread_ts, hit.latest_ts)
        channel = hit.channel_id
        if channel.startswith("U"):
            try:
                channel = open_dm_channel(token, channel)
            except SlackAPIError as exc:
                print(f"assistant_ingest: slack dm {hit.channel_id}: {exc}")
                continue
        ident = channel + "|" + hit.thread_ts
        if ident in posted:
            seen.add(key)
            continue
        try:
            messages = conversation_replies(token, channel, hit.thread_ts)
        except SlackAPIError as exc:
            print(f"assistant_ingest: slack replies {channel}: {exc}")
            continue
        last_user = ""
        last_bot = False
        lines: list[str] = []
        for msg in messages:
            if msg.get("subtype") in {"channel_join", "channel_leave", "bot_add", "bot_message"}:
                continue
            last_user = str(msg.get("user") or "")
            last_bot = bool(msg.get("bot_id")) or not last_user
            text = str(msg.get("text") or "").strip()
            if text:
                lines.append(text)
        if not lines or last_bot or last_user == LUKAS_USER_ID:
            seen.add(key)
            continue
        item = InboxItem(
            rel=f"01-INBOX/slack/{channel}_{hit.thread_ts}.md",
            fm={"kind": hit.kind, "channel_id": channel, "thread_ts": hit.thread_ts},
            body="\n\n".join(lines[-12:]),
        )
        try:
            text = compose_reply(item, playbook)
            if not text:
                raise RuntimeError("reply agent returned empty")
            payload = slack_draft_payload(text, channel, hit.thread_ts, hit.permalink)
            _post_n8n_slack_draft(payload)
        except Exception as exc:  # noqa: BLE001
            print(f"assistant_ingest: slack reply {hit.channel_name}: {exc}")
            continue
        posted.add(ident)
        seen.add(key)
        print(f"assistant_ingest: slack reply {hit.channel_name} {hit.thread_ts}")


if __name__ == "__main__":
    main()
