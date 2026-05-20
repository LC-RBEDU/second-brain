#!/usr/bin/env python3
"""One-shot ID migration so each project uses a single canonical tag (per user 2026-05-20).

- firemni-procesy: F+P (mix) -> FP, sequential 1..N (active -> backlog -> HOTOVO order)
- vibe-coding:     V+I (mix) -> VC, sequential 1..N
- ma-odyssey:      O -> MO
- kratky-potlesk:  K -> KP
- obchodni-podminky-rb-edu: H -> OP
- rb-network:      N -> RBN

Updates `02-Projekty/<slug>.md` (headers, HOTOVO bullets, in-body references) AND
`00-System/dashboard-tasks-source.json` (preserves ICE/dl/waitUntil/ch).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
PROJEKTY = VAULT / "02-Projekty"
SOURCE_JSON = VAULT / "00-System/dashboard-tasks-source.json"

HEAD_RE = re.compile(
    r"(^###\s+(?:~~)?)([A-Z]+\d+[a-z]?)(?=\s*[—–-])",
    re.MULTILINE,
)
HOTOVO_BULLET_RE = re.compile(r"(^-\s+\*\*)([A-Z]+\d+[a-z]?)(\*\*)", re.MULTILINE)
WORD_RE = re.compile(r"\b([A-Z]+\d+[a-z]?)\b")

# Per-project rename plans
RENAMES: dict[str, dict[str, str]] = {
    "firemni-procesy": {
        # Active in markdown order
        "P2": "FP1",
        "F8": "FP2",
        "P8": "FP3",
        "P9": "FP4",
        "P10": "FP5",
        "P11": "FP6",
        "P12": "FP7",
        "P17": "FP8",
        "P13": "FP9",
        "P14": "FP10",
        "P15": "FP11",
        "P18": "FP12",
        "F3": "FP13",
        "P19": "FP14",
        "P20": "FP15",
        "P21": "FP16",
        "P22": "FP17",
        "P23": "FP18",
        # Backlog
        "P1": "FP19",
        "P4": "FP20",
        "F6": "FP21",
        "P5": "FP22",
        "P3": "FP23",
        "P16": "FP24",
        "P6": "FP25",
        # HOTOVO
        "P7": "FP26",
        "F1": "FP27",
    },
    "vibe-coding": {
        "V2": "VC1",
        "I7": "VC2",
        "V1": "VC3",
    },
    "ma-odyssey": {
        "O1": "MO1", "O2": "MO2", "O3": "MO3", "O4": "MO4",
        "O5": "MO5", "O7": "MO7", "O8": "MO8",
    },
    "kratky-potlesk": {
        "K1": "KP1", "K2": "KP2", "K3": "KP3",
        "K4": "KP4", "K5": "KP5", "K6": "KP6", "K7": "KP7",
    },
    "obchodni-podminky-rb-edu": {
        "H3": "OP3", "H4": "OP4", "H5": "OP5",
    },
    "rb-network": {
        "N1": "RBN1",
    },
}

# Cross-project body references (file slug -> {old_id: new_id})
# Apply within finance.md / rb-universe-development.md to fix "navazuje na P11" etc.
CROSS_REFS: dict[str, dict[str, str]] = {
    "finance": {  # references to firemni-procesy IDs in body text
        "P11": "FP6",
        "P15": "FP11",
        "P19": "FP14",
        "P20": "FP15",
        "P21": "FP16",
        "P22": "FP17",
    },
}


def rewrite_markdown(slug: str, mapping: dict[str, str]) -> int:
    path = PROJEKTY / f"{slug}.md"
    if not path.is_file():
        print(f"  [skip] no file {path.name}")
        return 0
    text = path.read_text(encoding="utf-8")

    def head_sub(m: re.Match) -> str:
        prefix, tid = m.group(1), m.group(2)
        return f"{prefix}{mapping.get(tid, tid)}"

    def bullet_sub(m: re.Match) -> str:
        pre, tid, post = m.group(1), m.group(2), m.group(3)
        return f"{pre}{mapping.get(tid, tid)}{post}"

    new = HEAD_RE.sub(head_sub, text)
    new = HOTOVO_BULLET_RE.sub(bullet_sub, new)

    # In-body references (only IDs that appear in the rename map for this project)
    def word_sub(m: re.Match) -> str:
        tid = m.group(1)
        if tid in mapping:
            return mapping[tid]
        return tid

    new = WORD_RE.sub(word_sub, new)

    if new != text:
        path.write_text(new, encoding="utf-8")
    return sum(1 for k in mapping if k in text and k != mapping[k])


def rewrite_cross_refs(slug: str, mapping: dict[str, str]) -> int:
    path = PROJEKTY / f"{slug}.md"
    if not path.is_file() or not mapping:
        return 0
    text = path.read_text(encoding="utf-8")
    new = text
    for old, new_id in mapping.items():
        new = re.sub(rf"\b{re.escape(old)}\b", new_id, new)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return sum(1 for k in mapping if k in text)


def remap_source_json() -> tuple[int, int]:
    if not SOURCE_JSON.is_file():
        print("  [warn] source json not found")
        return 0, 0
    data = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    renamed = 0
    dropped = 0
    seen: set[tuple[str, str]] = set()
    out_tasks: list[dict] = []
    for t in data.get("tasks", []):
        slug = t.get("proj") or ""
        old_id = t.get("id") or ""
        new_id = RENAMES.get(slug, {}).get(old_id, old_id)
        key = (slug, new_id)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        if new_id != old_id:
            renamed += 1
            t["id"] = new_id
        # strip any cached displayId so build_dashboard recomputes from canonical id
        t.pop("displayId", None)
        t.pop("projPrefix", None)
        out_tasks.append(t)
    data["tasks"] = out_tasks
    SOURCE_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return renamed, dropped


def main() -> None:
    print(f"Vault: {VAULT}")
    if not PROJEKTY.is_dir():
        print("ERROR: projekty dir not found", file=sys.stderr)
        sys.exit(1)

    for slug, mapping in RENAMES.items():
        n = rewrite_markdown(slug, mapping)
        print(f"  md  {slug}.md             {n} ids renamed")

    for slug, mapping in CROSS_REFS.items():
        n = rewrite_cross_refs(slug, mapping)
        if n:
            print(f"  ref {slug}.md             {n} cross-refs updated")

    renamed, dropped = remap_source_json()
    print(f"  json renamed={renamed}, dropped(dup)={dropped}")
    print("done. Now run: python3 cron/sync_tasks_from_projekty.py --force && python3 cron/build_dashboard.py")


if __name__ == "__main__":
    main()
