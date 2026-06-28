#!/usr/bin/env python3
"""DEPRECATED — per-project workspace: frontmatter removed (2026-05).

Was: Fix broken workspace YAML in hub frontmatter.
Use: scripts/patch_hub_sources.py --strip-workspace if legacy hubs resurface.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HUBS = REPO / "OBSIDIAN" / "02-PROJEKTY"

BAD = re.compile(
    r"^(  (?:calendar|gmail|drive):)\n  \[\]\n",
    re.M,
)


def main() -> None:
    n = 0
    for p in HUBS.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        fixed = BAD.sub(r"\1 []\n", text)
        if fixed != text:
            p.write_text(fixed, encoding="utf-8")
            print(f"fixed: {p.name}")
            n += 1
    print(f"fix_hub_workspace_yaml: {n}")


if __name__ == "__main__":
    main()
