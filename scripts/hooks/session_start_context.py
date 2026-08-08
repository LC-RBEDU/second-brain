#!/usr/bin/env python3
"""sessionStart hook — inject compressed agent-context summary into session."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CTX = REPO / "OBSIDIAN" / "00-System" / "agent-context.json"
LESSONS_PENDING = REPO / "OBSIDIAN" / "00-System" / "Lessons-Pending"
_STALE_PENDING_DAYS = 7


def _lessons_pending_line() -> str | None:
    if not LESSONS_PENDING.is_dir():
        return None
    batches = [
        p
        for p in LESSONS_PENDING.iterdir()
        if p.is_file() and p.suffix == ".md" and p.name != ".gitkeep"
    ]
    if not batches:
        return None
    import time

    now = time.time()
    stale = any((now - p.stat().st_mtime) > _STALE_PENDING_DAYS * 86400 for p in batches)
    flag = " **stale**" if stale else ""
    return (
        f"- Lessons ke schválení: **{len(batches)}**{flag} "
        f"(řekni „schval lessons“)"
    )


def main() -> int:
    if not CTX.exists():
        print("<!-- SB: no agent-context.json -->")
        return 0
    try:
        data = json.loads(CTX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0

    stats = data.get("stats") or {}
    top = data.get("top_priority_today") or []
    upcoming = data.get("upcoming_deadlines") or []
    stale = data.get("stale_hubs") or []

    lines = [
        "## MrLUC snapshot (auto)",
        f"- generated: {data.get('generated_at', '?')}",
        f"- open tasks: {stats.get('total_open_tasks', '?')}",
        f"- upcoming 7d: {stats.get('upcoming_deadlines_7d', '?')}",
    ]
    lp = _lessons_pending_line()
    if lp:
        lines.append(lp)
    lines.append("")
    if stale:
        lines.append(f"**Zastaralé chartery ({len(stale)}):**")
        for h in sorted(stale, key=lambda x: str(x.get("hub_updated") or "")):
            lines.append(
                f"- {h.get('hub_filename', h.get('slug'))} — charter {h.get('hub_updated')}, "
                f"tasky {h.get('last_task_activity')}, otevřených {h.get('open_tasks_count')}"
            )
        lines.append("")
    lines.append("**TOP dnes:**")
    for t in top[:5]:
        src_hint = ""
        slug = t.get("slug")
        for p in data.get("projects") or []:
            if p.get("slug") == slug and p.get("sources"):
                src_hint = f" [sources: {', '.join(p['sources'][:3])}]"
                break
        lines.append(
            f"- **{t.get('id')} — {t.get('title', '')[:55]}** "
            f"(score {t.get('today_score', '?')}){src_hint}"
        )
    if upcoming[:3]:
        lines.append("")
        lines.append("**Deadlines (7d):**")
        for t in upcoming[:3]:
            lines.append(f"- {t.get('deadline')} — **{t.get('id')} — {t.get('title', '')[:45]}**")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
