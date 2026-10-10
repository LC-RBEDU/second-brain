"""Tests for lib/vault_factory.open_vault."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB_DIR))

from vault_factory import VaultPausedError, open_vault  # noqa: E402


def test_paused_raises_on_write_and_delete():
    inner = MagicMock()
    with patch("vault_factory._flag", return_value=True):
        # Build paused wrapper via open_vault git path with mocked GitVault
        with patch.dict(
            "os.environ",
            {"VAULT_BACKEND": "git", "VAULT_WRITERS_PAUSED": "1", "GIT_VAULT_ROOT": "/tmp"},
            clear=False,
        ):
            pass

    from vault_factory import _PausedVault

    paused = _PausedVault(inner)
    with pytest.raises(VaultPausedError, match="write_text"):
        paused.write_text("a.md", "x")
    with pytest.raises(VaultPausedError, match="delete"):
        paused.delete("a.md")
    with pytest.raises(VaultPausedError, match="mkdir_p"):
        paused.mkdir_p("dir")
    with pytest.raises(VaultPausedError, match="move"):
        paused.move("a.md", "b.md")
    # reads still forwarded
    inner.read_text.return_value = ("ok", None)
    assert paused.read_text("a.md")[0] == "ok"


def test_paused_via_open_vault_git(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    import subprocess

    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.com"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "T"], cwd=root, check=True, capture_output=True
    )
    (root / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "i"], cwd=root, check=True, capture_output=True
    )

    env = {
        "VAULT_BACKEND": "git",
        "VAULT_WRITERS_PAUSED": "1",
        "GIT_VAULT_ROOT": str(root),
        "GIT_VAULT_DRY_RUN": "0",
        "GIT_VAULT_PUSH": "0",
    }
    vault = open_vault(env=env)
    with pytest.raises(VaultPausedError):
        vault.write_text("x.md", "no")
    with pytest.raises(VaultPausedError):
        vault.delete("README.md")
    # read still works
    text, _ = vault.read_text("README.md")
    assert text == "x\n"


def test_default_drive_needs_env():
    env = {"VAULT_BACKEND": "drive"}  # no VAULT_DRIVE_ID
    with pytest.raises(RuntimeError, match="VAULT_DRIVE_ID"):
        open_vault(env=env)


def test_default_backend_is_drive():
    env = {"VAULT_DRIVE_ID": "root123"}
    fake_creds = object()
    with patch("drive_io.credentials_from_env", return_value=(fake_creds, "oauth")) as creds_fn:
        with patch("drive_io.DriveVault") as DV:
            DV.return_value = MagicMock(name="drive_vault")
            vault = open_vault(env=env)
            creds_fn.assert_called_once_with(env)
            DV.assert_called_once_with("root123", credentials=fake_creds)
            assert vault is DV.return_value


def test_drive_context_manager():
    from drive_io import DriveVault

    # Trivial enter/exit without real API
    v = DriveVault("root", service=MagicMock())
    with v as entered:
        assert entered is v


def test_unknown_backend():
    with pytest.raises(ValueError, match="Unknown VAULT_BACKEND"):
        open_vault(env={"VAULT_BACKEND": "s3"})
