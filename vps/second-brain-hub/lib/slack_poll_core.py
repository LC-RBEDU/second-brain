"""Pure Slack poll decisions: watchlist, enroll, versioned inbox dumps.

Network and Drive live in cron/slack_poll.py. This module is safe to unit-test.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

LUKAS_USER_ID = "U014AEZD72S"
STATE_REL = "00-System/slack-poll-state.json"
INBOX_DIR = "01-INBOX/slack"
ARCHIVE_SLACK_GLOB = "07-ARCHIV/inbox-processed"
LOOKBACK = timedelta(hours=2)
MAX_NEW_THREADS = 8
MAX_REFETCH_PER_TICK = 40
FLAT_THREAD_TS = "0"

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")
_PERMALINK_THREAD_RE = re.compile(r"[?&]thread_ts=(\d+\.\d+)")
_VERSION_IN_NAME_RE = re.compile(r"_(\d+\.\d+|0)_v(\d+)\.md$", re.I)
_VERSION_ANY_TS_RE = re.compile(r"_v(\d+)\.md$", re.I)


@dataclass
class ThreadHit:
    channel_id: str
    channel_name: str
    thread_ts: str
    latest_ts: str
    kind: str
    permalink: str = ""


@dataclass
class WatchEntry:
    kind: str
    reason: str
    latest_ts: str
    max_v: int = 0
    rel: str = ""
    ignored: bool = False
    channel_name: str = ""
    permalink: str = ""
    boost_ts: str = ""  # discover priority only — does not advance latest_ts
    eyes_message_ts: str = ""  # pending :eyes: unreact target (match.ts)

    def to_json(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "reason": self.reason,
            "latest_ts": self.latest_ts,
            "max_v": self.max_v,
            "rel": self.rel,
            "ignored": self.ignored,
            "channel_name": self.channel_name,
            "permalink": self.permalink,
            "boost_ts": self.boost_ts,
            "eyes_message_ts": self.eyes_message_ts,
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any] | None) -> WatchEntry:
        raw = raw or {}
        return cls(
            kind=str(raw.get("kind") or "dm"),
            reason=str(raw.get("reason") or ""),
            latest_ts=str(raw.get("latest_ts") or "0"),
            max_v=int(raw.get("max_v") or 0),
            rel=str(raw.get("rel") or ""),
            ignored=bool(raw.get("ignored")),
            channel_name=str(raw.get("channel_name") or ""),
            permalink=str(raw.get("permalink") or ""),
            boost_ts=str(raw.get("boost_ts") or ""),
            eyes_message_ts=str(raw.get("eyes_message_ts") or ""),
        )


@dataclass
class PollState:
    watermark_ts: str = "0"
    bootstrapped: bool = False
    seen: dict[str, dict[str, str]] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)
    watch: dict[str, WatchEntry] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "watermark_ts": self.watermark_ts,
            "bootstrapped": self.bootstrapped,
            "seen": self.seen,
            "names": self.names,
            "watch": {k: v.to_json() for k, v in self.watch.items()},
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any] | None) -> PollState:
        raw = raw or {}
        watch_raw = raw.get("watch") or {}
        watch: dict[str, WatchEntry] = {}
        if isinstance(watch_raw, dict):
            for key, val in watch_raw.items():
                if isinstance(val, dict):
                    watch[str(key)] = WatchEntry.from_json(val)
        return cls(
            watermark_ts=str(raw.get("watermark_ts") or "0"),
            bootstrapped=bool(raw.get("bootstrapped")),
            seen=dict(raw.get("seen") or {}),
            names=dict(raw.get("names") or {}),
            watch=watch,
        )


def ts_float(ts: str) -> float:
    try:
        return float(ts)
    except (TypeError, ValueError):
        return 0.0


def thread_key(channel_id: str, thread_ts: str) -> str:
    return f"{channel_id}:{thread_ts}"


def parse_watch_key(key: str) -> tuple[str, str]:
    channel_id, _, thread_ts = key.partition(":")
    return channel_id, thread_ts or FLAT_THREAD_TS


def bootstrap_state(now: datetime) -> PollState:
    """First run stores 'now' and fetches nothing — no historical dump."""
    ts = f"{now.timestamp():.6f}"
    return PollState(watermark_ts=ts, bootstrapped=True)


def _channel(match: dict[str, Any]) -> tuple[str, str]:
    ch = match.get("channel")
    if isinstance(ch, dict):
        cid = str(ch.get("id") or "")
        name = str(ch.get("name") or cid or "slack")
        return cid, name
    if isinstance(ch, str) and ch:
        return ch, ch
    return "", "slack"


def _channel_flags(match: dict[str, Any]) -> tuple[bool, bool]:
    ch = match.get("channel")
    if not isinstance(ch, dict):
        return False, False
    return bool(ch.get("is_im")), bool(ch.get("is_mpim"))


def is_dm_kind(kind: str) -> bool:
    return kind in {"dm", "gdm"}


def watch_thread_ts_for_hit(hit: ThreadHit) -> str:
    """Return thread_ts already normalized by hit_from_match."""
    return hit.thread_ts


def hit_from_match(match: dict[str, Any], kind: str) -> ThreadHit | None:
    channel_id, channel_name = _channel(match)
    ts = str(match.get("ts") or "")
    if not channel_id or not ts:
        return None
    permalink = str(match.get("permalink") or "")
    is_im, is_mpim = _channel_flags(match)

    from_link = _PERMALINK_THREAD_RE.search(permalink)
    raw_thread = str(match.get("thread_ts") or (from_link.group(1) if from_link else "") or ts)

    # IM = always channel:0. MPIM with a thread root keeps thread_ts (Cowork _vN continuity);
    # flat MPIM (no thread) also uses :0 + history.
    if is_im:
        kind = "dm"
        thread_ts = FLAT_THREAD_TS
    elif is_mpim:
        kind = "gdm"
        has_thread = bool(match.get("thread_ts") or from_link)
        thread_ts = raw_thread if has_thread else FLAT_THREAD_TS
    else:
        if kind in {"to_me", "from_me"}:
            kind = "dm"
        thread_ts = raw_thread

    return ThreadHit(
        channel_id=channel_id,
        channel_name=channel_name,
        thread_ts=thread_ts,
        latest_ts=ts,
        kind=kind,
        permalink=permalink,
    )


def select_threads(
    grouped: dict[str, list[tuple[str, dict[str, Any]]]],
    state: PollState,
    *,
    now: datetime,
) -> list[ThreadHit]:
    """Legacy watermark selection (kept for tests / Later-only path)."""
    if not state.bootstrapped:
        return []
    floor = ts_float(state.watermark_ts) - LOOKBACK.total_seconds()
    best: dict[str, ThreadHit] = {}
    for kind, matches in grouped.items():
        for match in matches:
            hit = hit_from_match(match, kind)
            if hit is None or ts_float(hit.latest_ts) <= floor:
                continue
            key = thread_key(hit.channel_id, hit.thread_ts)
            prev = state.seen.get(key) or {}
            if ts_float(hit.latest_ts) <= ts_float(prev.get("latest_ts") or "0"):
                continue
            current = best.get(key)
            if current is None or ts_float(hit.latest_ts) > ts_float(current.latest_ts):
                if current and current.kind != "eyes" and hit.kind == "eyes":
                    hit.kind = current.kind
                best[key] = hit
    ordered = sorted(best.values(), key=lambda h: ts_float(h.latest_ts), reverse=True)
    return ordered[:MAX_NEW_THREADS]


def discover_hits(grouped: dict[str, list[dict[str, Any]]]) -> list[ThreadHit]:
    """Dedup search matches into ThreadHits for watch enrollment.

    ``eyes`` matches are handled by a separate pass in slack_poll (not here).
    """
    best: dict[str, ThreadHit] = {}
    for kind, matches in grouped.items():
        if kind == "eyes":
            continue
        for match in matches:
            # Skip non-DM for to_me/from_me unless channel flags say otherwise —
            # mentions keep their kinds.
            is_im, is_mpim = _channel_flags(match)
            if kind in {"to_me", "from_me"} and not (is_im or is_mpim):
                continue
            hit = hit_from_match(match, kind)
            if hit is None:
                continue
            if kind == "mention" and (is_im or is_mpim):
                continue
            if kind == "mention":
                hit.kind = "mention"
            key = thread_key(hit.channel_id, hit.thread_ts)
            cur = best.get(key)
            if cur is None or ts_float(hit.latest_ts) > ts_float(cur.latest_ts):
                best[key] = hit
    return list(best.values())


def enroll_watch(
    state: PollState,
    hit: ThreadHit,
    *,
    seed_latest_ts: str,
    reason: str = "",
) -> WatchEntry:
    """Add or refresh watch entry. seed_latest_ts from history/replies limit=1 — never wall clock."""
    key = thread_key(hit.channel_id, hit.thread_ts)
    existing = state.watch.get(key)
    if existing and existing.ignored:
        return existing
    seed = seed_latest_ts if ts_float(seed_latest_ts) > 0 else hit.latest_ts
    if existing:
        if hit.channel_name:
            existing.channel_name = hit.channel_name
        if hit.permalink:
            existing.permalink = hit.permalink
        # :eyes: must not overwrite dm/gdm/mention kind (same pin as legacy saved_later).
        if hit.kind and hit.kind != "eyes":
            existing.kind = hit.kind
        if reason and reason != "eyes":
            existing.reason = reason
        elif reason == "eyes" and not existing.reason:
            existing.reason = reason
        # Do not advance latest_ts on re-enroll (that would skip the dump) —
        # boost sort priority when search sees newer activity (B5 / P).
        if ts_float(hit.latest_ts) > ts_float(existing.latest_ts):
            if ts_float(hit.latest_ts) > ts_float(existing.boost_ts or "0"):
                existing.boost_ts = hit.latest_ts
        return existing
    entry = WatchEntry(
        kind=hit.kind,
        reason=reason or hit.kind,
        latest_ts=seed,
        max_v=0,
        rel="",
        ignored=False,
        channel_name=hit.channel_name,
        permalink=hit.permalink,
        boost_ts=hit.latest_ts if ts_float(hit.latest_ts) > ts_float(seed) else "",
        eyes_message_ts="",
    )
    state.watch[key] = entry
    return entry


def mark_ignored(state: PollState, channel_id: str, thread_ts: str) -> WatchEntry:
    key = thread_key(channel_id, thread_ts)
    entry = state.watch.get(key)
    if entry is None:
        entry = WatchEntry(kind="dm", reason="triage_ignore", latest_ts="0", ignored=True)
        state.watch[key] = entry
    else:
        entry.ignored = True
    return entry


def should_refetch(entry: WatchEntry, newest_ts: str) -> bool:
    if entry.ignored:
        return False
    return ts_float(newest_ts) > ts_float(entry.latest_ts)


def watch_sort_ts(entry: WatchEntry) -> float:
    return max(ts_float(entry.latest_ts), ts_float(entry.boost_ts or "0"))


def select_watch_batch(state: PollState, *, limit: int = MAX_REFETCH_PER_TICK) -> list[str]:
    """Non-ignored watch keys. Prefer pending :eyes: / empty rel, then newest activity."""
    keys = [k for k, e in state.watch.items() if not e.ignored]

    def sort_key(k: str) -> tuple[int, float]:
        e = state.watch[k]
        # 0 = pending eyes or needs first dump → ahead of ordinary captured watches
        tier = 0 if (e.eyes_message_ts or not e.rel) else 1
        return (tier, -watch_sort_ts(e))

    keys.sort(key=sort_key)
    return keys[:limit]


def max_version_from_names(names: list[str], channel_id: str, thread_ts: str) -> int:
    """Highest _vN for this channel+thread among filenames."""
    best = 0
    needle = f"_{thread_ts}_v"
    alt = f"_{channel_id}_"  # unused; match by thread_ts token
    for name in names:
        if needle not in name and not (
            thread_ts == FLAT_THREAD_TS and f"_{FLAT_THREAD_TS}_v" in name and channel_id in name
        ):
            # Flat IM dumps: day_slug_0_vN.md — also match channel id in path if present
            if thread_ts == FLAT_THREAD_TS:
                m = _VERSION_ANY_TS_RE.search(name)
                if m and f"_{FLAT_THREAD_TS}_v" in name:
                    best = max(best, int(m.group(1)))
                continue
            continue
        m = _VERSION_IN_NAME_RE.search(name)
        if m and m.group(1) == thread_ts:
            best = max(best, int(m.group(2)))
    return best


def next_version(entry: WatchEntry, scanned_max: int | None = None) -> int:
    cached = int(entry.max_v or 0)
    if scanned_max is not None:
        cached = max(cached, scanned_max)
    return cached + 1


def inbox_filename(when: datetime, channel_name: str, thread_ts: str) -> str:
    """Legacy unversioned name (Later overwrite path)."""
    day = when.strftime("%Y-%m-%d")
    slug = _SLUG_RE.sub("-", (channel_name or "slack").lower()).strip("-")[:40] or "slack"
    return f"{day}_{slug}_{thread_ts}.md"


def inbox_filename_vN(
    when: datetime,
    channel_name: str,
    thread_ts: str,
    version: int,
) -> str:
    day = when.strftime("%Y-%m-%d")
    slug = _SLUG_RE.sub("-", (channel_name or "slack").lower()).strip("-")[:40] or "slack"
    return f"{day}_{slug}_{thread_ts}_v{version}.md"


def format_thread_markdown(
    hit: ThreadHit,
    messages: list[dict[str, Any]],
    names: dict[str, str],
    *,
    tz,
    attachment_lines: list[str] | None = None,
    version: int | None = None,
    reason_override: str | None = None,
) -> str:
    """Full thread dump. With version → Cowork-compatible Verze line for triage."""
    reason = reason_override or {
        "mention": "adresováno mně",
        "dm": "adresováno mně",
        "gdm": "adresováno mně",
        "eyes": "označeno :eyes:",
        "saved_later": "uloženo na později",  # legacy dumps
        "watch": "sledované vlákno",
    }.get(hit.kind, "adresováno mně")
    display_ts = hit.thread_ts if hit.thread_ts != FLAT_THREAD_TS else (hit.latest_ts or hit.thread_ts)
    lines = [
        "---",
        "source: slack",
        f"kind: {hit.kind}",
        f"channel_id: {hit.channel_id}",
        f"thread_ts: {hit.thread_ts}",
        f"slack_ts: {hit.latest_ts}",
        "---",
        "",
        f"**Vlákno:** {hit.permalink or display_ts}",
        f"**Kanál:** {hit.channel_name}",
        f"**Thread TS:** {hit.thread_ts}",
    ]
    if version is not None:
        lines.append(f"**Verze:** v{version} ← AKTUÁLNÍ")
    lines.append(f"**Důvod zálohy:** {reason}")
    lines.append("")
    for msg in messages:
        if msg.get("subtype") in {"channel_join", "channel_leave", "bot_add"}:
            continue
        uid = str(msg.get("user") or "")
        name = names.get(uid) or str(msg.get("username") or uid or "?")
        try:
            stamp = datetime.fromtimestamp(float(msg["ts"]), tz=tz)
            clock = stamp.strftime("%H:%M")
        except (KeyError, TypeError, ValueError):
            clock = ""
        text = str(msg.get("text") or "").strip()
        lines.append(f"**{name}** {clock}".rstrip())
        if text:
            lines.append(text)
        lines.append("")
    if attachment_lines:
        lines.append("## Přílohy")
        lines.append("")
        lines.extend(attachment_lines)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def advance_seen(state: PollState, hit: ThreadHit, rel: str) -> None:
    key = thread_key(hit.channel_id, hit.thread_ts)
    state.seen[key] = {"latest_ts": hit.latest_ts, "rel": rel}
    if ts_float(hit.latest_ts) > ts_float(state.watermark_ts):
        state.watermark_ts = hit.latest_ts


def advance_watch(
    state: PollState,
    key: str,
    *,
    latest_ts: str,
    rel: str,
    version: int,
) -> None:
    entry = state.watch.get(key)
    if entry is None:
        return
    entry.latest_ts = latest_ts
    entry.rel = rel
    entry.max_v = max(entry.max_v, version)
    entry.boost_ts = ""
    if ts_float(latest_ts) > ts_float(state.watermark_ts):
        state.watermark_ts = latest_ts


def newest_ts(messages: list[dict[str, Any]]) -> str:
    best = "0"
    for msg in messages:
        ts = str(msg.get("ts") or "")
        if ts_float(ts) > ts_float(best):
            best = ts
    return best


def merge_channel_history_with_replies(
    history: list[dict[str, Any]],
    replies_by_parent: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Flatten channel history + thread replies for a channel:0 dump (dedup by ts)."""
    by_ts: dict[str, dict[str, Any]] = {}
    for msg in history:
        ts = str(msg.get("ts") or "")
        if ts:
            by_ts[ts] = msg
    for parent_ts, replies in replies_by_parent.items():
        for msg in replies:
            ts = str(msg.get("ts") or "")
            if ts:
                by_ts[ts] = msg
    return sorted(by_ts.values(), key=lambda m: ts_float(str(m.get("ts") or "0")))
