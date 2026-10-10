"""Reminder chat delivery — Grok Bot webhook → Claude → Slack (F2-i / C4)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo

DEFAULT_MAX_ATTEMPTS = 5


@dataclass
class ChannelResult:
    channel: str  # grok | claude | slack
    ok: bool
    detail: str = ""
    skipped: bool = False


def max_attempts(env: Mapping[str, str] | None = None) -> int:
    env_map = env if env is not None else os.environ
    raw = (env_map.get("REMINDER_MAX_ATTEMPTS") or "").strip()
    if not raw:
        return DEFAULT_MAX_ATTEMPTS
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MAX_ATTEMPTS


def backoff_minutes(attempt_count: int) -> int:
    """A23: min(60, 2^attempt) minutes."""
    return min(60, 2 ** max(0, int(attempt_count)))


def next_attempt_at(now: datetime, attempt_count: int, tz: ZoneInfo) -> str:
    delta = timedelta(minutes=backoff_minutes(attempt_count))
    return (now.astimezone(tz) + delta).isoformat(timespec="seconds")


def send_grok_chat(
    reminder: dict[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    timeout_s: float = 20.0,
) -> ChannelResult:
    """POST Bot routine webhook (docs/brain-api-runbook.md)."""
    env_map = env if env is not None else os.environ
    url = (env_map.get("GROK_BOT_REMINDER_WEBHOOK_URL") or "").strip()
    key = (env_map.get("GROK_BOT_REMINDER_WEBHOOK_KEY") or "").strip()
    if not url or not key:
        return ChannelResult(
            "grok",
            ok=False,
            detail="GROK_BOT_REMINDER_WEBHOOK_URL/KEY missing",
        )
    body = {
        "task": reminder.get("message") or "",
        "request_id": reminder.get("id") or "",
        "source": "second-brain-hub",
        "deliver_at": reminder.get("deliver_at"),
        "task_ref": reminder.get("task_ref"),
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            if int(code) == 200:
                return ChannelResult("grok", ok=True, detail=f"http={code}")
            return ChannelResult("grok", ok=False, detail=f"http={code}")
    except urllib.error.HTTPError as exc:
        return ChannelResult("grok", ok=False, detail=f"http={exc.code}")
    except Exception as exc:  # noqa: BLE001
        return ChannelResult("grok", ok=False, detail=str(exc))


def send_claude_chat(
    reminder: dict[str, Any],
    *,
    env: Mapping[str, str] | None = None,
) -> ChannelResult:
    """Secondary channel — skip+log when API not configured (A4)."""
    _ = reminder
    env_map = env if env is not None else os.environ
    if not (env_map.get("CLAUDE_REMINDER_WEBHOOK_URL") or "").strip():
        return ChannelResult(
            "claude",
            ok=False,
            skipped=True,
            detail="CLAUDE_REMINDER_WEBHOOK_URL missing — skip",
        )
    # Placeholder until Claude chat transport is provisioned — treat as fail not silent success.
    return ChannelResult(
        "claude",
        ok=False,
        detail="Claude chat transport not implemented",
    )


def send_slack_chat(
    reminder: dict[str, Any],
    *,
    token: str,
    format_text,
    post_message,
    resolve_dm_channel,
    dm_channel_cache: dict[str, str],
) -> ChannelResult:
    """Slack last — only after Grok/Claude (C4). Missing token = skip here."""
    if not token:
        return ChannelResult(
            "slack",
            ok=False,
            skipped=True,
            detail="SLACK_BOT_TOKEN missing — skip after Grok/Claude",
        )
    try:
        from reminders import format_slack_text  # local default

        text = format_text(reminder) if format_text else format_slack_text(reminder)
        target = reminder.get("target") or {"type": "dm"}
        if target.get("type") == "channel":
            channel = (target.get("channel_id") or "").strip()
            if not channel:
                raise ValueError("channel target missing channel_id")
        else:
            if "dm" not in dm_channel_cache:
                dm_channel_cache["dm"] = resolve_dm_channel(token)
            channel = dm_channel_cache["dm"]
        ts = post_message(token, channel, text)
        return ChannelResult("slack", ok=True, detail=f"ts={ts}")
    except Exception as exc:  # noqa: BLE001
        return ChannelResult("slack", ok=False, detail=str(exc))


def deliver_chat_chain(
    reminder: dict[str, Any],
    *,
    env: Mapping[str, str] | None = None,
    slack_token: str = "",
    format_text=None,
    post_message=None,
    resolve_dm_channel=None,
    dm_channel_cache: dict[str, str] | None = None,
) -> tuple[bool, list[ChannelResult]]:
    """Grok → Claude → Slack; stop on first success (A19 / B28)."""
    env_map = env if env is not None else os.environ
    results: list[ChannelResult] = []
    cache = dm_channel_cache if dm_channel_cache is not None else {}

    r = send_grok_chat(reminder, env=env_map)
    results.append(r)
    if r.ok:
        return True, results

    r = send_claude_chat(reminder, env=env_map)
    results.append(r)
    if r.ok:
        return True, results

    if post_message is None or resolve_dm_channel is None:
        results.append(
            ChannelResult("slack", ok=False, detail="slack helpers not provided")
        )
        return False, results

    r = send_slack_chat(
        reminder,
        token=slack_token,
        format_text=format_text,
        post_message=post_message,
        resolve_dm_channel=resolve_dm_channel,
        dm_channel_cache=cache,
    )
    results.append(r)
    return r.ok, results
