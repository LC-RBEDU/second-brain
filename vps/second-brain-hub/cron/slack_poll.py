#!/usr/bin/env python3
"""Poll Slack into 01-INBOX/slack/ with a persistent watchlist.

Discover (no on:date): to:/from: Lukáš in IM/MPIM, @mentions, is:saved.
Refetch non-ignored watches; write Cowork-compatible _vN dumps.
Stop watching only when triage marks ignored (scripts/slack_watch_ignore.py).
Archive/ZPRACOVÁNO does not clear the watch. Active 08:00–24:00 Europe/Prague.

Prereq: pause Cowork Slack archive schedules 3.3 + 3.4 (dual-writer).
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
from drive_io import DriveConflictError, DriveNotFoundError, DriveVault, credentials_from_env  # noqa: E402
from run_lock import try_lock  # noqa: E402
from slack_client import (  # noqa: E402
    SlackAPIError,
    conversation_history,
    conversation_replies,
    download_private_file,
    search_messages,
    user_display_name,
)
from slack_poll_core import (  # noqa: E402
    FLAT_THREAD_TS,
    INBOX_DIR,
    LUKAS_USER_ID,
    MAX_REFETCH_PER_TICK,
    STATE_REL,
    PollState,
    ThreadHit,
    WatchEntry,
    advance_watch,
    bootstrap_state,
    discover_hits,
    enroll_watch,
    format_thread_markdown,
    inbox_filename_vN,
    max_version_from_names,
    merge_channel_history_with_replies,
    newest_ts,
    next_version,
    parse_watch_key,
    select_watch_batch,
    should_refetch,
    thread_key,
    ts_float,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
LOCK = "/tmp/second-brain-slack-poll.lock"
CAS_RETRIES = 3


def _discover_queries() -> list[tuple[str, str]]:
    uid = LUKAS_USER_ID
    # is:im / is:mpim return empty in this workspace — use to:/from: + channel flags.
    return [
        ("to_me", f"to:<@{uid}>"),
        ("from_me", f"from:<@{uid}>"),
        ("mention", f"<@{uid}> -from:<@{uid}>"),
        ("saved_later", "is:saved"),
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
            safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-.")[:80] or "attachment"
            rel = f"{INBOX_DIR}/{stem}__{n}-{safe}"
            try:
                data = download_private_file(token, url)
                meta = vault.write_bytes(
                    rel, data, mime_type=str(file.get("mimetype") or "application/octet-stream")
                )
                link = f"https://drive.google.com/file/d/{meta.id}/view"
                lines.append(f"- [{name}]({link})")
            except Exception as exc:  # noqa: BLE001 — Drive HttpError must not abort the poll
                print(f"slack_poll: attachment skip {name} ({rel}): {exc}")
                if permalink:
                    lines.append(f"- [{name}]({permalink})")
    return lines


def _fill_names(token: str, state: PollState, messages: list[dict]) -> None:
    for msg in messages:
        uid = str(msg.get("user") or "")
        if uid and uid not in state.names:
            try:
                state.names[uid] = user_display_name(token, uid, state.names)
            except SlackAPIError:
                state.names[uid] = uid


def _seed_latest(token: str, hit: ThreadHit) -> str:
    """limit=1 seed — never wall-clock now."""
    try:
        if hit.thread_ts == FLAT_THREAD_TS:
            msgs = conversation_history(token, hit.channel_id, limit=1)
        else:
            msgs = conversation_replies(token, hit.channel_id, hit.thread_ts, limit=1)
    except SlackAPIError as exc:
        print(f"slack_poll: seed {thread_key(hit.channel_id, hit.thread_ts)}: {exc}")
        return hit.latest_ts
    return newest_ts(msgs) or hit.latest_ts


def _fetch_watch_messages(
    token: str,
    channel_id: str,
    thread_ts: str,
    *,
    oldest: str = "",
    budget: list[int],
) -> list[dict]:
    """Fetch messages; each Slack API call decrements shared budget[0]."""
    if budget[0] <= 0:
        return []
    if thread_ts == FLAT_THREAD_TS:
        history = conversation_history(token, channel_id, limit=100, oldest=oldest)
        budget[0] -= 1
        replies_by_parent: dict[str, list[dict]] = {}
        # Cap nested reply expansion so one busy DM cannot burn the whole tick (P).
        max_reply_fetches = min(5, budget[0])
        fetched = 0
        for msg in history:
            if fetched >= max_reply_fetches or budget[0] <= 0:
                break
            parent = str(msg.get("ts") or "")
            reply_count = int(msg.get("reply_count") or 0)
            if not parent or reply_count <= 0:
                continue
            try:
                replies_by_parent[parent] = conversation_replies(
                    token, channel_id, parent, limit=100
                )
                budget[0] -= 1
                fetched += 1
            except SlackAPIError as exc:
                print(f"slack_poll: replies {channel_id}:{parent}: {exc}")
        return merge_channel_history_with_replies(history, replies_by_parent)
    msgs = conversation_replies(
        token, channel_id, thread_ts, limit=100, oldest=oldest
    )
    budget[0] -= 1
    return msgs


def _scan_max_v(vault: DriveVault, channel_id: str, thread_ts: str, entry: WatchEntry) -> int:
    if entry.max_v > 0:
        return entry.max_v
    names: list[str] = []
    try:
        for meta in vault.list_dir(INBOX_DIR, pattern="*.md", recursive=False):
            names.append(meta.name)
    except Exception as exc:  # noqa: BLE001
        print(f"slack_poll: list INBOX skip: {exc}")
    # Prefer cache miss only — light archive scan by year/month would be heavy; use rel basename hint
    if entry.rel:
        names.append(Path(entry.rel).name)
    return max_version_from_names(names, channel_id, thread_ts)


def _write_state(vault: DriveVault, state: PollState, expect_mtime) -> object:
    last_exc: Exception | None = None
    mtime = expect_mtime
    for attempt in range(CAS_RETRIES):
        try:
            meta = vault.write_json(STATE_REL, state.to_json(), expect_mtime=mtime)
            return meta.modified_time
        except DriveConflictError as exc:
            last_exc = exc
            print(f"slack_poll: state CAS conflict attempt {attempt + 1}: {exc}")
            try:
                raw, meta = vault.read_json(STATE_REL)
                remote = PollState.from_json(raw if isinstance(raw, dict) else {})
                for key, entry in remote.watch.items():
                    ours = state.watch.get(key)
                    if ours is None:
                        state.watch[key] = entry
                        continue
                    if entry.ignored:
                        ours.ignored = True
                    if ts_float(entry.latest_ts) > ts_float(ours.latest_ts):
                        ours.latest_ts = entry.latest_ts
                    if ts_float(entry.boost_ts or "0") > ts_float(ours.boost_ts or "0"):
                        ours.boost_ts = entry.boost_ts
                    ours.max_v = max(ours.max_v, entry.max_v)
                    # Prefer whichever side has a dump path; keep newer max_v's rel
                    if entry.rel and (not ours.rel or entry.max_v >= ours.max_v):
                        ours.rel = entry.rel
                for uid, name in remote.names.items():
                    state.names.setdefault(uid, name)
                if remote.bootstrapped:
                    state.bootstrapped = True
                mtime = meta.modified_time
            except DriveNotFoundError:
                mtime = None
        except DriveNotFoundError:
            meta = vault.write_json(STATE_REL, state.to_json())
            return meta.modified_time
    # Last resort: force write without CAS so empty-rel progress is not lost forever.
    print(f"slack_poll: state CAS exhausted ({last_exc}); force write")
    meta = vault.write_json(STATE_REL, state.to_json())
    return meta.modified_time


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
    state_mtime = None
    try:
        raw, meta = vault.read_json(STATE_REL)
        state = PollState.from_json(raw if isinstance(raw, dict) else {})
        state_mtime = meta.modified_time
    except DriveNotFoundError:
        state = PollState()

    if not state.bootstrapped:
        state = bootstrap_state(now)
        state_mtime = _write_state(vault, state, None)
        print(f"slack_poll: bootstrapped watermark={state.watermark_ts} (no backfill)")
        return

    # --- Discover + enroll ---
    grouped: dict[str, list] = {}
    for kind, query in _discover_queries():
        try:
            grouped[kind] = search_messages(token, query, count=100, max_pages=3)
        except SlackAPIError as exc:
            print(f"slack_poll: search {kind} failed: {exc}")
            grouped[kind] = []

    hits = discover_hits(grouped)
    enrolled = 0
    for hit in hits:
        key = thread_key(hit.channel_id, hit.thread_ts)
        if key in state.watch and state.watch[key].ignored:
            continue
        is_new = key not in state.watch
        seed = _seed_latest(token, hit) if is_new else state.watch[key].latest_ts
        enroll_watch(state, hit, seed_latest_ts=seed, reason=hit.kind)
        if is_new:
            enrolled += 1

    # --- Refetch watches ---
    written = 0
    budget = [MAX_REFETCH_PER_TICK]
    for key in select_watch_batch(state, limit=MAX_REFETCH_PER_TICK):
        if budget[0] <= 0:
            break
        entry = state.watch[key]
        channel_id, thread_ts = parse_watch_key(key)
        oldest = ""
        if (
            thread_ts != FLAT_THREAD_TS
            and entry.rel
            and ts_float(entry.latest_ts) > 0
        ):
            # Thread replies API: oldest is safe. Flat :0 history+replies must
            # still see reply_count bumps on older parents — no oldest filter.
            oldest = entry.latest_ts
        try:
            messages = _fetch_watch_messages(
                token, channel_id, thread_ts, oldest=oldest, budget=budget
            )
        except SlackAPIError as exc:
            print(f"slack_poll: fetch {key}: {exc}")
            continue
        if not messages:
            continue
        newest = newest_ts(messages)
        # First capture (no rel yet) OR newer than seed/latest — archive must not block.
        if entry.rel and not should_refetch(entry, newest):
            continue
        _fill_names(token, state, messages)
        scanned = _scan_max_v(vault, channel_id, thread_ts, entry)
        version = next_version(entry, scanned)
        when = datetime.fromtimestamp(float(newest), tz=timezone.utc).astimezone(TZ)
        filename = inbox_filename_vN(when, entry.channel_name or channel_id, thread_ts, version)
        rel = f"{INBOX_DIR}/{filename}"
        hit = ThreadHit(
            channel_id=channel_id,
            channel_name=entry.channel_name or channel_id,
            thread_ts=thread_ts,
            latest_ts=newest,
            kind=entry.kind,
            permalink=entry.permalink,
        )
        stem = Path(rel).stem
        attachments = _save_attachments(token, vault, messages, stem)
        md = format_thread_markdown(
            hit,
            messages,
            state.names,
            tz=TZ,
            attachment_lines=attachments,
            version=version,
        )
        try:
            vault.write_text(rel, md)
        except Exception as exc:  # noqa: BLE001
            print(f"slack_poll: write {rel} failed ({exc})")
            continue
        advance_watch(state, key, latest_ts=newest, rel=rel, version=version)
        written += 1
        print(f"slack_poll: wrote {rel} kind={entry.kind} key={key}")
        # Persist after each dump so a mid-tick crash / CAS failure does not
        # re-dump the same empty-rel watches forever.
        try:
            state_mtime = _write_state(vault, state, state_mtime)
        except Exception as exc:  # noqa: BLE001
            print(f"slack_poll: state persist after write failed: {exc}")

    try:
        state_mtime = _write_state(vault, state, state_mtime)
    except Exception as exc:  # noqa: BLE001
        print(f"slack_poll: final state write failed: {exc}")
        raise
    print(
        f"slack_poll: done enrolled={enrolled} written={written} "
        f"watch={len(state.watch)} ({now.isoformat()})"
    )


if __name__ == "__main__":
    main()
