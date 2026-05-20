#!/usr/bin/env python3
"""Backfill ICE into markdown priority lines so md is full SSOT.

For each task in dashboard-tasks-source.json:
- find `### TID — Name` in md
- locate first `**...**` line below it (priority line)
- if line lacks `ICE Ix Cy Ez` AND json ice != default 5/5/5 → inject

Skip when md already has ICE (md is SSOT — keep md value).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
PROJEKTY = VAULT / "02-Projekty"
SOURCE_JSON = VAULT / "00-System/dashboard-tasks-source.json"

ICE_RE = re.compile(r"ICE\s+I\d+\s+C\d+\s+E\d+", re.I)
PRIORITY_LINE_RE = re.compile(r"^\*\*([^*]+)\*\*\s*$", re.MULTILINE)


def find_task_block(text: str, tid: str) -> tuple[int, int] | None:
    head_re = re.compile(
        rf"^###\s+(?:~~)?{re.escape(tid)}(?=\s*[—–-])",
        re.MULTILINE,
    )
    m = head_re.search(text)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"^###\s+", text[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(text)
    return (start, end)


def inject_ice_into_priority_line(
    block: str, ice: dict, fallback_priority: str
) -> tuple[str, bool]:
    """Return (new_block, changed). Inserts priority line if missing."""
    if ICE_RE.search(block):
        return block, False
    pl = PRIORITY_LINE_RE.search(block)
    if pl:
        content = pl.group(1).strip()
        new_content = f"{content} | ICE I{ice['i']} C{ice['c']} E{ice['e']}"
        new_line = f"**{new_content}**"
        new_block = block[: pl.start()] + new_line + block[pl.end() :]
        return new_block, True
    # No priority line — insert one right at start of block (block starts after "### TID — Name\n")
    new_line = f"**{fallback_priority} | ICE I{ice['i']} C{ice['c']} E{ice['e']}**\n"
    leading = block.lstrip("\n")
    pad = block[: len(block) - len(leading)]
    return pad + new_line + leading, True


def main() -> None:
    src = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    by_proj_id = {(t["proj"], t["id"]): t for t in src["tasks"]}

    files_changed = 0
    tasks_updated = 0
    skipped_default = 0
    not_found = []

    for slug in sorted({t["proj"] for t in src["tasks"]}):
        path = PROJEKTY / f"{slug}.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new_text = text
        changed = False
        for t in src["tasks"]:
            if t["proj"] != slug:
                continue
            ice = t.get("ice") or {}
            i, c, e = ice.get("i", 5), ice.get("c", 5), ice.get("e", 5)
            if (i, c, e) == (5, 5, 5):
                # default — skip
                skipped_default += 1
                continue
            if t.get("st") == "dn":
                # done tasks: ICE not displayed in HOTOVO bullet, OK to skip
                continue
            block_range = find_task_block(new_text, t["id"])
            if not block_range:
                not_found.append((slug, t["id"]))
                continue
            s, e_ = block_range
            block = new_text[s:e_]
            fallback_priority = t.get("p") or "Backlog"
            if fallback_priority == "Waiting":
                fallback_priority = "Backlog"
            new_block, did_change = inject_ice_into_priority_line(
                block, ice, fallback_priority
            )
            if did_change:
                new_text = new_text[:s] + new_block + new_text[e_:]
                changed = True
                tasks_updated += 1
        if changed:
            path.write_text(new_text, encoding="utf-8")
            files_changed += 1
            print(f"  updated {path.name}")

    print(f"\nFiles changed: {files_changed}")
    print(f"Tasks ICE backfilled: {tasks_updated}")
    print(f"Skipped (default 5/5/5 or done): {skipped_default}")
    if not_found:
        print(f"Tasks not found in md headers: {len(not_found)}")
        for s, i in not_found[:20]:
            print(f"  {s}/{i}")


if __name__ == "__main__":
    main()
