"""finalize_meeting: dry-run, archive, collisions, frontmatter fence."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.errors import BrainClientError  # noqa: E402
from app.tools import finalize_meeting as mod  # noqa: E402

ZAPIS = """---
type: material
material_kind: schuzka
doc_type: meeting_summary
title: Finance Sync
meeting_date: '2026-10-13'
participants:
- Lukáš
variant: full
---
Hello transcript note.
---
still in the body
"""

TRANSCRIPT = "01-INBOX/sembly/2026-10-13-1000-finance.md"


class _Vault:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.tracked: set[str] = set()
        self.writes: list[str] = []
        self.mode = "mutate"
        self.head = "aaa"

    def exists(self, rel: str) -> bool:
        return rel in self.files

    def read_text(self, rel: str):
        return self.files[rel], SimpleNamespace(oid=f"oid-{rel}")

    def write_text(self, rel: str, body: str, **_kw) -> None:
        self.writes.append(rel)
        self.files[rel] = body

    def delete(self, rel: str, **_kw) -> None:
        self.files.pop(rel, None)

    def move(self, src: str, dst: str, **_kw) -> None:
        self.files[dst] = self.files.pop(src)

    def is_tracked(self, rel: str) -> bool:
        return rel in self.tracked

    def list_dir(self, rel: str, **_kw):
        prefix = rel.rstrip("/") + "/"
        out = []
        for path in self.files:
            if path.startswith(prefix) and "/" not in path[len(prefix) :]:
                out.append(SimpleNamespace(name=path.rsplit("/", 1)[-1]))
        return out

    def mkdir_p(self, _rel: str) -> None:
        return None

    def head_sha(self) -> str:
        return self.head


def _cm(vault: _Vault, mode: str):
    class _CM:
        def __enter__(self):
            vault.mode = mode
            return vault

        def __exit__(self, *a):
            if vault.writes:
                vault.head = "bbb"
            return False

    return _CM()


def _patch(vault: _Vault):
    def _open(*, mode, env=None):
        return _cm(vault, mode)

    return patch.object(mod, "brain_vault", side_effect=_open)


def test_dry_run_writes_nothing():
    vault = _Vault()
    vault.files[TRANSCRIPT] = "the meeting said hello"
    vault.tracked.add(TRANSCRIPT)
    with _patch(vault):
        result = mod.finalize_meeting(
            transcript_path=TRANSCRIPT, zapis_md=ZAPIS, dry_run=True, env={}
        )
    assert result["dry_run"] is True
    assert result["would_write"] is True
    assert result["commit"] is None
    assert result["zapis_path"].endswith("2026-10-13_finance-sync_zapis.md")
    assert TRANSCRIPT in vault.files
    assert vault.writes == []
    assert vault.mode == "read"


def test_apply_archives_and_keeps_body_fence():
    vault = _Vault()
    vault.files[TRANSCRIPT] = "the meeting said hello"
    vault.tracked.add(TRANSCRIPT)
    with _patch(vault):
        result = mod.finalize_meeting(transcript_path=TRANSCRIPT, zapis_md=ZAPIS, env={})
    assert TRANSCRIPT not in vault.files
    archived = vault.files[result["archive_path"]]
    assert archived.startswith("**ZPRACOVÁNO**")
    assert "the meeting said hello" in archived
    saved = vault.files[result["zapis_path"]]
    assert "still in the body" in saved
    assert saved.count("\n---\n") >= 1


def test_skip_keeps_transcript_text():
    vault = _Vault()
    vault.files[TRANSCRIPT] = "smoke only line"
    vault.tracked.add(TRANSCRIPT)
    with _patch(vault):
        result = mod.finalize_meeting(
            transcript_path=TRANSCRIPT, skip_reason="smoke", env={}
        )
    assert result["zapis_path"] is None
    text = vault.files[result["archive_path"]]
    assert "skip_reason: smoke" in text
    assert "smoke only line" in text


def test_missing_fence_is_400():
    vault = _Vault()
    vault.files[TRANSCRIPT] = "x"
    vault.tracked.add(TRANSCRIPT)
    with _patch(vault):
        with pytest.raises(BrainClientError) as exc:
            mod.finalize_meeting(transcript_path=TRANSCRIPT, zapis_md="no fence", env={})
    assert exc.value.error_reason == "bad_frontmatter"
    assert TRANSCRIPT in vault.files


def test_other_without_note_is_400():
    with pytest.raises(BrainClientError) as exc:
        mod.finalize_meeting(transcript_path=TRANSCRIPT, skip_reason="other", env={})
    assert exc.value.error_reason == "skip_note_required"
