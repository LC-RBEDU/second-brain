"""Hierarchy create needs a parent. Bulk focus and a bad deadline write nothing."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.errors import BrainClientError  # noqa: E402
from app.tools import bulk_update as bulk_mod  # noqa: E402
from app.tools import create_task as create_mod  # noqa: E402


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *a):
        return False


def _vault() -> MagicMock:
    vault = MagicMock()
    vault.list_dir.return_value = []
    return vault


def test_hierarchy_task_without_parent_is_rejected():
    vault = _vault()
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            create_mod.create_task(slug="rb-universe-development", title="Krok", level="task", dry_run=True)
    assert ei.value.error_reason == "parent_required"
    vault.write_text.assert_not_called()


def test_dry_run_batch_returns_distinct_ids():
    vault = _vault()
    story = "---\nid: RBU-S1\ntype: story\nslug: rb-universe-development\nstatus: Next\n---\n"
    meta = MagicMock()

    def _read(path):
        return story, meta

    vault.read_text.side_effect = _read
    file_meta = MagicMock()
    file_meta.rel_path = "02-PROJEKTY/rb-universe-development/tasks/RBU-S1 — Story.md"
    vault.list_dir.return_value = [file_meta]
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(create_mod, "peek_ids", return_value=[("RBU20", "t"), ("RBU21", "t")]):
            out = create_mod.create_task(
                slug="rb-universe-development",
                dry_run=True,
                items=[
                    {"title": "První", "level": "task", "parent": "RBU-S1"},
                    {"title": "Druhý", "level": "task", "parent": "RBU-S1"},
                ],
            )
    assert [item["id"] for item in out["created"]] == ["RBU-T20", "RBU-T21"]
    vault.write_text.assert_not_called()


def test_bulk_focus_writes_nothing():
    with pytest.raises(BrainClientError) as ei:
        bulk_mod.bulk_update(updates=[{"id": "RBU-T1", "patch": {"focus": "2026-W42"}}])
    assert ei.value.error_reason == "focus_requires_proposal"


def test_bulk_deadline_conflict_writes_nothing():
    parent = SimpleNamespace(
        frontmatter={"id": "RBU-E1", "type": "epic", "status": "Doing", "deadline": "2026-10-20", "parent": None, "slug": "rb-universe-development"},
        body="",
        rel_path="02-PROJEKTY/rb-universe-development/tasks/RBU-E1.md",
    )
    child = SimpleNamespace(
        frontmatter={"id": "RBU-T1", "type": "task", "status": "Next", "deadline": "2026-10-18", "parent": "[[RBU-E1]]", "slug": "rb-universe-development"},
        body="",
        rel_path="02-PROJEKTY/rb-universe-development/tasks/RBU-T1.md",
    )
    vault = MagicMock()
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(bulk_mod, "load_tasks", return_value=[parent, child]):
            with pytest.raises(BrainClientError) as ei:
                bulk_mod.bulk_update(updates=[{"id": "RBU-E1", "patch": {"deadline": "2026-10-10"}}])
    assert ei.value.error_reason == "deadline_order"
    vault.write_text.assert_not_called()
