#!/usr/bin/env python3
"""Allocate the next free task ID for a project — scan-then-max, never recycle.

    python3 scripts/next_task_id.py <slug>          # → e.g. "F42"
    python3 scripts/next_task_id.py <slug> --why    # + where the ceiling came from
    python3 scripts/next_task_id.py --check         # report duplicate IDs, exit 1 if any

Logic lives in vps/second-brain-hub/lib/task_id_allocate.py (shared with Brain).
"""
from __future__ import annotations

import os

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from task_id_allocate import (  # noqa: E402
    PathVault,
    find_duplicates,
    next_id,
    with_level,
)

VAULT = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("slug", nargs="?", help="project slug, e.g. finance")
    ap.add_argument("--why", action="store_true", help="show where the ceiling came from")
    ap.add_argument("--check", action="store_true", help="report duplicate IDs and exit 1 if any")
    ap.add_argument(
        "--type",
        choices=("epic", "story", "task"),
        help="hierarchy level; adds the level letter (RBU-E73 / RBU-S73 / RBU-T73)",
    )
    args = ap.parse_args()

    vault = PathVault(VAULT)

    if args.check:
        dups = find_duplicates(vault)
        if not dups:
            print("✓ žádné duplicitní task ID")
            return 0
        print(f"✗ duplicitní task ID: {len(dups)}")
        for tid, paths in sorted(dups.items()):
            print(f"  {tid}")
            for p in paths:
                print(f"    {p}")
        return 1

    if not args.slug:
        ap.error("chybí slug (nebo použij --check)")

    new_id, where = next_id(vault, args.slug)
    if args.type:
        new_id = with_level(new_id, args.type)
    print(new_id if not args.why else f"{new_id}   (strop podle: {where})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
