#!/usr/bin/env python3
"""Smoke test for lib/drive_io.DriveVault against the real Google Drive.

Usage (OAuth — preferred):
    GOOGLE_DRIVE_OAUTH_JSON="$(cat ~/.config/mrluc/oauth_creds.json)" \
    VAULT_DRIVE_ID=1FYeCEsC6rRtZPayjToEJqwGWAZax3eRD \
        python3 scripts/smoke_drive_io.py

Usage (Service Account fallback):
    GOOGLE_DRIVE_SA_JSON='{...}' VAULT_DRIVE_ID=1FYeC... \
        python3 scripts/smoke_drive_io.py

Performs a round-trip exercising the operations cron jobs need:
  1. list 01-INBOX subfolders
  2. count 02-PROJEKTY/*.md
  3. write + read + delete a dummy file under 00-System/_smoke/
  4. mtime-based CAS rewrite of the dummy file (positive case)

Exits non-zero on the first failure.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, credentials_from_env  # noqa: E402


def main() -> int:
    vault_id = os.environ.get("VAULT_DRIVE_ID")
    if not vault_id:
        print("ERROR: set VAULT_DRIVE_ID", file=sys.stderr)
        return 2
    try:
        creds, mode = credentials_from_env()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"== auth mode: {mode} ==")
    vault = DriveVault(vault_id, credentials=creds)

    print("== root meta ==")
    root = vault.stat("")
    print(f"  id={root.id} name={root.name}")

    print("== 01-INBOX children ==")
    children = vault.list_dir("01-INBOX", include_folders=True)
    for c in children:
        kind = "DIR" if c.is_folder else "FILE"
        print(f"  [{kind}] {c.name}")

    print("== 02-PROJEKTY/*.md count ==")
    hubs = vault.list_dir("02-PROJEKTY", pattern="*.md")
    print(f"  {len(hubs)} hubs")
    for h in hubs[:3]:
        print(f"  - {h.name} | mtime={h.modified_time.isoformat()}")
    if len(hubs) > 3:
        print(f"  ... +{len(hubs) - 3} more")

    print("== write + read + CAS + delete smoke ==")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    rel = f"00-System/_smoke/_smoke_{stamp}.json"
    payload = {"smoke": True, "ts": stamp}
    meta = vault.write_json(rel, payload)
    print(f"  wrote {rel} mtime={meta.modified_time.isoformat()}")
    loaded, meta_read = vault.read_json(rel)
    assert loaded == payload, f"roundtrip mismatch: {loaded!r} != {payload!r}"
    print("  roundtrip OK")
    payload2 = {**payload, "rewritten": True}
    meta_cas = vault.write_json(rel, payload2, expect_mtime=meta_read.modified_time)
    print(f"  CAS rewrite OK new mtime={meta_cas.modified_time.isoformat()}")
    vault.delete(rel)
    print(f"  deleted {rel} (moved to trash)")

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
