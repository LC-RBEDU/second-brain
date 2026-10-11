#!/usr/bin/env python3
"""F4 one-shot: archive 01-INBOX/slack/*.md (+ attachments + orphans) via GitVault.move CAS.

Uses inbox_archive_dest + list_colocated_attachments. Does NOT call
archive_inbox_capture / archive_orphan_inbox_attachments (Path.rename, no CAS).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402
from inbox_archive import inbox_archive_dest, list_colocated_attachments  # noqa: E402
from vault_factory import open_vault  # noqa: E402

INBOX = "01-INBOX/slack"


def _rel_dest(vault_root: Path, abs_dest: Path) -> str:
    return str(abs_dest.relative_to(vault_root)).replace("\\", "/")


def _move_cas(vault, src_rel: str, *, dry_run: bool) -> str | None:
    """Move one file with expect_oid from stat. Returns dest rel or None on skip."""
    try:
        meta = vault.stat(src_rel)
    except DriveNotFoundError:
        print(f"archive_slack_inbox: skip missing {src_rel}")
        return None
    oid = getattr(meta, "oid", None)
    if not oid:
        print(f"archive_slack_inbox: skip no oid {src_rel}")
        return None
    root = Path(vault.root)
    try:
        dest_abs = inbox_archive_dest(root, src_rel)
    except ValueError as exc:
        print(f"archive_slack_inbox: skip bad dest {src_rel}: {exc}")
        return None
    dst_rel = _rel_dest(root, dest_abs)
    if dry_run:
        print(f"archive_slack_inbox: [dry] would-move {src_rel} -> {dst_rel}")
        return dst_rel
    try:
        vault.move(src_rel, dst_rel, expect_oid=oid)
    except DriveConflictError as exc:
        print(f"archive_slack_inbox: CAS conflict {src_rel}: {exc}")
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"archive_slack_inbox: move failed {src_rel}: {exc}")
        return None
    print(f"archive_slack_inbox: moved {src_rel} -> {dst_rel}")
    return dst_rel


def archive_slack_inbox(*, dry_run: bool = True) -> dict:
    moved = 0
    skipped = 0
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print("archive_slack_inbox: vault session skipped")
            return {"moved": 0, "skipped": 0, "dry_run": dry_run, "skipped_session": True}
        root = Path(vault.root)
        inbox_dir = root / INBOX
        if not inbox_dir.is_dir():
            print(f"archive_slack_inbox: no {INBOX}")
            return {"moved": 0, "skipped": 0, "dry_run": dry_run}

        md_names = sorted(p.name for p in inbox_dir.iterdir() if p.is_file() and p.suffix.lower() == ".md")
        claimed_atts: set[str] = set()

        for md_name in md_names:
            src_rel = f"{INBOX}/{md_name}"
            out = _move_cas(vault, src_rel, dry_run=dry_run)
            if out is None:
                skipped += 1
                continue
            moved += 1
            for att in list_colocated_attachments(inbox_dir, md_name):
                claimed_atts.add(att.name)
                att_rel = f"{INBOX}/{att.name}"
                # After md move (non-dry), att still in inbox; dry_run leaves both.
                aout = _move_cas(vault, att_rel, dry_run=dry_run)
                if aout is None:
                    skipped += 1
                else:
                    moved += 1

        # Orphan non-md files not claimed by a paired md
        for p in sorted(inbox_dir.iterdir()):
            if not p.is_file() or p.suffix.lower() == ".md" or p.name == ".keep":
                continue
            if p.name in claimed_atts:
                continue
            # Skip if still has a md sibling that failed to move (prefix match)
            stem = p.name.split("__", 1)[0]
            if any(n.startswith(stem) or n.rsplit(".", 1)[0] == stem for n in md_names):
                # colocated with remaining md — only if md still present
                if (inbox_dir / f"{stem}.md").exists() or any(
                    n.startswith(stem) for n in md_names if (inbox_dir / n).exists()
                ):
                    continue
            out = _move_cas(vault, f"{INBOX}/{p.name}", dry_run=dry_run)
            if out is None:
                skipped += 1
            else:
                moved += 1

        if not dry_run and not getattr(vault, "dry_run", False):
            vault.commit_if_dirty("hub: F4 archive 01-INBOX/slack → inbox-processed")

    return {"moved": moved, "skipped": skipped, "dry_run": dry_run}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Default True — 0 write. Pass --no-dry-run for real archive.",
    )
    args = parser.parse_args()
    result = archive_slack_inbox(dry_run=args.dry_run)
    print(f"archive_slack_inbox: done {result}")


if __name__ == "__main__":
    main()
