"""Non-blocking file lock so a 1–2 min cron does not overlap itself."""
from __future__ import annotations

import fcntl
from pathlib import Path


def try_lock(path: str | Path):
    """Return an open file holding an exclusive lock, or None if busy."""
    handle = open(path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    return handle
