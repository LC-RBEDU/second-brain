"""Minimal Slack Web API client for outbound reminders (stdlib only)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class SlackAPIError(RuntimeError):
    def __init__(self, method: str, error: str, *, ok: bool = False):
        super().__init__(f"Slack {method} failed: {error}")
        self.method = method
        self.error = error
        self.ok = ok


def _post(token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"https://slack.com/api/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SlackAPIError(method, f"HTTP {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise SlackAPIError(method, str(exc)) from exc

    if not body.get("ok"):
        raise SlackAPIError(method, body.get("error") or "unknown_error", ok=False)
    return body


def lookup_user_id_by_email(token: str, email: str) -> str:
    body = _post(token, "users.lookupByEmail", {"email": email.strip().lower()})
    user = body.get("user") or {}
    user_id = user.get("id")
    if not user_id:
        raise SlackAPIError("users.lookupByEmail", "missing user.id")
    return user_id


def open_dm_channel(token: str, user_id: str) -> str:
    body = _post(token, "conversations.open", {"users": user_id})
    channel = (body.get("channel") or {}).get("id")
    if not channel:
        raise SlackAPIError("conversations.open", "missing channel.id")
    return channel


def post_message(token: str, channel: str, text: str) -> str:
    body = _post(
        token,
        "chat.postMessage",
        {"channel": channel, "text": text, "unfurl_links": False, "unfurl_media": False},
    )
    ts = body.get("ts")
    if not ts:
        raise SlackAPIError("chat.postMessage", "missing ts")
    return ts


def resolve_dm_channel(token: str, env: dict | None = None) -> str:
    """Resolve DM channel for reminders from env."""
    env = env if env is not None else os.environ
    user_id = (env.get("SLACK_REMINDER_DM_USER_ID") or "").strip()
    if not user_id:
        email = (
            (env.get("SLACK_REMINDER_USER_EMAIL") or "").strip()
            or (env.get("CALENDAR_USER_EMAIL") or "").strip()
            or "lukas@redbuttonedu.cz"
        )
        user_id = lookup_user_id_by_email(token, email)
    return open_dm_channel(token, user_id)


def send_reminder_dm(token: str, text: str, env: dict | None = None) -> str:
    channel = resolve_dm_channel(token, env=env)
    return post_message(token, channel, text)
