#!/usr/bin/env python3
"""Local: seřadí `## Operativní kroky` ve všech task souborech.

Pořadí: nesplněné vzestupně podle čísla podkroku, pak splněné taktéž.
`### ` podnadpisy uvnitř sekce jsou hranice — položky se přes ně nepřesouvají.

Usage:
    python3 scripts/sort_operational_steps.py --dry-run
    python3 scripts/sort_operational_steps.py
    python3 scripts/sort_operational_steps.py --include-archive
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from operational_steps import sort_operational_steps  # noqa: E402

DEFAULT_VAULT = Path(
    os.environ.get(
        "SECOND_BRAIN_VAULT",
        str(Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"),
    )
)


def iter_task_files(vault: Path, include_archive: bool) -> list[Path]:
    files = sorted((vault / "02-PROJEKTY").glob("*/tasks/*.md"))
    if include_archive:
        files += sorted((vault / "07-ARCHIV" / "tasks-done").glob("*/*.md"))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-archive", action="store_true")
    args = ap.parse_args()

    changed = 0
    scanned = 0
    for path in iter_task_files(args.vault, args.include_archive):
        scanned += 1
        original = path.read_text(encoding="utf-8")
        new_text, did = sort_operational_steps(original)
        if not did or new_text == original:
            continue
        changed += 1
        rel = path.relative_to(args.vault)
        print(f"{'would sort' if args.dry_run else 'sorted'}: {rel}")
        if not args.dry_run:
            path.write_text(new_text, encoding="utf-8")

    print(f"scanned={scanned} changed={changed} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
