"""Bulk expect_oid is collected, and a mid-loop conflict is 409 with failures."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.errors import BrainClientError  # noqa: E402
from app.tools import bulk_update as bulk_mod  # noqa: E402
from drive_io import DriveConflictError  # noqa: E402
from tests.test_hierarchy_contract import MemVault, _CM, _seed, _vault  # noqa: E402


def test_b8_all_oid_mismatches_are_returned_and_nothing_is_written():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "C-A", "task")
    _seed(vault, "finance", "C-2", "task")
    _seed(vault, "finance", "C-10", "task")
    before = dict(vault.files)
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as one:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "expect_oid": "oid", "patch": {"title": "a"}},
                    {"id": "C-2", "expect_oid": "stale", "patch": {"title": "b"}},
                    {"id": "C-10", "expect_oid": "oid", "patch": {"title": "c"}},
                ],
                dry_run=True,
            )
    assert one.value.status_code == 409
    assert len(one.value.detail["failures"]) == 1
    assert one.value.detail["failures"][0]["id"] == "C-2"
    assert one.value.detail["failures"][0]["oid"] == "oid"
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as both:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "expect_oid": "oid", "patch": {"title": "a"}},
                    {"id": "C-2", "expect_oid": "stale", "patch": {"title": "b"}},
                    {"id": "C-10", "expect_oid": "other", "patch": {"title": "c"}},
                ]
            )
    ids = [item["id"] for item in both.value.detail["failures"]]
    assert ids == ["C-10", "C-2"]
    assert vault.files == before


def test_b10_partial_oid_is_rejected():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "C-A", "task")
    _seed(vault, "finance", "C-2", "task")
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        out = bulk_mod.bulk_update(
            updates=[
                {"id": "C-A", "patch": {"title": "a"}},
                {"id": "C-2", "patch": {"title": "b"}},
            ],
            dry_run=True,
        )
    assert out["count"] == 2
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "expect_oid": "oid", "patch": {"title": "a"}},
                    {"id": "C-2", "patch": {"title": "b"}},
                ],
                dry_run=True,
            )
    assert ei.value.error_reason == "missing_expect_oid"


def test_b9_write_conflict_is_409_with_failures():
    class _ConflictVault(MemVault):
        def write_text(self, path: str, text: str, **kwargs):
            if path.endswith("C-2.md"):
                raise DriveConflictError("race", oid="oid-new")
            return super().write_text(path, text, **kwargs)

    vault = _ConflictVault()
    vault.add("02-PROJEKTY/Finance.md", "---\ntype: project\nslug: finance\n---\n")
    _seed(vault, "finance", "C-A", "task")
    _seed(vault, "finance", "C-2", "task")
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "expect_oid": "oid", "patch": {"title": "a"}},
                    {"id": "C-2", "expect_oid": "oid", "patch": {"title": "b"}},
                ]
            )
    assert ei.value.status_code == 409
    assert ei.value.error_reason == "oid_mismatch"
    assert ei.value.detail["failures"] == [
        {"id": "C-2", "path": "02-PROJEKTY/finance/tasks/C-2.md", "oid": "oid-new"}
    ]
    assert ei.value.oid is None


def test_b9_real_session_puts_the_first_file_back_on_head(tmp_path):
    root = tmp_path / "vault"
    first = root / "02-PROJEKTY/finance/tasks/C-A.md"
    second = root / "02-PROJEKTY/finance/tasks/C-2.md"
    first.parent.mkdir(parents=True)
    body = "---\nid: {id}\ntype: task\ntitle: {id}\nslug: finance\nstatus: Next\nparent:\ndeadline:\n---\n"
    first.write_text(body.format(id="C-A"), encoding="utf-8")
    second.write_text(body.format(id="C-2"), encoding="utf-8")
    git = ["git", "-C", str(root), "-c", "user.email=brain@local", "-c", "user.name=Brain"]
    subprocess.run([*git, "init", "-b", "main"], check=True, capture_output=True)
    subprocess.run([*git, "add", "."], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-m", "seed"], check=True, capture_output=True)
    subprocess.run([*git, "remote", "add", "origin", str(root)], check=True, capture_output=True)
    subprocess.run([*git, "update-ref", "refs/remotes/origin/main", "HEAD"], check=True, capture_output=True)
    subprocess.run([*git, "branch", "--set-upstream-to=origin/main"], check=True, capture_output=True)
    original = first.read_text(encoding="utf-8")
    from git_io import GitVault

    original_write = GitVault.write_text

    def _race(self, rel, text, **kwargs):
        if str(rel).endswith("C-2.md"):
            raise DriveConflictError("race", oid="oid-new")
        return original_write(self, rel, text, **kwargs)

    env = {
        "GIT_VAULT_ROOT": str(root),
        "GIT_VAULT_PUSH": "1",
        "GIT_VAULT_REMOTE": "",
        "GIT_AUTHOR_NAME": "Brain",
        "GIT_AUTHOR_EMAIL": "brain@local",
    }
    with patch.object(GitVault, "write_text", _race):
        with pytest.raises(BrainClientError) as ei:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "patch": {"title": "a"}},
                    {"id": "C-2", "patch": {"title": "b"}},
                ],
                env=env,
            )
    assert ei.value.status_code == 409
    assert ei.value.detail["failures"][0]["id"] == "C-2"
    assert first.read_text(encoding="utf-8") == original


def test_b15_mcp_oid_mismatch_is_a_call_tool_result():
    from mcp.types import CallToolResult

    from app.mcp_app import build_mcp

    tool = build_mcp()._tool_manager.get_tool("bulk_update")
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "C-A", "task")
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        before_write = tool.fn(
            updates_json=json.dumps(
                [{"id": "C-A", "expect_oid": "stale", "patch": {"title": "a"}}]
            )
        )
    assert isinstance(before_write, CallToolResult)
    assert before_write.is_error is True
    assert json.loads(before_write.content[0].text)["error_reason"] == "oid_mismatch"

    class _ConflictVault(MemVault):
        def write_text(self, path: str, text: str, **kwargs):
            if path.endswith("C-2.md"):
                raise DriveConflictError("race", oid="oid-new")
            return super().write_text(path, text, **kwargs)

    racing = _ConflictVault()
    racing.add("02-PROJEKTY/Finance.md", "---\ntype: project\nslug: finance\n---\n")
    _seed(racing, "finance", "C-A", "task")
    _seed(racing, "finance", "C-2", "task")
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(racing)):
        during_write = tool.fn(
            updates_json=json.dumps(
                [
                    {"id": "C-A", "expect_oid": "oid", "patch": {"title": "a"}},
                    {"id": "C-2", "expect_oid": "oid", "patch": {"title": "b"}},
                ]
            )
        )
    assert isinstance(during_write, CallToolResult)
    assert during_write.is_error is True
    assert json.loads(during_write.content[0].text)["error_reason"] == "oid_mismatch"


def test_batch_caps():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "C-A", "task")
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as dup:
            bulk_mod.bulk_update(
                updates=[
                    {"id": "C-A", "patch": {"title": "a"}},
                    {"id": "C-A", "patch": {"title": "b"}},
                ],
                dry_run=True,
            )
    assert dup.value.error_reason == "duplicate_id"
    with pytest.raises(BrainClientError) as big:
        bulk_mod.bulk_update(
            updates=[{"id": f"X{i}", "patch": {"title": "a"}} for i in range(81)],
            dry_run=True,
        )
    assert big.value.error_reason == "batch_too_large"
