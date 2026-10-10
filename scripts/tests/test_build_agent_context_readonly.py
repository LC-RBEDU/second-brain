"""B23: Mac build_agent_context fails write on git clone; dry-run OK."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "build_agent_context.py"


def test_write_fails_on_git_clone(tmp_path: Path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".git").mkdir()
    (vault / "00-System").mkdir()
    (vault / "02-PROJEKTY").mkdir()
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(vault)}
    env.pop("SECOND_BRAIN_VAULT_READONLY", None)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "git" in r.stderr.lower() or "READONLY" in r.stderr or "klon" in r.stderr.lower()


def test_dry_run_ok_on_git_clone(tmp_path: Path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".git").mkdir()
    (vault / "00-System").mkdir()
    (vault / "02-PROJEKTY").mkdir()
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(vault)}
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
