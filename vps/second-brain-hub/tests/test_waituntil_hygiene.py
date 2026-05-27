"""Unit tests for waitUntil hygiene invariant."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_CRON = Path(__file__).resolve().parents[1] / "cron"
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

from lifecycle_waituntil_hygiene import should_clear_wait_until  # noqa: E402


def test_waiting_keeps_wait_until():
    assert should_clear_wait_until("Waiting", "2026-06-01") is False
    assert should_clear_wait_until("Waiting", date(2026, 6, 1)) is False


def test_asap_clears_wait_until():
    assert should_clear_wait_until("ASAP", "2026-06-01") is True
    assert should_clear_wait_until("ASAP", None) is False
    assert should_clear_wait_until("ASAP", "") is False


def test_other_statuses_clear_when_set():
    for status in ("Next", "Backlog", "Doing", "Done"):
        assert should_clear_wait_until(status, "2026-06-01") is True
        assert should_clear_wait_until(status, None) is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
    print("all passed")
