#!/usr/bin/env python3
"""Archive one INBOX capture (``.md`` + co-located attachments) or fix orphan attachments."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_LIB = _REPO / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from inbox_archive import archive_inbox_capture, archive_orphan_inbox_attachments  # noqa: E402


def default_vault() -> Path:
    return _REPO / "OBSIDIAN"


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive INBOX item(s) with attachments")
    ap.add_argument(
        "paths",
        nargs="*",
        help="Vault-relative paths under 01-INBOX/ (e.g. 01-INBOX/slack/foo.md)",
    )
    ap.add_argument("--vault", type=Path, default=default_vault())
    ap.add_argument(
        "--orphans",
        action="store_true",
        help="Move attachment orphans whose .md is already in inbox-processed",
    )
    args = ap.parse_args()
    vault: Path = args.vault

    if args.orphans:
        moves = archive_orphan_inbox_attachments(vault)
        for src, dst in moves:
            print(f"orphan: {src} -> {dst}")
        print(f"orphans_moved={len(moves)}")
        return 0

    if not args.paths:
        ap.error("provide paths or --orphans")

    total_att = 0
    for rel in args.paths:
        md_rel, atts = archive_inbox_capture(vault, rel)
        print(f"archived: {md_rel}")
        for a in atts:
            print(f"  attachment: {a}")
        total_att += len(atts)
    print(f"archived_files={len(args.paths)} attachments={total_att}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
