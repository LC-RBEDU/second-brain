"""Deterministic Sembly → MD fill (R9 / Q7) — no LLM."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any


def _slug_title(title: str, max_len: int = 50) -> str:
    s = unicodedata.normalize("NFC", (title or "meeting").strip())
    for ch in '\\/:*?"<>|':
        s = s.replace(ch, "")
    s = re.sub(r"\s+", "-", s)
    return (s[:max_len] or "meeting").rstrip("-")


def _parse_start(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw)
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def filename_for(payload: dict[str, Any]) -> str:
    meeting = payload.get("meeting") or payload
    title = str(meeting.get("title") or payload.get("title") or "meeting")
    start = _parse_start(
        meeting.get("start_time")
        or meeting.get("started_at")
        or payload.get("start_time")
    )
    stamp = start.strftime("%Y-%m-%d-%H%M") if start else "unknown-time"
    return f"{stamp}-{_slug_title(title)}.md"


def render_markdown(payload: dict[str, Any]) -> str:
    meeting = payload.get("meeting") or payload
    title = str(meeting.get("title") or payload.get("title") or "Meeting")
    start = _parse_start(
        meeting.get("start_time")
        or meeting.get("started_at")
        or payload.get("start_time")
    )
    when = start.strftime("%Y-%m-%d %H:%M") if start else "—"
    participants = meeting.get("participants") or payload.get("participants") or []
    if isinstance(participants, list):
        parts = ", ".join(
            (p.get("name") if isinstance(p, dict) else str(p)) for p in participants
        )
    else:
        parts = str(participants)
    duration = meeting.get("duration_minutes") or meeting.get("duration") or "—"
    permalink = (
        meeting.get("permalink")
        or meeting.get("url")
        or payload.get("permalink")
        or ""
    )
    summary = (
        payload.get("summary")
        or meeting.get("summary")
        or payload.get("auto_summary")
        or ""
    )
    actions = payload.get("action_items") or meeting.get("action_items") or []
    if isinstance(actions, list):
        action_lines = []
        for a in actions:
            text = a.get("text") if isinstance(a, dict) else str(a)
            action_lines.append(f"- [ ] {text}")
        actions_md = "\n".join(action_lines) if action_lines else "- [ ] —"
    else:
        actions_md = str(actions)
    transcript = (
        payload.get("transcript")
        or meeting.get("transcript")
        or payload.get("full_transcript")
        or ""
    )
    return (
        f"# {title} — {when}\n\n"
        f"**Účastníci**: {parts or '—'}\n"
        f"**Trvání**: {duration} min\n"
        f"**Sembly**: {permalink or '—'}\n\n"
        f"## Shrnutí\n\n{summary or '—'}\n\n"
        f"## Akční body\n\n{actions_md}\n\n"
        f"## Plný transkript\n\n{transcript or '—'}\n"
    )
