#!/usr/bin/env python3
"""One-shot: clear review_deadline on open tasks that also have deadline.

Exclusive axes model (2026-10-01): when deadline exists, review_deadline is
ignored and should be empty in vault.

Usage:
    python3 scripts/clear_review_when_deadline.py            # apply
    python3 scripts/clear_review_when_deadline.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "OBSIDIAN"
TASKS_GLOB = "02-PROJEKTY/*/tasks/*.md"
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _field(fm: str, key: str) -> str | None:
    # Use [ \t]* not \s* — \s would swallow the newline and capture the next key.
    m = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.*)$", fm)
    if not m:
        return None
    val = m.group(1).strip().strip("\"'")
    if not val or val.lower() in ("null", "~", "none"):
        return None
    return val[:10] if re.match(r"\d{4}-\d{2}-\d{2}", val) else val or None


def clear_review(text: str) -> tuple[str, bool]:
    m = FM_RE.match(text)
    if not m:
        return text, False
    fm = m.group(1)
    if not _field(fm, "deadline"):
        return text, False
    if not _field(fm, "review_deadline"):
        return text, False
    new_fm = re.sub(
        r"(?m)^review_deadline:[ \t]*.*$",
        "review_deadline:",
        fm,
        count=1,
    )
    if new_fm == fm:
        return text, False
    return text[: m.start(1)] + new_fm + text[m.end(1) :], True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vault", type=Path, default=VAULT)
    args = ap.parse_args()
    paths = sorted((args.vault).glob(TASKS_GLOB))
    changed: list[Path] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        new, ok = clear_review(raw)
        if not ok:
            continue
        changed.append(path)
        if not args.dry_run:
            path.write_text(new, encoding="utf-8")
    mode = "would clear" if args.dry_run else "cleared"
    print(f"{mode} review_deadline on {len(changed)} task(s)")
    for p in changed:
        print(f"  - {p.relative_to(args.vault)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
