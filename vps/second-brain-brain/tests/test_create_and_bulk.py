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


def test_append_step_on_story_creates_a_file_after_the_anchor():
    from app.tools import append_task_note as append_mod

    vault = _vault()
    story = (
        "---\nid: RBU-S1\ntype: story\nslug: rb-universe-development\nstatus: Next\n---\n"
        "## Operativní kroky\n"
    )
    anchor = '{"applied_at": "2026-10-16"}\n'
    meta = MagicMock()

    def _read(path):
        if path.endswith("task-promotion-applied.json"):
            return anchor, meta
        if path == "02-PROJEKTY/RB Universe.md":
            return "---\ntype: project\nslug: rb-universe-development\n---\n", meta
        return story, meta

    hub = MagicMock()
    hub.name = "RB Universe.md"
    hub.rel_path = "02-PROJEKTY/RB Universe.md"
    hub.is_folder = False

    def _list(path, pattern=None, recursive=False, include_folders=False):
        if path == "02-PROJEKTY":
            return [hub]
        return []

    vault.read_text.side_effect = _read
    vault.list_dir.side_effect = _list
    with patch.object(append_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(append_mod, "peek_ids", create=True):
            pass
    with patch.object(append_mod, "brain_vault", return_value=_CM(vault)):
        with patch("app.tools.append_task_note.peek_ids", create=True) as peek:
            peek.return_value = [("RBU40", "t")]
            # peek is imported inside the function
            with patch("task_id_allocate.peek_ids", return_value=[("RBU40", "t")]):
                out = append_mod.append_task_note(
                    path="02-PROJEKTY/rb-universe-development/tasks/RBU-S1 — Story.md",
                    text="Nový krok",
                    target="step",
                    dry_run=True,
                )
    assert out["created"] == "RBU-T40"
    assert out["parent"] == "RBU-S1"
    assert out["written"] is False
    vault.write_text.assert_not_called()


def test_append_request_defaults_dry_run_off():
    from app.main import AppendTaskBody

    plain = AppendTaskBody(path="02-PROJEKTY/x/tasks/a.md", text="krok", target="step")
    preview = AppendTaskBody(path="02-PROJEKTY/x/tasks/a.md", text="krok", target="step", dry_run=True)
    assert plain.dry_run is False
    assert preview.dry_run is True


def _hub(slug: str = "rb-universe-development") -> MagicMock:
    hub = MagicMock()
    hub.name = "RB Universe.md"
    hub.rel_path = "02-PROJEKTY/RB Universe.md"
    hub._slug = slug
    return hub


def _bind_hub(vault: MagicMock, slug: str = "rb-universe-development") -> None:
    hub = _hub(slug)

    def _list(path, pattern=None, recursive=False, include_folders=False):
        if path == "02-PROJEKTY":
            return [hub]
        return []

    def _read(path):
        if path == hub.rel_path:
            return f"---\ntype: project\nslug: {slug}\n---\n", MagicMock()
        return "", MagicMock()

    vault.list_dir.side_effect = _list
    vault.read_text.side_effect = _read


def test_unknown_project_is_rejected():
    vault = _vault()
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            create_mod.create_task(slug="auto-superb", title="Krok", level="task", dry_run=True)
    assert ei.value.error_reason == "unknown_project"
    vault.write_text.assert_not_called()
    vault.mkdir_p.assert_not_called()


def test_story_without_parent_is_rejected():
    vault = _vault()
    _bind_hub(vault)
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            create_mod.create_task(slug="rb-universe-development", title="Krok", level="story", dry_run=True)
    assert ei.value.error_reason == "parent_required"
    assert ei.value.detail["errors"] == ["parent_required"]
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


def test_create_deadline_after_parent_writes_nothing():
    vault = _vault()
    parent = (
        "---\nid: RBU-S1\ntype: story\nslug: rb-universe-development\n"
        "status: Next\ndeadline: 2026-10-10\n---\n"
    )
    meta = MagicMock()
    meta.rel_path = "02-PROJEKTY/rb-universe-development/tasks/RBU-S1 — Story.md"
    vault.list_dir.return_value = [meta]
    vault.read_text.return_value = (parent, meta)
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(create_mod, "peek_ids", return_value=[("RBU30", "t")]):
            with pytest.raises(BrainClientError) as ei:
                create_mod.create_task(
                    slug="rb-universe-development",
                    title="Pozdě",
                    level="task",
                    parent="RBU-S1",
                    deadline="2026-10-20",
                )
    assert ei.value.error_reason == "deadline_order"
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


def test_b29_waiting_without_waituntil_does_not_open_the_vault():
    vault = _vault()
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)) as opened:
        with pytest.raises(BrainClientError) as ei:
            create_mod.create_task(
                slug="rb-universe-development",
                title="Cekam",
                status="Waiting",
            )
    assert ei.value.error_reason == "waiting_no_waituntil"
    opened.assert_not_called()
    vault.mkdir_p.assert_not_called()


