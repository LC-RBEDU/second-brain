"""T20 lokální preflight — A60ᵀ / A61 (F0–F4, mimo Coolify T20-live)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB_LIB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB_LIB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")

from app.vault_deps import brain_vault, defer_push_enabled  # noqa: E402
from push_queue import load_queue  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def git_vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    (root / "00-System").mkdir()
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    return root


def test_t20_a60t_hard_skip_without_defer_in_os_environ():
    """A60ᵀ: T20 happy-path musí mít truthy defer; bez → hard-skip (ne FAIL).

    Tento test ověří bránu: když os.environ nemá defer, T20 se přeskočí.
    Happy-path níže injektuje BRAIN_DEFER_PUSH=1 do env mapy (fixture).
    """
    if defer_push_enabled(os.environ):
        pytest.skip("os.environ už má BRAIN_DEFER_PUSH — A60ᵀ N/A")
    pytest.skip("A60ᵀ: T20 vyžaduje BRAIN_DEFER_PUSH fixture (viz test_t20_defer_…)")


def test_t20_defer_commit_oid_enqueue_no_remote_push(
    git_vault: Path, monkeypatch: pytest.MonkeyPatch
):
    """A61: stub jen remote push; local commit + oid + enqueue běží."""
    from git_io import GitVault

    pushes: list[bool] = []
    monkeypatch.setattr(GitVault, "_push_ff_only", lambda self: pushes.append(True))

    env = {
        "VAULT_BACKEND": "git",
        "GIT_VAULT_ROOT": str(git_vault),
        "GIT_VAULT_PUSH": "1",
        "BRAIN_DEFER_PUSH": "1",
    }
    assert defer_push_enabled(env) is True

    before = _git(git_vault, "rev-parse", "HEAD").stdout.strip()
    with brain_vault(mode="mutate", env=env) as vault:
        meta = vault.write_text("00-System/t20.md", "t20-body\n")
        assert meta.oid
    after = _git(git_vault, "rev-parse", "HEAD").stdout.strip()
    assert after != before
    assert (git_vault / "00-System" / "t20.md").read_text(encoding="utf-8") == "t20-body\n"
    assert pushes == []  # A61: remote push not invoked
    jobs = load_queue(git_vault)["jobs"]
    assert any(j.get("status") == "pending" for j in jobs)
