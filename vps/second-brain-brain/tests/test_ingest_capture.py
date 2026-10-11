"""T2 — ingest_sembly + capture_daily via mocked brain_vault."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.tools import capture_daily as capture_mod  # noqa: E402
from app.tools import ingest_sembly as ingest_mod  # noqa: E402


class _FakeVault:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.mkdirs: list[str] = []

    def exists(self, rel: str) -> bool:
        return rel in self.files

    def mkdir_p(self, rel: str) -> None:
        self.mkdirs.append(rel)

    def write_text(self, rel: str, body: str, **_kw) -> None:
        self.files[rel] = body

    def read_text(self, rel: str):
        return self.files[rel], MagicMock(oid="x")


def test_ingest_write_and_dedupe():
    vault = _FakeVault()

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    payload = {
        "id": "meet-1",
        "meeting": {
            "title": "Sync",
            "start_time": "2026-10-11T10:00:00",
            "participants": [],
        },
        "summary": "hi",
        "transcript": "t",
    }
    with patch.object(ingest_mod, "brain_vault", return_value=_CM()):
        r1 = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
        r2 = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
    assert r1["deduped"] is False
    assert r1["path"].startswith("01-INBOX/sembly/")
    assert r2["deduped"] is True
    assert "hi" in next(iter(vault.files.values()))


def test_capture_daily_path():
    vault = _FakeVault()

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch.object(capture_mod, "brain_vault", return_value=_CM()):
        out = capture_mod.capture_daily("poznámka", title="Test", env={"TZ": "Europe/Prague"})
    assert out["path"].startswith("01-INBOX/daily/")
    assert "poznámka" in vault.files[out["path"]]
