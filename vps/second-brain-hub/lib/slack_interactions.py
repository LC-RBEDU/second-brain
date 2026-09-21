"""Slack button Odpověz: verify the click, then the caller posts as Lukáš.

The card lives in the draft channel. The button value is only the target
channel and thread. The text sent is the current reply_body block, so an
edit of that message before the click is what goes out.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qs

from assistant_ingest import LUKAS_SLACK_ID

ACTION_REPLY = "slack_reply_send"
MAX_SKEW_SECONDS = 60 * 5


def verify_slack_signature(secret: str, timestamp: str, body: bytes, signature: str) -> bool:
    if not secret or not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > MAX_SKEW_SECONDS:
        return False
    base = b"v0:" + timestamp.encode("utf-8") + b":" + body
    digest = hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"v0={digest}", signature)


def parse_interaction(body: bytes) -> dict[str, Any]:
    raw = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    payload = (raw.get("payload") or [""])[0]
    if not payload:
        return {}
    data = json.loads(payload)
    return data if isinstance(data, dict) else {}


def reply_from_action(payload: dict[str, Any]) -> tuple[str, str, str] | None:
    """(channel, thread_ts, text) when this click is Lukáš sending a proposal."""
    user = str((payload.get("user") or {}).get("id") or "")
    if user != LUKAS_SLACK_ID:
        return None
    actions = payload.get("actions") or []
    if not actions or actions[0].get("action_id") != ACTION_REPLY:
        return None
    try:
        target = json.loads(actions[0].get("value") or "")
    except json.JSONDecodeError:
        return None
    channel = str(target.get("c") or "")
    thread_ts = str(target.get("t") or "")
    text = ""
    for block in (payload.get("message") or {}).get("blocks") or []:
        if block.get("block_id") == "reply_body":
            text = str((block.get("text") or {}).get("text") or "").strip()
            break
    if not channel or not thread_ts or not text:
        return None
    return channel, thread_ts, text
