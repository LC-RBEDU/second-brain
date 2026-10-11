"""T12 — prepare_meeting degrade + force with mocked vault."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.tools import prepare_meeting as mod  # noqa: E402


class _FakeVault:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def exists(self, rel: str) -> bool:
        return rel in self.files

    def mkdir_p(self, rel: str) -> None:
        return None

    def write_text(self, rel: str, body: str, **_kw) -> None:
        self.files[rel] = body


def test_degraded_without_universe_drive():
    vault = _FakeVault()

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch.object(mod, "brain_vault", return_value=_CM()):
        out = mod.prepare_meeting(
            "e1",
            title="X",
            starts_at="2026-10-11T12:00:00",
            deliver=False,
            dry_run=False,
            env={},
        )
    assert out["written"] is True
    assert out["degraded_flag"] is True
    assert "universe" in out["degraded"]
    assert "drive" in out["degraded"]


def test_force_overwrites():
    vault = _FakeVault()
    vault.files["00-System/Meeting-Preps/e1-2026-10-11.md"] = "old"

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch.object(mod, "brain_vault", return_value=_CM()):
        skip = mod.prepare_meeting(
            "e1", starts_at="2026-10-11T12:00:00", deliver=False, force=False, env={}
        )
        forced = mod.prepare_meeting(
            "e1", starts_at="2026-10-11T12:00:00", deliver=False, force=True, env={}
        )
    assert skip["skipped"] is True
    assert forced["written"] is True
