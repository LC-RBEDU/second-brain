"""B24: schedule/cancel fail on git-clone vault; list OK."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "schedule_reminder.py"


@pytest.fixture()
def git_vault(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / ".git").mkdir()
    pending = root / "00-System" / "Reminders-Pending"
    pending.mkdir(parents=True)
    return root


def test_schedule_fails_on_git_clone(git_vault: Path):
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(git_vault)}
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "schedule",
            "--at",
            "2099-01-01 08:00",
            "--message",
            "test",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "git" in (r.stderr + r.stdout).lower() or "READONLY" in (r.stderr + r.stdout)


def test_list_ok_on_git_clone(git_vault: Path):
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(git_vault)}
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "list"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0


def test_cancel_fails_on_git_clone(git_vault: Path):
    pending = git_vault / "00-System" / "Reminders-Pending"
    rem = {
        "id": "2099-01-01-0800-rem-test",
        "status": "pending",
        "deliver_at": "2099-01-01T08:00:00+01:00",
        "message": "x",
    }
    (pending / "2099-01-01-0800-rem-test.json").write_text(
        json.dumps(rem), encoding="utf-8"
    )
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(git_vault)}
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "cancel", "rem-test"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert (pending / "2099-01-01-0800-rem-test.json").exists()


def test_schedule_ok_without_git(tmp_path: Path):
    root = tmp_path / "obsidian"
    root.mkdir()
    env = {**os.environ, "SECOND_BRAIN_VAULT": str(root)}
    # clear readonly if set in parent env
    env.pop("SECOND_BRAIN_VAULT_READONLY", None)
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "schedule",
            "--at",
            "2099-01-01 09:00",
            "--message",
            "ok",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert list((root / "00-System" / "Reminders-Pending").glob("*.json"))
