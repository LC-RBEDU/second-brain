#!/usr/bin/env python3
"""OPS2 EDU news marker helper (file-per-task v2).

Topic proposals are **not** generated here anymore — use Cursor skill
`agenda-edu-news` on demand (vault + calendar + agent judgment).

This script only:
  --reset   clear the marker block after recording / between cycles
  (default) no-op with a pointer to the skill (safe if leftover crontab)

Resolves OPS2 by task id (supports `OPS2 — <title>.md` filenames).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, DriveConflictError, credentials_from_env  # noqa: E402
from task_io import iter_active_tasks  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

OPS2_ID = "OPS2"
MARKER_RE = re.compile(
    r"<!-- edu-news-topics:start -->.*?<!-- edu-news-topics:end -->",
    re.DOTALL,
)


def find_ops2_path(vault: DriveVault) -> str | None:
    for task in iter_active_tasks(vault):
        if task.task_id == OPS2_ID and task.slug == "operations":
            return task.rel_path
    return None


def clear_marker(vault: DriveVault, *, dry_run: bool) -> bool:
    """Clear topics marker in OPS2.md. CAS-aware. Returns True if changed."""
    path = find_ops2_path(vault)
    if not path:
        print(f"edu_news: active {OPS2_ID} not found — skipping")
        return False
    try:
        text, meta = vault.read_text(path)
    except DriveNotFoundError:
        print(f"edu_news: {path} not found — skipping")
        return False

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    block = (
        "<!-- edu-news-topics:start -->\n"
        f"**Návrh EDU news** _(vyčištěno {now})_:\n"
        "- _(spusť skill `agenda-edu-news` před nahráním)_\n"
        "<!-- edu-news-topics:end -->"
    )
    if MARKER_RE.search(text):
        new_text = MARKER_RE.sub(block, text)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        new_text = text + "\n" + block + "\n"
    if new_text == text:
        print(f"edu_news: {path} already clear")
        return False
    if dry_run:
        print(f"edu_news: --dry-run would clear marker in {path}")
        return False
    try:
        vault.write_text(path, new_text, expect_mtime=meta.modified_time)
        print(f"edu_news: cleared marker drive://{path}")
        return True
    except DriveConflictError as e:
        print(f"edu_news: OPS2 changed externally — skipping ({e})", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear topics marker (po nahrání / před novým cyklem)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.reset:
        print(
            "edu_news: auto-refresh zrušen — témata připrav skill `agenda-edu-news` "
            "v Cursoru. Pro vyčištění markeru: --reset"
        )
        return

    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    print("edu_news: --reset (clearing topics via agenda-edu-news placeholder)")
    clear_marker(vault, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
