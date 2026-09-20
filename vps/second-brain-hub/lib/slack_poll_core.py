"""Pure Slack poll decisions: watermark, dedup, full-thread markdown.

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
LOOKBACK = timedelta(hours=2)
MAX_NEW_THREADS = 8

_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


@dataclass
class ThreadHit:
    channel_id: str
    channel_name: str
    thread_ts: str
    latest_ts: str
    kind: str
    permalink: str = ""


@dataclass
class PollState:
    watermark_ts: str = "0"
    bootstrapped: bool = False
    seen: dict[str, dict[str, str]] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "watermark_ts": self.watermark_ts,
            "bootstrapped": self.bootstrapped,
            "seen": self.seen,
            "names": self.names,
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any] | None) -> PollState:
        raw = raw or {}
        return cls(
            watermark_ts=str(raw.get("watermark_ts") or "0"),
            bootstrapped=bool(raw.get("bootstrapped")),
            seen=dict(raw.get("seen") or {}),
            names=dict(raw.get("names") or {}),
        )


def ts_float(ts: str) -> float:
    try:
        return float(ts)
    except (TypeError, ValueError):
        return 0.0


def thread_key(channel_id: str, thread_ts: str) -> str:
    return f"{channel_id}:{thread_ts}"


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


def hit_from_match(match: dict[str, Any], kind: str) -> ThreadHit | None:
    channel_id, channel_name = _channel(match)
    ts = str(match.get("ts") or "")
    if not channel_id or not ts:
        return None
    thread_ts = str(match.get("thread_ts") or ts)
    return ThreadHit(
        channel_id=channel_id,
        channel_name=channel_name,
        thread_ts=thread_ts,
        latest_ts=ts,
        kind=kind,
        permalink=str(match.get("permalink") or ""),
    )


def select_threads(
    grouped: dict[str, list[tuple[str, dict[str, Any]]]],
    state: PollState,
    *,
    now: datetime,
) -> list[ThreadHit]:
    """Pick threads newer than watermark minus lookback, skipping unchanged seen."""
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
                # mention/dm outrank a plain saved hit on the same thread
                if current and current.kind != "saved_later" and hit.kind == "saved_later":
                    hit.kind = current.kind
                best[key] = hit
    ordered = sorted(best.values(), key=lambda h: ts_float(h.latest_ts))
    return ordered[:MAX_NEW_THREADS]


def inbox_filename(when: datetime, channel_name: str, thread_ts: str) -> str:
    day = when.strftime("%Y-%m-%d")
    slug = _SLUG_RE.sub("-", (channel_name or "slack").lower()).strip("-")[:40] or "slack"
    return f"{day}_{slug}_{thread_ts}.md"


def format_thread_markdown(
    hit: ThreadHit,
    messages: list[dict[str, Any]],
    names: dict[str, str],
    *,
    tz,
    attachment_lines: list[str] | None = None,
) -> str:
    """Full thread, not the tagging line alone. Shape matches existing thread dumps."""
    reason = {
        "mention": "adresováno mně",
        "dm": "adresováno mně",
        "gdm": "adresováno mně",
        "saved_later": "uloženo na později",
    }.get(hit.kind, "adresováno mně")
    lines = [
        "---",
        "source: slack",
        f"kind: {hit.kind}",
        f"channel_id: {hit.channel_id}",
        f"thread_ts: {hit.thread_ts}",
        f"slack_ts: {hit.latest_ts}",
        "---",
        "",
        f"**Vlákno:** {hit.permalink or hit.thread_ts}",
        f"**Kanál:** {hit.channel_name}",
        f"**Thread TS:** {hit.thread_ts}",
        f"**Důvod zálohy:** {reason}",
        "",
    ]
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