def test_b13_deadline_clears_review_and_waiting_keeps_its_date():
    from tests.test_hierarchy_contract import _update, _vault as mem_vault

    vault = mem_vault(("finance", "Finance"))
    dated = "02-PROJEKTY/finance/tasks/F-T1.md"
    waiting = "02-PROJEKTY/finance/tasks/F-T2.md"
    vault.add(
        dated,
        "---\nid: F-T1\ntype: task\ntitle: F-T1\nslug: finance\nstatus: Next\n"
        "parent:\ndeadline:\nreview_deadline: 2026-11-01\n---\n",
    )
    vault.add(
        waiting,
        "---\nid: F-T2\ntype: task\ntitle: F-T2\nslug: finance\nstatus: Waiting\n"
        "parent:\nwaitUntil: 2026-11-02\n---\n",
    )
    _update(vault, dated, {"deadline": "2026-12-01"})
    written = vault.files[dated]
    assert "2026-12-01" in written
    assert "2026-11-01" not in written
    with pytest.raises(BrainClientError) as ei:
        _update(vault, waiting, {"waitUntil": ""})
    assert ei.value.error_reason == "waiting_no_waituntil"
    assert "title: F-T2" in vault.files[waiting]
    _update(vault, waiting, {"title": "Novy nazev"})
    assert "Novy nazev" in vault.files[waiting]


def test_b14_and_b33_create_keeps_detail_and_drops_review_when_deadline_is_set():
    from tests.test_hierarchy_contract import _create, _vault as mem_vault

    vault = mem_vault(("finance", "Finance"))
    preview = _create(
        vault,
        slug="finance",
        title="Cekam",
        level="epic",
        status="Waiting",
        waitUntil="2026-11-02",
        detail="poznamka",
        dry_run=True,
    )
    assert preview["id"]
    assert preview["dry_run"] is True
    assert not any("Cekam" in text for text in vault.files.values())
    before = set(vault.files)
    _create(
        vault,
        slug="finance",
        title="S terminem",
        level="epic",
        detail="poznamka",
        deadline="2026-12-01",
        review_deadline="2026-11-01",
        peeks=[("RBU41", "t")],
    )
    created = [text for path, text in vault.files.items() if path not in before]
    assert len(created) == 1
    assert "poznamka" in created[0]
    assert "2026-12-01" in created[0]
    assert "2026-11-01" not in created[0]


def test_b50_archived_done_parent_is_not_a_deadline_bridge():
    from tests.test_hierarchy_contract import _update, _vault as mem_vault

    vault = mem_vault(("finance", "Finance"))
    vault.add(
        "07-ARCHIV/tasks-done/finance/F-S1.md",
        "---\nid: F-S1\ntype: story\ntitle: F-S1\nslug: finance\nstatus: Done\n"
        "deadline: 2026-10-01\n---\n",
    )
    child = "02-PROJEKTY/finance/tasks/F-T1.md"
    vault.add(
        child,
        "---\nid: F-T1\ntype: task\ntitle: F-T1\nslug: finance\nstatus: Next\n"
        'parent: "[[F-S1]]"\ndeadline:\n---\n',
    )
    _update(vault, child, {"deadline": "2026-12-01"})
    assert "2026-12-01" in vault.files[child]


def test_b52_done_parent_still_in_tasks_blocks_a_later_child_deadline():
    from tests.test_hierarchy_contract import _update, _vault as mem_vault

    vault = mem_vault(("finance", "Finance"))
    vault.add(
        "02-PROJEKTY/finance/tasks/F-S1.md",
        "---\nid: F-S1\ntype: story\ntitle: F-S1\nslug: finance\nstatus: Done\n"
        "deadline: 2026-10-01\n---\n",
    )
    child = "02-PROJEKTY/finance/tasks/F-T1.md"
    original = (
        "---\nid: F-T1\ntype: task\ntitle: F-T1\nslug: finance\nstatus: Next\n"
        'parent: "[[F-S1]]"\ndeadline:\n---\n'
    )
    vault.add(child, original)
    with pytest.raises(BrainClientError) as ei:
        _update(vault, child, {"deadline": "2026-12-01"})
    assert ei.value.error_reason == "deadline_order"
    assert ei.value.detail["conflicts"]
    assert vault.files[child] == original
