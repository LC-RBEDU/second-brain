"""Scheduled Slack reminders — vault queue schema and helpers."""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

PENDING_DIR = "00-System/Reminders-Pending"
SENT_DIR = "00-System/Reminders-Sent"
CANCELLED_DIR = "00-System/Reminders-Cancelled"
FAILED_DIR = "00-System/Reminders-Failed"

VALID_STATUSES = frozenset({"pending", "sent", "cancelled", "failed"})
_DUE_STATUSES = frozenset({"pending", "failed"})


def default_tz() -> ZoneInfo:
    return ZoneInfo("Europe/Prague")


def parse_deliver_at(value: str, tz: ZoneInfo | None = None) -> datetime:
    """Parse ISO or naive local datetime string into timezone-aware datetime."""
    tz = tz or default_tz()
    raw = (value or "").strip()
    if not raw:
        raise ValueError("deliver_at is empty")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def format_deliver_at(dt: datetime, tz: ZoneInfo | None = None) -> str:
    tz = tz or default_tz()
    return dt.astimezone(tz).isoformat(timespec="seconds")


def make_reminder_id(deliver_at: datetime, tz: ZoneInfo | None = None) -> str:
    tz = tz or default_tz()
    local = deliver_at.astimezone(tz)
    suffix = uuid.uuid4().hex[:6]
    return f"{local:%Y-%m-%d-%H%M}-rem-{suffix}"


def slugify_filename(reminder_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", reminder_id).strip("-")
    return f"{safe}.json"


def reminder_error(reminder: dict[str, Any]) -> str | None:
    """Dual-read last_error || error (legacy)."""
    for key in ("last_error", "error"):
        val = reminder.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if text:
            return text
    return None


def build_reminder(
    *,
    message: str,
    deliver_at: datetime,
    task_ref: str | None = None,
    source: str = "cursor-agent",
    target: dict[str, Any] | None = None,
    tz: ZoneInfo | None = None,
) -> dict[str, Any]:
    tz = tz or default_tz()
    msg = (message or "").strip()
    if not msg:
        raise ValueError("message is empty")
    now = datetime.now(tz)
    deliver = deliver_at.astimezone(tz)
    if deliver <= now:
        raise ValueError("deliver_at must be in the future")

    rid = make_reminder_id(deliver, tz=tz)
    payload: dict[str, Any] = {
        "id": rid,
        "status": "pending",
        "created_at": format_deliver_at(now, tz=tz),
        "deliver_at": format_deliver_at(deliver, tz=tz),
        "message": msg,
        "target": target or {"type": "dm"},
        "source": source,
        "attempt_count": 0,
    }
    if task_ref:
        payload["task_ref"] = task_ref.strip()
    return payload


def format_slack_text(reminder: dict[str, Any]) -> str:
    lines = [reminder.get("message") or ""]
    task_ref = (reminder.get("task_ref") or "").strip()
    if task_ref:
        lines.append("")
        lines.append(f"↳ {task_ref}")
    return "\n".join(lines).strip()


def is_due(reminder: dict[str, Any], now: datetime, tz: ZoneInfo | None = None) -> bool:
    """True when pending|failed, deliver_at ≤ now, and next_attempt_at absent or ≤ now.

    Legacy ``status=failed`` still in Pending remains retryable (A51).
    """
    status = str(reminder.get("status") or "").strip().lower()
    if status not in _DUE_STATUSES:
        return False
    tz = tz or default_tz()
    now_local = now.astimezone(tz)
    deliver = parse_deliver_at(str(reminder["deliver_at"]), tz=tz)
    if deliver > now_local:
        return False
    next_raw = reminder.get("next_attempt_at")
    if next_raw:
        next_at = parse_deliver_at(str(next_raw), tz=tz)
        if next_at > now_local:
            return False
    return True
