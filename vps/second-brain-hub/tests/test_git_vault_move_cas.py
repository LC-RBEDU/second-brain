"""B28 / T20 — GitVault.move CAS (expect_oid)."""
from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import pytest

_LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB_DIR))

from drive_io import DriveConflictError  # noqa: E402
from git_io import GitVault  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    inbox = root / "01-INBOX" / "slack"
    inbox.mkdir(parents=True)
    (inbox / "note.md").write_text("hello\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    return root


def test_move_signature_has_expect_oid():
    sig = inspect.signature(GitVault.move)
    assert "expect_oid" in sig.parameters
    assert "expect_mtime" in sig.parameters


def test_move_cas_happy(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        meta = vault.stat("01-INBOX/slack/note.md")
        assert meta.oid
        out = vault.move(
            "01-INBOX/slack/note.md",
            "07-ARCHIV/inbox-processed/2026/10/slack/note.md",
            expect_oid=meta.oid,
        )
        assert out.rel_path.endswith("note.md")
        assert not (git_repo / "01-INBOX" / "slack" / "note.md").exists()
        assert (git_repo / "07-ARCHIV" / "inbox-processed" / "2026" / "10" / "slack" / "note.md").exists()


def test_move_cas_conflict(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        meta = vault.stat("01-INBOX/slack/note.md")
        (git_repo / "01-INBOX" / "slack" / "note.md").write_text(
            "changed\n", encoding="utf-8"
        )
        with pytest.raises(DriveConflictError):
            vault.move(
                "01-INBOX/slack/note.md",
                "07-ARCHIV/inbox-processed/2026/10/slack/note.md",
                expect_oid=meta.oid,
            )
        assert (git_repo / "01-INBOX" / "slack" / "note.md").exists()
