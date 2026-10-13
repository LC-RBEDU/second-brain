"""T5/T6 — filename collision + key dedupe for ingest_sembly."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.tools import ingest_sembly as ingest_mod  # noqa: E402


class _FakeVault:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def exists(self, rel: str) -> bool:
        return rel in self.files

    def mkdir_p(self, rel: str) -> None:
        return None

    def write_text(self, rel: str, body: str, **_kw) -> None:
        self.files[rel] = body

    def read_text(self, rel: str):
        return self.files[rel], MagicMock(oid="x")


def _cm(vault: _FakeVault):
    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    return _CM()


def test_two_meetings_same_unknown_filename_both_write():
    vault = _FakeVault()
    p1 = {"meeting_id": "m1", "meeting_title": "meeting", "meeting_transcription": "a"}
    p2 = {"meeting_id": "m2", "meeting_title": "meeting", "meeting_transcription": "b"}
    p3 = {"meeting_id": "m3", "meeting_title": "meeting", "meeting_transcription": "c"}
    with patch.object(ingest_mod, "brain_vault", return_value=_cm(vault)):
        r1 = ingest_mod.ingest_sembly(p1, env={"GIT_VAULT_PUSH": "1"})
        r2 = ingest_mod.ingest_sembly(p2, env={"GIT_VAULT_PUSH": "1"})
        r3 = ingest_mod.ingest_sembly(p3, env={"GIT_VAULT_PUSH": "1"})
    assert r1["deduped"] is False
    assert r2["deduped"] is False
    assert r3["deduped"] is False
    assert r1["path"] == "01-INBOX/sembly/unknown-time-meeting.md"
    assert r2["path"] == "01-INBOX/sembly/unknown-time-meeting-m2.md"
    assert r3["path"] == "01-INBOX/sembly/unknown-time-meeting-m3.md"
    assert "a" in vault.files[r1["path"]]
    assert "b" in vault.files[r2["path"]]
    assert "c" in vault.files[r3["path"]]


def test_collision_suffix_increments_when_key12_path_taken():
    vault = _FakeVault()
    # Pre-seed colliding stem-key12 path so third write must use -2
    vault.files["01-INBOX/sembly/unknown-time-meeting.md"] = "old"
    vault.files["01-INBOX/sembly/unknown-time-meeting-m9.md"] = "taken"
    p = {"meeting_id": "m9", "meeting_title": "meeting", "meeting_transcription": "x"}
    with patch.object(ingest_mod, "brain_vault", return_value=_cm(vault)):
        r = ingest_mod.ingest_sembly(p, env={"GIT_VAULT_PUSH": "1"})
    assert r["deduped"] is False
    assert r["path"] == "01-INBOX/sembly/unknown-time-meeting-m9-2.md"
    assert "x" in vault.files[r["path"]]


def test_same_meeting_id_dedupes_via_key():
    vault = _FakeVault()
    payload = {
        "meeting_id": "same-1",
        "meeting_title": "Sync",
        "meeting_started_at": "2026-10-13T10:00:00",
        "meeting_transcription": "t",
    }
    with patch.object(ingest_mod, "brain_vault", return_value=_cm(vault)):
        r1 = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
        r2 = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
    assert r1["deduped"] is False
    assert r2["deduped"] is True
    assert r2["path"] == r1["path"]


def test_unsafe_meeting_id_sanitized():
    vault = _FakeVault()
    payload = {
        "meeting_id": "id/with spaces!",
        "meeting_title": "X",
        "meeting_started_at": "2026-10-13T10:00:00",
    }
    with patch.object(ingest_mod, "brain_vault", return_value=_cm(vault)):
        r = ingest_mod.ingest_sembly(payload, env={"GIT_VAULT_PUSH": "1"})
    assert r["deduped"] is False
    assert "/" not in r["idempotency_key"]
    assert " " not in r["idempotency_key"]
    assert f"01-INBOX/sembly/.keys/{r['idempotency_key']}.path" in vault.files
