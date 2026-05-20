#!/usr/bin/env python3
"""Scan 01-INBOX and write Triage-Pending batch JSON (semi-auto; approve in Cursor).

Waiting tasks with expired waitUntil are written by build_dashboard.py as
`00-System/Triage-Pending/waiting-<proj>-<id>-<date>.json` (type waiting_expired).
Approve in Cursor via agenda-triage PENDING mode — not processed by this script.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

VAULT = Path(os.environ.get("VAULT_PATH", Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC"))
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

# Standard MrLUC INBOX layout (Drive mirror → VPS /data/mrluc/01-INBOX/)
INBOX_SUBDIRS = ("slack", "sembly", "email", "daily")

SLUG_HINTS = [
    ("rb-universe", "rb-universe-development"),
    ("universe", "rb-universe-development"),
    ("pipedrive", "pipedrive-a-dalsi-nastroje"),
    ("finance", "finance"),
    ("finan", "finance"),
    ("strategy", "strategy"),
    ("strateg", "strategy"),
    ("proces", "firemni-procesy"),
    ("operations", "operations"),
    ("odyssey", "ma-odyssey"),
    ("potlesk", "kratky-potlesk"),
    ("inspirace", "obecna-inspirace"),
    ("exponential", "exponential-summit"),
    ("vibe", "vibe-coding"),
]


def guess_proj(text: str, path: Path) -> str:
    low = (text + " " + str(path)).lower()
    for needle, slug in SLUG_HINTS:
        if needle in low:
            return slug
    if "slack" in path.parts:
        return "firemni-procesy"
    if "sembly" in path.parts:
        return "strategy"
    if "email" in path.parts:
        return "finance"
    if "daily" in path.parts:
        return "firemni-procesy"
    return "firemni-procesy"


def title_from_file(p: Path, body: str) -> str:
    for line in body.splitlines()[:30]:
        if line.startswith("# "):
            return line[2:].strip()[:120]
    m = re.search(r"capture[:\s]+(.+)", body, re.I)
    if m:
        return m.group(1).strip()[:120]
    return p.stem.replace("-", " ")[:120]


def iter_inbox_files(inbox: Path) -> list[Path]:
    files: list[Path] = []
    if not inbox.exists():
        return files
    for sub in INBOX_SUBDIRS:
        subdir = inbox / sub
        if not subdir.is_dir():
            continue
        for p in subdir.rglob("*.md"):
            if p.name.startswith("README"):
                continue
            if "ZPRACOVÁNO" in p.read_text(encoding="utf-8", errors="ignore")[:400]:
                continue
            files.append(p)
    return files


def main() -> None:
    inbox = VAULT / "01-INBOX"
    pending_dir = VAULT / "00-System/Triage-Pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    files = iter_inbox_files(inbox)

    if not files:
        print("no inbox files to triage")
        return

    now = datetime.now(TZ)
    batch_id = now.strftime("%Y-%m-%d-%H%M")
    proposals = []
    for i, p in enumerate(sorted(files), 1):
        rel = p.relative_to(VAULT)
        body = p.read_text(encoding="utf-8", errors="ignore")
        proposals.append(
            {
                "id": f"p{i}",
                "action": "add_task",
                "title": title_from_file(p, body),
                "suggestedProj": guess_proj(body, p),
                "priority": "Next",
                "ice": [7, 6, 5],
                "notes": "",
                "subtasks": [],
                "sourceFile": str(rel),
            }
        )

    batch = {
        "batchId": batch_id,
        "status": "open",
        "created": now.isoformat(),
        "sourceFiles": [pr["sourceFile"] for pr in proposals],
        "proposals": proposals,
    }
    out = pending_dir / f"{batch_id}-batch.json"
    out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = pending_dir / f"{batch_id}-summary.md"
    lines = [f"# Triage batch {batch_id}\n", f"**Počet návrhů:** {len(proposals)}\n", "| ID | Návrh | Projekt |", "|----|-------|---------|"]
    for pr in proposals:
        lines.append(f"| {pr['id']} | {pr['title'][:60]} | {pr['suggestedProj']} |")
    lines.append("\nSchválení: v Cursoru `schval pending triáž`\n")
    summary.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out, "proposals=", len(proposals))


if __name__ == "__main__":
    main()
