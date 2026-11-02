"""Live count of unprocessed Sembly transcripts. Not stored in the snapshot."""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from drive_io import DriveNotFoundError  # noqa: E402

_PREFIX = "01-INBOX/sembly/"


def sembly_pending_stats(vault, *, today: date | None = None) -> dict:
    today = today or datetime.now(ZoneInfo("Europe/Prague")).date()
    try:
        entries = vault.list_dir("01-INBOX/sembly", pattern="*.md", recursive=False)
    except DriveNotFoundError:
        return {"inbox_sembly_pending": 0, "oldest_pending_age_days": None}
    ages: list[int] = []
    for meta in entries:
        name = getattr(meta, "name", "") or ""
        if not name.endswith(".md") or name.startswith("."):
            continue
        stamp = name[:10]
        try:
            day = date.fromisoformat(stamp)
        except ValueError:
            modified = getattr(meta, "modified_time", None)
            if modified is None:
                continue
            day = modified.date()
        ages.append(max(0, (today - day).days))
    if not ages:
        return {"inbox_sembly_pending": 0, "oldest_pending_age_days": None}
    return {
        "inbox_sembly_pending": len(ages),
        "oldest_pending_age_days": max(ages),
    }


def attach_sembly_pending(context: dict, vault) -> dict:
    context.update(sembly_pending_stats(vault))
    return context
