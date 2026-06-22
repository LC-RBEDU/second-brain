#!/usr/bin/env python3
"""sessionStart hook — inject compressed agent-context summary into session."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CTX = REPO / "OBSIDIAN" / "00-System" / "agent-context.json"


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
    if stale:
        lines.append(f"- stale hubs: {len(stale)}")
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
