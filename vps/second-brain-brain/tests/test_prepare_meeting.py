"""T12 — prepare_meeting dry_run + degrade flags (no vault write)."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.tools.prepare_meeting import prepare_meeting  # noqa: E402


def test_dry_run_no_write_no_deliver():
    out = prepare_meeting(
        "evt-1",
        title="X",
        starts_at="2026-10-11T15:00:00",
        deliver=True,
        dry_run=True,
        env={},
    )
    assert out["dry_run"] is True
    assert out["written"] is False
    assert out["delivered"] is False
    assert out["would_prepare"] is True
