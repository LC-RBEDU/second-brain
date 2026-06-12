#!/usr/bin/env python3
"""Refresh ## Stav (auto) marker blocks in project hub charters on Drive.

Schedule: every 2h at :07 (after other lifecycle jobs).
CAS-aware via expect_mtime on hub writes.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import yaml  # noqa: E402

from drive_io import DriveNotFoundError, DriveVault, credentials_from_env  # noqa: E402
from hub_state import (  # noqa: E402
    build_state_content,
    upsert_state_in_hub_body,
)
from task_io import FRONTMATTER_RE, iter_active_tasks, iter_archive_tasks  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
PROJEKTY_DIR = "02-PROJEKTY"


def _parse_hub(text: str) -> tuple[dict, str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text, ""
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm if isinstance(fm, dict) else {}, m.group(1), m.group(2)


def _serialize_hub(fm_yaml: str, body: str) -> str:
    return f"---\n{fm_yaml}---\n{body}"


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    now = datetime.now(TZ)
    today = now.date()
    generated_at = now.isoformat(timespec="minutes")

    active = list(iter_active_tasks(vault))
    archived = list(iter_archive_tasks(vault))

    updated = 0
    skipped = 0
    stale_count = 0

    try:
        hubs = vault.list_dir(PROJEKTY_DIR, pattern="*.md")
    except DriveNotFoundError:
        print("lifecycle_hub_state: no PROJEKTY dir")
        return

    for meta in hubs:
        if meta.name.startswith("_"):
            continue
        try:
            text, file_meta = vault.read_text(meta.rel_path)
        except DriveNotFoundError:
            continue

        fm, fm_yaml, body = _parse_hub(text)
        if (fm.get("type") or "").lower() != "project":
            continue

        slug = str(fm.get("slug") or meta.name.removesuffix(".md"))
        hub_updated = fm.get("updated")
        if isinstance(hub_updated, datetime):
            hub_updated = hub_updated.date().isoformat()
        elif hub_updated is not None:
            hub_updated = str(hub_updated)[:10]

        inner, is_stale = build_state_content(
            slug,
            active,
            archived,
            today,
            hub_updated=hub_updated,
            generated_at=generated_at,
        )
        if is_stale:
            stale_count += 1

        new_body = upsert_state_in_hub_body(body, inner)
        if new_body == body:
            skipped += 1
            continue

        new_text = _serialize_hub(fm_yaml, new_body)
        ok = vault.write_text(
            meta.rel_path,
            new_text,
            expect_mtime=file_meta.modified_time if file_meta else None,
        )
        if ok:
            updated += 1
            print(f"  ✓ {meta.rel_path}")
        else:
            skipped += 1
            print(f"  ~ conflict {meta.rel_path}")

    print(
        f"lifecycle_hub_state: updated={updated} skipped={skipped} "
        f"stale_hubs={stale_count}"
    )


if __name__ == "__main__":
    main()
