"""Bulk expect_oid is collected, and a mid-loop conflict is 409 with failures."""
from __future__ import annotations

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
