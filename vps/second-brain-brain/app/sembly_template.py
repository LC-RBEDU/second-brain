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


def _meeting_blob(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("meeting", "meeting_data", "data"):
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _pick(*vals: Any) -> Any:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v.strip() if isinstance(v, str) else v
    return None


def _coerce_number(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _field(payload: dict[str, Any], blob: dict[str, Any], *keys: str) -> Any:
    candidates: list[Any] = []
    for key in keys:
        candidates.append(payload.get(key))
        candidates.append(blob.get(key))
    return _pick(*candidates)


def _duration_minutes_value(payload: dict[str, Any], blob: dict[str, Any]) -> int | str:
    minutes = _coerce_number(_field(payload, blob, "duration_minutes"))
    if minutes is not None:
        return int(round(minutes))
    raw = _coerce_number(_field(payload, blob, "duration", "meeting_duration"))
    if raw is None:
        return "—"
    if raw >= 1000:
        return int(round(raw / 60))
    return int(round(raw))


def _participants_label(payload: dict[str, Any], blob: dict[str, Any]) -> str:
    raw = _field(payload, blob, "participants", "attendees")
    if raw is None:
        return "—"
    if isinstance(raw, list):
        parts = []
        for p in raw:
            if isinstance(p, dict):
                name = _pick(p.get("name"), p.get("email"), str(p))
                if name is not None:
                    parts.append(str(name))
            else:
                text = str(p).strip()
                if text:
                    parts.append(text)
        return ", ".join(parts) if parts else "—"
    text = str(raw).strip()
    return text or "—"


def _title_and_start(payload: dict[str, Any]) -> tuple[str, datetime | None]:
    blob = _meeting_blob(payload)
    title = _field(
        payload, blob, "meeting_title", "title", "name", "subject", "meetingName"
    )
    title_s = str(title) if title is not None else "meeting"
    start = _parse_start(
        _field(
            payload,
            blob,
            "meeting_started_at",
            "start_time",
            "started_at",
            "meeting_start",
        )
    )
    return title_s, start


def filename_for(payload: dict[str, Any]) -> str:
    title, start = _title_and_start(payload)
    stamp = start.strftime("%Y-%m-%d-%H%M") if start else "unknown-time"
    return f"{stamp}-{_slug_title(title)}.md"


def render_markdown(payload: dict[str, Any]) -> str:
    blob = _meeting_blob(payload)
    title, start = _title_and_start(payload)
    display_title = title if title != "meeting" else "Meeting"
    when = start.strftime("%Y-%m-%d %H:%M") if start else "—"
    parts = _participants_label(payload, blob)
    duration = _duration_minutes_value(payload, blob)
    if isinstance(duration, int):
        duration_line = f"**Trvání**: {duration} min"
    else:
        duration_line = f"**Trvání**: {duration}"
    permalink = _field(payload, blob, "permalink", "url", "meeting_url") or ""
    summary = _field(payload, blob, "summary", "auto_summary") or ""
    actions = _field(payload, blob, "action_items") or []
    if isinstance(actions, list):
        action_lines = []
        for a in actions:
            text = a.get("text") if isinstance(a, dict) else str(a)
            action_lines.append(f"- [ ] {text}")
        actions_md = "\n".join(action_lines) if action_lines else "- [ ] —"
    else:
        actions_md = str(actions)
    transcript = (
        _field(
            payload,
            blob,
            "meeting_transcription",
            "transcript",
            "transcription",
            "full_transcript",
            "content",
        )
        or ""
    )
    return (
        f"# {display_title} — {when}\n\n"
        f"**Účastníci**: {parts}\n"
        f"{duration_line}\n"
        f"**Sembly**: {permalink or '—'}\n\n"
        f"## Shrnutí\n\n{summary or '—'}\n\n"
        f"## Akční body\n\n{actions_md}\n\n"
        f"## Plný transkript\n\n{transcript or '—'}\n"
    )
