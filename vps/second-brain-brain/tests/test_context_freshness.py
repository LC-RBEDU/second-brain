"""C2 — TTL 15 min exact + timestamp mismatch → needs_rebuild."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.context_freshness import CONTEXT_TTL, needs_rebuild  # noqa: E402


def test_stale_after_exactly_15_minutes():
    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    fresh = {
        "generated_at": (now - CONTEXT_TTL).isoformat(),
    }
    # age == 15 min → not stale (strict >)
    assert needs_rebuild(fresh, fresh, fresh, now=now) is False
    older = {
        "generated_at": (now - CONTEXT_TTL - timedelta(seconds=1)).isoformat(),
    }
    assert needs_rebuild(older, older, older, now=now) is True


def test_timestamp_mismatch_needs_rebuild():
    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    full = {"generated_at": now.isoformat()}
    light = {"generated_at": (now - timedelta(minutes=1)).isoformat()}
    charters = {"generated_at": now.isoformat()}
    assert needs_rebuild(full, light, charters, now=now) is True
