#!/usr/bin/env python3
"""GC Meeting-Preps older than 14 days (R14 / C6)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from vault_factory import open_vault  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
PREPS = "00-System/Meeting-Preps"
RETENTION_DAYS = 14


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cutoff = datetime.now(TZ) - timedelta(days=RETENTION_DAYS)
    deleted = 0
    skipped = 0

    with open_vault() as vault:
        if not vault.exists(PREPS):
            print(f"meeting_preps_gc: no dir, dry_run={args.dry_run}")
            return
        try:
            metas = list(vault.list_dir(PREPS, pattern="*.md", recursive=False))
        except Exception as exc:
            print(f"meeting_preps_gc: list failed: {exc}")
            return
        for meta in metas:
            rel = getattr(meta, "rel_path", "")
            mtime = getattr(meta, "mtime", None) or getattr(meta, "modified", None)
            if not rel:
                continue
            too_old = True
            if mtime is not None:
                try:
                    if isinstance(mtime, (int, float)):
                        mt = datetime.fromtimestamp(mtime, tz=TZ)
                    else:
                        mt = datetime.fromisoformat(str(mtime))
                        if mt.tzinfo is None:
                            mt = mt.replace(tzinfo=TZ)
                    too_old = mt < cutoff
                except Exception:
                    too_old = True
            if not too_old:
                skipped += 1
                continue
            oid = getattr(meta, "oid", None)
            if args.dry_run:
                print(f"  [dry] delete {rel} expect_oid={oid}")
                deleted += 1
                continue
            try:
                # Prefer CAS delete when supported
                try:
                    vault.delete(rel, expect_oid=oid)  # type: ignore[call-arg]
                except TypeError:
                    vault.delete(rel)
                print(f"  ✓ deleted {rel}")
                deleted += 1
            except Exception as exc:
                print(f"  ! skip {rel}: {exc}")
                skipped += 1

    print(f"meeting_preps_gc: deleted={deleted}, skipped={skipped}, dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
