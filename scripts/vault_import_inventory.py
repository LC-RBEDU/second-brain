#!/usr/bin/env python3
"""F1-a / B9: classify vault files for git blob vs LFS vs Drive-only."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BLOB_MAX = 1 * 1024 * 1024  # ≤1 MiB
LFS_MAX = 40 * 1024 * 1024  # ≤40 MiB


def classify(path: Path, size: int) -> str:
    if path.suffix.lower() == ".md":
        return "blob"  # md always blob (A4 / Q2a)
    if size <= BLOB_MAX:
        return "blob"
    if size <= LFS_MAX:
        return "lfs"
    return "drive-only"


def main() -> int:
    p = argparse.ArgumentParser(description="Vault import inventory (blob / LFS / Drive-only)")
    p.add_argument("root", type=Path, help="Vault root (OBSIDIAN layout)")
    p.add_argument("--tsv", type=Path, default=None, help="Write TSV report")
    p.add_argument("--fail-drive-only", action="store_true", help="Exit 1 if any >40 MiB non-md")
    args = p.parse_args()
    root: Path = args.root
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    rows: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        size = path.stat().st_size
        rel = path.relative_to(root).as_posix()
        rows.append((rel, size, classify(path, size)))

    counts = {"blob": 0, "lfs": 0, "drive-only": 0}
    total = 0
    for _, size, kind in rows:
        counts[kind] += 1
        total += size

    print(f"files={len(rows)} bytes={total}")
    print(f"blob={counts['blob']} lfs={counts['lfs']} drive-only={counts['drive-only']}")

    out = args.tsv
    if out is None:
        out = Path("vault-import-inventory.tsv")
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["rel_path", "size", "class"])
        w.writerows(rows)
    print(f"tsv={out}")

    if args.fail_drive_only and counts["drive-only"]:
        print("error: drive-only files present ( >40 MiB non-md )", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
