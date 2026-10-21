"""Tests for lib/git_io.GitVault (temp git repos, no network)."""
from __future__ import annotations

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
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    # Fake origin so fetch does not need network (local bare remote).
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    return root


def test_cas_oid_conflict(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        text, meta = vault.read_text("README.md")
        assert meta.oid
        (git_repo / "README.md").write_text("externally changed\n", encoding="utf-8")
        with pytest.raises(DriveConflictError):
            vault.write_text("README.md", "new\n", expect_oid=meta.oid)


def test_cas_oid_passes(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        _, meta = vault.read_text("README.md")
        out = vault.write_text("README.md", "updated\n", expect_oid=meta.oid)
        assert out.oid
        assert (git_repo / "README.md").read_text(encoding="utf-8") == "updated\n"


def test_dirty_skip_at_start_no_reset(git_repo: Path):
    from git_io import VaultSessionSkipped

    (git_repo / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        assert vault.skipped is True
        assert vault.skip_reason == "vault_dirty_start"
        with pytest.raises(VaultSessionSkipped) as excinfo:
            vault.write_text("00-System/x.md", "nope\n")
        assert excinfo.value.skip_reason == "vault_dirty_start"
        assert not (git_repo / "00-System" / "x.md").exists()
    cmds = [" ".join(c) for c in vault._git_cmds]
    assert not any("reset --hard" in c and "@{upstream}" not in c for c in cmds)
    assert not any(c.endswith("reset --hard HEAD") or "reset --hard HEAD" in c for c in cmds)
    # Dirty file still there (no clean/reset on start).
    assert (git_repo / "dirty.txt").exists()


def test_flock_timeout_skips_session(git_repo: Path):
    """B4: held flock → skipped; mutate raises (no silent write)."""
    import fcntl
    import threading
    import time

    from git_io import LOCK_NAME, VaultSessionSkipped

    lock_path = git_repo / ".git" / LOCK_NAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    holder = open(lock_path, "a+", encoding="utf-8")
    fcntl.flock(holder.fileno(), fcntl.LOCK_EX)

    def release_later() -> None:
        time.sleep(0.3)
        fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
        holder.close()

    threading.Thread(target=release_later, daemon=True).start()
    vault = GitVault(git_repo, dry_run=False, push=False, flock_timeout=0.1)
    with vault:
        assert vault.skipped is True
        assert vault.skip_reason == "vault_flock_busy"
        with pytest.raises(VaultSessionSkipped) as excinfo:
            vault.write_text("held.md", "x\n")
        assert excinfo.value.skip_reason == "vault_flock_busy"
    assert not (git_repo / "held.md").exists()


def test_empty_commit_not_created(git_repo: Path):
    before = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        assert vault.skipped is False
        # read-only session
        vault.read_text("README.md")
    after = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    assert before == after
    log = _git(git_repo, "log", "--oneline").stdout.strip().splitlines()
    assert len(log) == 1


def test_commit_when_dirty(git_repo: Path):
    before = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        vault.write_text("00-System/a.md", "x\n")
    after = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    assert before != after
    assert (git_repo / "00-System" / "a.md").read_text(encoding="utf-8") == "x\n"


def test_dirty_only_push_mock(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    pushes: list[bool] = []

    def fake_push(self):  # noqa: ANN001
        pushes.append(True)

    monkeypatch.setattr(GitVault, "_push_ff_only", fake_push)

    # Clean session → no push
    vault = GitVault(git_repo, dry_run=False, push=True)
    with vault:
        vault.read_text("README.md")
    assert pushes == []

    # Dirty session → push once
    vault2 = GitVault(git_repo, dry_run=False, push=True)
    with vault2:
        vault2.write_text("00-System/b.md", "y\n")
    assert pushes == [True]


def test_push_ff_reject_keep_tip_no_reset(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    vault = GitVault(git_repo, dry_run=False, push=True, on_push_fail="keep_tip")
    real_git = GitVault._git

    def flaky_git(self, args, **kwargs):  # noqa: ANN001
        if args[:3] == ["-c", "push.ff=only", "push"] or args[:2] == [
            "push",
            "--ff-only",
        ]:
            return subprocess.CompletedProcess(args, 1, "", "rejected")
        return real_git(self, args, **kwargs)

    monkeypatch.setattr(GitVault, "_git", flaky_git)
    with vault:
        vault.write_text("00-System/keep.md", "z\n")
    cmds = [" ".join(c) for c in vault._git_cmds]
    assert not any("reset --hard @{upstream}" in c for c in cmds)


def test_push_ff_reject_resets_upstream(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    vault = GitVault(git_repo, dry_run=False, push=True, on_push_fail="reset")
    real_git = GitVault._git

    def flaky_git(self, args, **kwargs):  # noqa: ANN001
        if args[:3] == ["-c", "push.ff=only", "push"] or args[:2] == [
            "push",
            "--ff-only",
        ]:
            return subprocess.CompletedProcess(args, 1, "", "rejected")
        return real_git(self, args, **kwargs)

    monkeypatch.setattr(GitVault, "_git", flaky_git)
    with vault:
        vault.write_text("00-System/c.md", "z\n")
    cmds = [" ".join(c) for c in vault._git_cmds]
    assert any("reset --hard @{upstream}" in c for c in cmds)


def test_strict_push_raises_after_reset_ok(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    from git_io import GitPushError

    vault = GitVault(
        git_repo, dry_run=False, push=True, strict_push=True, on_push_fail="reset"
    )
    real_git = GitVault._git

    def flaky_git(self, args, **kwargs):  # noqa: ANN001
        if args[:3] == ["-c", "push.ff=only", "push"] or args[:2] == [
            "push",
            "--ff-only",
        ]:
            return subprocess.CompletedProcess(args, 1, "", "rejected")
        return real_git(self, args, **kwargs)

    monkeypatch.setattr(GitVault, "_git", flaky_git)
    with pytest.raises(GitPushError) as excinfo:
        with vault:
            vault.write_text("00-System/strict.md", "z\n")
    assert excinfo.value.error_reason == "vault_push_reset_ok"


def test_mkdir_alias_equals_mkdir_p(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    assert GitVault.mkdir is GitVault.mkdir_p
    assert vault.mkdir.__func__ is vault.mkdir_p.__func__
    with vault:
        p = vault.mkdir("07-ARCHIV/inbox-processed")
        assert Path(p).is_dir()
        again = vault.mkdir_p("07-ARCHIV/inbox-processed")
        assert Path(again).is_dir()


def test_dry_run_no_wt_write(git_repo: Path):
    before = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    vault = GitVault(git_repo, dry_run=True, push=True)
    with vault:
        meta = vault.write_text("00-System/dry.md", "would\n")
        assert meta.rel_path == "00-System/dry.md"
        assert not (git_repo / "00-System" / "dry.md").exists()
        vault.mkdir("00-System/newdir")
        assert not (git_repo / "00-System" / "newdir").exists()
    after = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    assert before == after
    cmds = [" ".join(c) for c in vault._git_cmds]
    assert not any(" commit " in f" {c} " or c.endswith("commit") or "commit -m" in c for c in cmds)
    assert not any("push" in c for c in cmds)


def test_missing_git_raises_clear_error(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError, match="no .git"):
        GitVault(empty, dry_run=True, push=False)


def test_ensure_clone_refused_in_dry_run(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    vault = GitVault(
        empty,
        remote="git@example.com:org/repo.git",
        dry_run=True,
        push=False,
        require_git=False,
    )
    with pytest.raises(RuntimeError, match="refuse auto-clone"):
        vault.ensure_clone()


def test_blob_oid_matches_hash_object_without_subprocess(git_repo: Path):
    """T8 — in-process blob id equals git hash-object; hash-object is not spawned."""
    from git_io import git_blob_oid

    data = b"abc\n\0\xff"
    proc = subprocess.run(
        ["git", "hash-object", "--stdin"],
        input=data,
        capture_output=True,
        check=True,
    )
    expected = proc.stdout.decode().strip()
    assert git_blob_oid(data, "sha1") == expected
    vault = GitVault(git_repo, dry_run=True, push=False)
    assert vault._blob_oid_for_bytes(data) == expected
    sample = git_repo / "oid-sample.txt"
    sample.write_bytes(data)
    assert vault._blob_oid_for_path(sample) == expected
    assert not any("hash-object" in arg for cmd in vault._git_cmds for arg in cmd)


def test_sha256_blob_oid_matches_hash_object(tmp_path: Path):
    root = tmp_path / "sha"
    _git(tmp_path, "init", "--object-format=sha256", "-b", "main", str(root))
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    data = b"sha-256 sample\n"
    (root / "README.md").write_bytes(data)
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    proc = subprocess.run(
        ["git", "hash-object", "--stdin"],
        input=data,
        cwd=str(root),
        capture_output=True,
        check=True,
    )
    expected = proc.stdout.decode().strip()
    assert len(expected) == 64
    from git_io import git_blob_oid

    assert git_blob_oid(data, "sha256") == expected
    vault = GitVault(root, dry_run=True, push=False)
    assert vault._object_format() == "sha256"
    assert vault._blob_oid_for_bytes(data) == expected
    assert vault._blob_oid_for_path(root / "README.md") == expected
    assert not any("hash-object" in arg for cmd in vault._git_cmds for arg in cmd)


def test_parse_log_name_only_splits_lf_inside_nul_chunks():
    """C2 — NUL splits commits; LF splits paths; quoted/octal lines drop."""
    from git_io import _parse_log_name_only_z

    em = "02-PROJEKTY/alpha/tasks/X1 — Nadpis.md"
    assert _parse_log_name_only_z(em + "\n") == {em}
    assert _parse_log_name_only_z(em + "\0") == {em}
    assert _parse_log_name_only_z(em + "\r\n") == {em}
    multi = "02-PROJEKTY/alpha/tasks/A.md\n02-PROJEKTY/alpha/tasks/B.md\n"
    assert _parse_log_name_only_z(multi) == {
        "02-PROJEKTY/alpha/tasks/A.md",
        "02-PROJEKTY/alpha/tasks/B.md",
    }
    nul_multi = "02-PROJEKTY/alpha/tasks/A.md\x0002-PROJEKTY/alpha/tasks/B.md\x00"
    assert _parse_log_name_only_z(nul_multi) == {
        "02-PROJEKTY/alpha/tasks/A.md",
        "02-PROJEKTY/alpha/tasks/B.md",
    }
    quoted = '"02-PROJEKTY/alpha/tasks/X1 \\342\\200\\224 Nadpis.md"\n'
    assert _parse_log_name_only_z(quoted) == set()
    weird = "02-PROJEKTY/alpha/tasks/X\u2028Y.md\n"
    assert _parse_log_name_only_z(weird) == {"02-PROJEKTY/alpha/tasks/X\u2028Y.md"}
    assert _parse_log_name_only_z("README.md\n") == set()
    assert _parse_log_name_only_z("") == set()


def test_filemeta_oid_and_folder_mime(git_repo: Path):
    vault = GitVault(git_repo, dry_run=False, push=False)
    with vault:
        vault.mkdir_p("folder")
        meta = vault.stat("folder")
        assert meta.is_folder is True
        assert meta.oid is None
        _, fmeta = vault.read_text("README.md")
        assert fmeta.oid
        assert len(fmeta.oid) == 40
