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


def post_message(
    token: str,
    channel: str,
    text: str,
    *,
    blocks: list[dict[str, Any]] | None = None,
    thread_ts: str = "",
) -> str:
    payload: dict[str, Any] = {
        "channel": channel,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if blocks:
        payload["blocks"] = blocks
    if thread_ts:
        payload["thread_ts"] = thread_ts
    body = _post(token, "chat.postMessage", payload)
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


def api_get(token: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    import urllib.parse

    qs = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    url = f"https://slack.com/api/{method}"
    if qs:
        url = f"{url}?{qs}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
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


def search_messages(
    token: str,
    query: str,
    *,
    count: int = 100,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    # desc = newest first. asc returned 2020–2024 DMs/Later and the watermark
    # floor then dropped every hit after bootstrap. Paginate next_cursor (cap max_pages).
    matches: list[dict[str, Any]] = []
    cursor = ""
    for _ in range(max(1, max_pages)):
        params: dict[str, Any] = {
            "query": query,
            "count": str(min(100, max(1, count))),
            "sort": "timestamp",
            "sort_dir": "desc",
        }
        if cursor:
            params["cursor"] = cursor
        body = api_get(token, "search.messages", params)
        page = list((body.get("messages") or {}).get("matches") or [])
        matches.extend(page)
        pagination = body.get("response_metadata") or {}
        # search.messages also nests pagination under messages
        msg_meta = (body.get("messages") or {}).get("pagination") or {}
        cursor = str(
            pagination.get("next_cursor")
            or msg_meta.get("next_cursor")
            or ""
        ).strip()
        if not cursor or not page:
            break
    return matches


def conversation_replies(
    token: str,
    channel: str,
    ts: str,
    *,
    limit: int = 100,
    oldest: str = "",
) -> list[dict[str, Any]]:
    # GET — JSON POST returns invalid_arguments for this method.
    params: dict[str, Any] = {"channel": channel, "ts": ts, "limit": str(limit)}
    if oldest:
        params["oldest"] = oldest
    body = api_get(token, "conversations.replies", params)
    return list(body.get("messages") or [])


def conversation_history(
    token: str,
    channel: str,
    *,
    limit: int = 100,
    oldest: str = "",
) -> list[dict[str, Any]]:
    """Channel messages (IM/MPIM flat). Thread replies are not included — fetch via replies."""
    params: dict[str, Any] = {"channel": channel, "limit": str(limit)}
    if oldest:
        params["oldest"] = oldest
    body = api_get(token, "conversations.history", params)
    return list(body.get("messages") or [])

def user_display_name(token: str, user_id: str, cache: dict[str, str] | None = None) -> str:
    if cache is not None and user_id in cache:
        return cache[user_id]
    body = _post(token, "users.info", {"user": user_id})
    user = body.get("user") or {}
    profile = user.get("profile") or {}
    name = (
        profile.get("real_name")
        or profile.get("display_name")
        or user.get("real_name")
        or user_id
    )
    if cache is not None:
        cache[user_id] = name
    return name


def download_private_file(token: str, url: str, *, max_bytes: int = 5_000_000) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise SlackAPIError("files.download", f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SlackAPIError("files.download", str(exc)) from exc
    if len(data) > max_bytes:
        raise SlackAPIError("files.download", "too_large")
    return data
