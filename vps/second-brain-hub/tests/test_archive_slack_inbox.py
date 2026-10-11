"""T4 / B6 — archive_slack_inbox CAS + dry-run + attachments."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "lib"))

from drive_io import DriveConflictError  # noqa: E402
from git_io import GitVault  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "archive_slack_inbox", HUB / "cron" / "archive_slack_inbox.py"
)
assert _SPEC and _SPEC.loader
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def vault_root(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    inbox = root / "01-INBOX" / "slack"
    inbox.mkdir(parents=True)
    (inbox / "2026-10-09_dm-test_1_v1.md").write_text("# note\n", encoding="utf-8")
    (inbox / "2026-10-09_dm-test_1_v1__1-image.png").write_bytes(b"png")
    (inbox / "2026-10-09_orphan.bin").write_bytes(b"x")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    monkeypatch.setenv("VAULT_BACKEND", "git")
    monkeypatch.setenv("GIT_VAULT_ROOT", str(root))
    monkeypatch.setenv("GIT_VAULT_PUSH", "0")
    return root


def test_dry_run_zero_write(vault_root: Path):
    before = {p.name for p in (vault_root / "01-INBOX" / "slack").iterdir()}
    result = mod.archive_slack_inbox(dry_run=True)
    assert result["dry_run"] is True
    after = {p.name for p in (vault_root / "01-INBOX" / "slack").iterdir()}
    assert before == after
    assert not (vault_root / "07-ARCHIV").exists() or not list(
        (vault_root / "07-ARCHIV").rglob("*")
    )


def test_happy_md_att_orphan(vault_root: Path):
    result = mod.archive_slack_inbox(dry_run=False)
    assert result["moved"] == 3
    assert not (vault_root / "01-INBOX" / "slack" / "2026-10-09_dm-test_1_v1.md").exists()
    dest_dir = vault_root / "07-ARCHIV" / "inbox-processed" / "2026" / "10" / "slack"
    assert (dest_dir / "2026-10-09_dm-test_1_v1.md").exists()
    assert (dest_dir / "2026-10-09_dm-test_1_v1__1-image.png").exists()
    assert (dest_dir / "2026-10-09_orphan.bin").exists()
    assert not (vault_root / "01-INBOX" / "slack" / "2026-10-09_orphan.bin").exists()


def test_cas_conflict_skips(vault_root: Path, monkeypatch):
    """Wrong oid path: move with stale oid leaves src."""
    vault = GitVault(vault_root, dry_run=False, push=False)
    with vault:
        meta = vault.stat("01-INBOX/slack/2026-10-09_dm-test_1_v1.md")
        (vault_root / "01-INBOX" / "slack" / "2026-10-09_dm-test_1_v1.md").write_text(
            "changed\n", encoding="utf-8"
        )
        with pytest.raises(DriveConflictError):
            vault.move(
                "01-INBOX/slack/2026-10-09_dm-test_1_v1.md",
                "07-ARCHIV/inbox-processed/2026/10/slack/2026-10-09_dm-test_1_v1.md",
                expect_oid=meta.oid,
            )
    assert (vault_root / "01-INBOX" / "slack" / "2026-10-09_dm-test_1_v1.md").exists()
