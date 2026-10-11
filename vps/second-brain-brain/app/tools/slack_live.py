"""slack_live — live search, 0 dump write (R7)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _search(token: str, query: str, *, timeout_s: float = 15.0) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode({"query": query, "count": 20})
    req = urllib.request.Request(
        f"https://slack.com/api/search.messages?{qs}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "slack_search_failed")
    matches = ((data.get("messages") or {}).get("matches")) or []
    return [
        {
            "ts": m.get("ts"),
            "channel": (m.get("channel") or {}).get("id"),
            "text": (m.get("text") or "")[:500],
            "permalink": m.get("permalink"),
        }
        for m in matches
    ]


def slack_live_search(*, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    token = (env.get("SLACK_USER_TOKEN") or "").strip()
    uid = (env.get("SLACK_LUKAS_USER_ID") or env.get("LUKAS_USER_ID") or "").strip()
    if not token:
        return {"candidates": [], "error_reason": "slack_token_missing", "dumped": False}
    queries = [
        f"to:<@{uid}>" if uid else "is:im",
        f"from:<@{uid}>" if uid else "from:me",
        f"<@{uid}>" if uid else "@me",
        "hasmy::eyes:",
        "hasmy::gear:",
    ]
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        for q in queries:
            for m in _search(token, q):
                key = f"{m.get('channel')}:{m.get('ts')}"
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(m)
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        return {
            "candidates": candidates,
            "error_reason": f"slack_live_error:{exc}",
            "dumped": False,
        }
    return {"candidates": candidates, "dumped": False}
