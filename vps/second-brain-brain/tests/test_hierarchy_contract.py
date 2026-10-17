"""Cross-project hierarchy contract. Fake vault, no live write."""
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
from app.tools import append_task_note as append_mod  # noqa: E402
from app.tools import bulk_update as bulk_mod  # noqa: E402
from app.tools import close_task as close_mod  # noqa: E402
from app.tools import create_task as create_mod  # noqa: E402
from app.tools import update_task as update_mod  # noqa: E402
from drive_io import DriveNotFoundError  # noqa: E402


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *args):
        return False


class _Meta:
    def __init__(self, rel: str, is_folder: bool = False):
        self.rel_path = rel
        self.name = rel.rstrip("/").split("/")[-1]
        self.is_folder = is_folder
        self.oid = "oid"


class MemVault:
    def __init__(self):
        self.files: dict[str, str] = {}
        self.mkdirs: list[str] = []

    def exists(self, _path: str) -> bool:
        return False

    def add(self, path: str, text: str) -> None:
        self.files[path] = text

    def read_text(self, path: str):
        if path not in self.files:
            raise DriveNotFoundError(path)
        return self.files[path], _Meta(path)

    def write_text(self, path: str, text: str, **_kwargs):
        self.files[path] = text
        return _Meta(path)

    def mkdir_p(self, path: str) -> None:
        self.mkdirs.append(path)

    def list_dir(self, path, pattern=None, recursive=False, include_folders=False):
        prefix = path.rstrip("/") + "/"
        seen: dict[str, tuple[str, str]] = {}
        for rel in self.files:
            if not rel.startswith(prefix):
                continue
            rest = rel[len(prefix):]
            if "/" in rest and not recursive:
                if include_folders:
                    folder = rest.split("/")[0]
                    seen[folder] = ("dir", prefix + folder)
                continue
            name = rest.split("/")[-1]
            if pattern == "*.md" and not name.endswith(".md"):
                continue
            seen[rest] = ("file", rel)
        return [_Meta(rel, kind == "dir") for kind, rel in seen.values()]


def _hub(slug: str, stem: str, quoted: bool = False) -> str:
    value = f'"{slug}"' if quoted else slug
    return f"---\ntype: project\nslug: {value}\n---\n"


def _task(task_id: str, work_type: str, slug: str, status: str = "Next", parent: str = "", deadline: str = "", body: str = "\n") -> str:
    parent_line = f'parent: "{parent}"\n' if parent else "parent:\n"
    deadline_line = f"deadline: {deadline}\n" if deadline else "deadline:\n"
    return (
        f"---\nid: {task_id}\ntype: {work_type}\ntitle: {task_id}\nslug: {slug}\n"
        f"status: {status}\n{parent_line}{deadline_line}---\n{body}"
    )


def _path(slug: str, task_id: str) -> str:
    return f"02-PROJEKTY/{slug}/tasks/{task_id}.md"


def _vault(*hubs: tuple[str, str], quoted: bool = False) -> MemVault:
    vault = MemVault()
    for slug, stem in hubs:
        vault.add(f"02-PROJEKTY/{stem}.md", _hub(slug, stem, quoted=quoted))
    return vault


def _seed(vault: MemVault, slug: str, task_id: str, work_type: str, **kwargs) -> str:
    path = _path(slug, task_id)
    vault.add(path, _task(task_id, work_type, slug, **kwargs))
    return path


def _create(vault: MemVault, **kwargs):
    peeks = kwargs.pop("peeks", [("RBU40", "t")])
    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(create_mod, "peek_ids", return_value=peeks):
            return create_mod.create_task(**kwargs)


def _update(vault: MemVault, path: str, changes: dict, dry_run: bool = False):
    with patch.object(update_mod, "brain_vault", return_value=_CM(vault)):
        return update_mod.update_task(path=path, patch=changes, dry_run=dry_run)


def _bulk(vault: MemVault, updates: list, dry_run: bool = False):
    with patch.object(bulk_mod, "brain_vault", return_value=_CM(vault)):
        return bulk_mod.bulk_update(updates=updates, dry_run=dry_run)


def _written_new(vault: MemVault, before: set[str]) -> list[str]:
    return [text for path, text in vault.files.items() if path not in before]


def test_quoted_slug_on_a_later_frontmatter_line_writes_the_hub_stem():
    vault = _vault(("finance", "Finance"), quoted=True)
    before = set(vault.files)
    _create(vault, slug="finance", title="Epic", level="epic")
    created = _written_new(vault, before)
    assert len(created) == 1
    assert 'project: "[[Finance]]"' in created[0]
    assert "ice_i: 5" in created[0]
    assert "**RBU-E40-1**" in created[0]


def test_slug_only_in_the_body_is_unknown():
    vault = MemVault()
    vault.add("02-PROJEKTY/Finance.md", "---\ntype: project\n---\nslug: finance\n")
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Epic", level="epic", dry_run=True)
    assert ei.value.error_reason == "unknown_project"
    assert vault.mkdirs == []


def test_two_hubs_with_the_same_slug_are_ambiguous():
    vault = _vault(("finance", "Finance"), ("finance", "Finance-ops"))
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Epic", level="epic", dry_run=True)
    assert ei.value.error_reason == "hub_ambiguous"


def test_list_dir_failure_is_unknown_project():
    vault = _vault(("finance", "Finance"))

    def _boom(*_args, **_kwargs):
        raise RuntimeError("down")

    vault.list_dir = _boom
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Epic", level="epic", dry_run=True)
    assert ei.value.error_reason == "unknown_project"
    assert vault.mkdirs == []


def test_epic_with_a_parent_writes_nothing():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "RBU-E1", "epic")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Dalsi", level="epic", parent="RBU-E1")
    assert ei.value.error_reason == "epic_has_no_parent"
    assert vault.files == before


def test_story_under_an_epic_in_another_project():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic")
    before = set(vault.files)
    out = _create(vault, slug="finance", title="Story", level="story", parent="OS-E1", peeks=[("F12", "t")])
    assert out["path"].startswith("02-PROJEKTY/finance/tasks/")
    body = vault.files[out["path"]]
    assert 'parent: "[[OS-E1]]"' in body
    assert "ice_i: 5" in body
    assert "**F-S12-1**" not in body


def test_story_under_a_story_is_rejected():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-S1", "story", parent="[[F-E1]]")
    _seed(vault, "finance", "F-E1", "epic")
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Dalsi", level="story", parent="F-S1", dry_run=True)
    assert ei.value.error_reason == "parent_not_epic"


def test_task_without_parent_has_no_ice_and_no_placeholder():
    vault = _vault(("rb-universe-development", "RB Universe"))
    before = set(vault.files)
    out = _create(vault, slug="rb-universe-development", title="Kus", level="task")
    body = vault.files[out["path"]]
    assert "ice_i" not in body
    assert "**RBU-T40-1**" not in body


def test_task_under_a_story_in_another_project():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-S1", "story", parent="[[OS-E1]]")
    _seed(vault, "osobni", "OS-E1", "epic")
    out = _create(vault, slug="finance", title="Kus", level="task", parent="OS-S1", peeks=[("F3", "t")])
    body = vault.files[out["path"]]
    assert 'parent: "[[OS-S1]]"' in body
    assert "parent_slug" not in body


def test_task_under_an_epic_is_rejected():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-E1", "epic")
    with pytest.raises(BrainClientError) as ei:
        _create(vault, slug="finance", title="Kus", level="task", parent="F-E1", dry_run=True)
    assert ei.value.error_reason == "parent_not_story"


def test_missing_archived_and_duplicate_and_unreadable_parent():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-E1", "epic")
    vault.add(_path("finance", "F-E1-copy"), _task("F-E1", "epic", "finance"))
    with pytest.raises(BrainClientError) as missing:
        _create(vault, slug="finance", title="S", level="story", parent="F-E9", dry_run=True)
    assert missing.value.error_reason == "parent_not_found"
    with pytest.raises(BrainClientError) as dup:
        _create(vault, slug="finance", title="S", level="story", parent="F-E1", dry_run=True)
    assert dup.value.error_reason == "parent_ambiguous"
    with pytest.raises(BrainClientError) as raw:
        _create(vault, slug="finance", title="Kus", level="task", parent="not an id", dry_run=True)
    assert raw.value.error_reason == "parent_not_found"


def test_done_parent_in_tasks_is_accepted_and_a_batch_does_not_see_itself():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-E1", "epic", status="Done")
    out = _create(vault, slug="finance", title="Story", level="story", parent="F-E1", peeks=[("F8", "t")])
    assert 'parent: "[[F-E1]]"' in vault.files[out["path"]]
    fresh = _vault(("finance", "Finance"))
    before = dict(fresh.files)
    with pytest.raises(BrainClientError) as ei:
        _create(
            fresh,
            slug="finance",
            peeks=[("F9", "t"), ("F10", "t")],
            items=[
                {"title": "Epic", "level": "epic"},
                {"title": "Story", "level": "story", "parent": "F-E9"},
            ],
        )
    assert ei.value.error_reason == "parent_not_found"
    assert fresh.files == before


def test_create_scans_active_tasks_once():
    vault = _vault(("finance", "Finance"))
    calls = {"n": 0}
    real = create_mod.iter_active_tasks

    def _once(inner):
        calls["n"] += 1
        return real(inner)

    with patch.object(create_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(create_mod, "peek_ids", return_value=[("F4", "t")]):
            with patch.object(create_mod, "iter_active_tasks", side_effect=_once):
                create_mod.create_task(
                    slug="finance",
                    title="Kus",
                    level="task",
                    deadline="2026-10-20",
                )
    assert calls["n"] == 1


def test_create_deadline_after_a_cross_project_ancestor_writes_nothing():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-S1", "story", parent="[[OS-E1]]", deadline="2026-10-10")
    _seed(vault, "osobni", "OS-E1", "epic", deadline="2026-10-10")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _create(
            vault,
            slug="finance",
            title="Pozde",
            level="task",
            parent="OS-S1",
            deadline="2026-10-20",
            peeks=[("F4", "t")],
        )
    assert ei.value.error_reason == "deadline_order"
    assert vault.files == before
    out = _create(
        vault,
        slug="finance",
        title="Stejny den",
        level="task",
        parent="OS-S1",
        deadline="2026-10-10",
        peeks=[("F5", "t")],
    )
    assert "deadline: 2026-10-10" in vault.files[out["path"]]


def test_update_moves_parent_across_projects_and_refuses_a_cleared_story_parent():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    task_path = _seed(vault, "finance", "F-T1", "task")
    _seed(vault, "osobni", "OS-S1", "story", parent="[[OS-E1]]")
    _seed(vault, "osobni", "OS-E1", "epic")
    _update(vault, task_path, {"parent": "OS-S1"})
    assert task_path in vault.files
    assert 'parent: "[[OS-S1]]"' in vault.files[task_path]
    story = _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]")
    original = vault.files[story]
    with pytest.raises(BrainClientError) as ei:
        _update(vault, story, {"parent": ""})
    assert ei.value.error_reason == "parent_required"
    assert vault.files[story] == original


def test_pure_done_skips_the_forest_and_a_bad_parent_on_done_does_not():
    vault = _vault(("finance", "Finance"))
    story = _seed(vault, "finance", "F-S1", "story")
    calls = {"n": 0}
    real = update_mod.iter_active_tasks

    def _once(inner):
        calls["n"] += 1
        return real(inner)

    with patch.object(update_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(update_mod, "iter_active_tasks", side_effect=_once):
            update_mod.update_task(path=story, patch={"status": "Done"})
    assert calls["n"] == 0
    assert "status: Done" in vault.files[story]
    task = _seed(vault, "finance", "F-T1", "task", parent="[[F-S9]]")
    original = vault.files[task]
    with pytest.raises(BrainClientError) as ei:
        _update(vault, task, {"status": "Done", "parent": "not an id"})
    assert ei.value.error_reason == "parent_not_found"
    assert vault.files[task] == original


def test_done_plus_deadline_still_uses_the_cone():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic", deadline="2026-10-10")
    story = _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]", deadline="2026-10-09")
    original = vault.files[story]
    with pytest.raises(BrainClientError) as ei:
        _update(vault, story, {"status": "Done", "deadline": "2026-10-20"})
    assert ei.value.error_reason == "deadline_order"
    assert vault.files[story] == original
    _update(vault, story, {"status": "Done", "deadline": "2026-10-10"})
    assert "deadline: 2026-10-10" in vault.files[story]
    assert "status: Done" in vault.files[story]


def test_type_change_without_an_epic_parent_is_rejected():
    vault = _vault(("finance", "Finance"))
    task = _seed(vault, "finance", "F-T1", "task")
    original = vault.files[task]
    with pytest.raises(BrainClientError) as ei:
        _update(vault, task, {"type": "story"})
    assert ei.value.error_reason == "parent_required"
    assert vault.files[task] == original


def test_duplicate_parent_on_update_writes_nothing():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-S1", "story", parent="[[F-E1]]")
    _seed(vault, "osobni", "F-S1", "story", parent="[[F-E1]]")
    # second file is under finance folder name osobni — put it in finance tasks via a second path
    vault.files.pop(_path("osobni", "F-S1"), None)
    vault.add(_path("finance", "F-S1-copy"), _task("F-S1", "story", "finance", parent="[[F-E1]]"))
    _seed(vault, "finance", "F-E1", "epic")
    task = _seed(vault, "finance", "F-T1", "task")
    original = vault.files[task]
    with pytest.raises(BrainClientError) as ei:
        _update(vault, task, {"parent": "F-S1"})
    assert ei.value.error_reason == "parent_ambiguous"
    assert vault.files[task] == original


def test_bulk_bad_parent_and_dry_run_write_nothing():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-T1", "task")
    _seed(vault, "finance", "F-T2", "task")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(
            vault,
            [
                {"id": "F-T1", "patch": {"parent": "missing"}},
                {"id": "F-T2", "patch": {"status": "Doing"}},
            ],
            dry_run=True,
        )
    assert ei.value.error_reason == "parent_not_found"
    assert vault.files == before


def test_story_to_epic_reports_both_reasons_and_writes_nothing():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic")
    _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]")
    _seed(vault, "osobni", "OS-T1", "task", parent="[[F-S1]]")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(vault, [{"id": "F-S1", "patch": {"type": "epic"}}])
    assert ei.value.error_reason == "epic_has_no_parent"
    assert ei.value.detail["errors"] == ["epic_has_no_parent", "parent_not_story"]
    assert "parent_not_story" in ei.value.message
    assert vault.files == before


def test_story_to_epic_with_cleared_parent_and_an_open_child():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic")
    _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]")
    _seed(vault, "osobni", "OS-T1", "task", parent="[[F-S1]]")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(vault, [{"id": "F-S1", "patch": {"type": "epic", "parent": ""}}])
    assert ei.value.detail["errors"] == ["parent_not_story"]
    assert vault.files == before


def test_story_to_epic_with_a_done_child_writes_only_the_story():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic")
    story = _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]")
    child = _seed(vault, "osobni", "OS-T1", "task", parent="[[F-S1]]", status="Done")
    child_before = vault.files[child]
    _bulk(vault, [{"id": "F-S1", "patch": {"type": "epic", "parent": ""}}])
    assert "type: epic" in vault.files[story]
    assert vault.files[child] == child_before


def test_bare_epic_conversion_with_only_done_children_is_one_reason():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-E0", "epic")
    _seed(vault, "finance", "F-S1", "story", parent="[[F-E0]]")
    _seed(vault, "finance", "F-T1", "task", parent="[[F-S1]]", status="Done")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(vault, [{"id": "F-S1", "patch": {"type": "epic"}}])
    assert ei.value.detail["errors"] == ["epic_has_no_parent"]
    assert vault.files == before


def test_combined_bulk_waking_a_child_returns_both_reasons_once():
    vault = _vault(("finance", "Finance"))
    _seed(vault, "finance", "F-E0", "epic")
    _seed(vault, "finance", "F-S1", "story", parent="[[F-E0]]")
    child = _seed(vault, "finance", "F-T1", "task", parent="[[F-S1]]", status="Done")
    before = dict(vault.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(
            vault,
            [
                {"id": "F-S1", "patch": {"type": "epic"}},
                {"id": "F-T1", "patch": {"status": "Next"}},
            ],
        )
    assert ei.value.error_reason == "epic_has_no_parent"
    assert ei.value.detail["errors"] == ["epic_has_no_parent", "parent_not_story"]
    assert ei.value.detail["errors"].count("parent_not_story") == 1
    assert vault.files == before
    later = _vault(("finance", "Finance"))
    _seed(later, "finance", "F-E0", "epic")
    _seed(later, "finance", "F-T1", "task", parent="[[F-E0]]")
    original = later.files[_path("finance", "F-T1")]
    with pytest.raises(BrainClientError) as later_err:
        _update(later, _path("finance", "F-T1"), {"status": "Next"})
    assert later_err.value.detail["errors"] == ["parent_not_story"]
    assert later.files[_path("finance", "F-T1")] == original
    assert child  # the first vault child stayed unused after the raise


def test_overlay_lets_a_task_become_an_epic_and_its_child_a_story():
    vault = _vault(("finance", "Finance"))
    parent = _seed(vault, "finance", "F-T1", "task")
    child = _seed(vault, "finance", "F-T2", "task", parent="[[F-T1]]")
    _bulk(
        vault,
        [
            {"id": "F-T1", "patch": {"type": "epic"}},
            {"id": "F-T2", "patch": {"type": "story"}},
        ],
    )
    assert "type: epic" in vault.files[parent]
    assert "type: story" in vault.files[child]
    blocked = _vault(("finance", "Finance"))
    _seed(blocked, "finance", "F-E0", "epic")
    _seed(blocked, "finance", "F-T1", "task", parent="[[F-E0]]")
    _seed(blocked, "finance", "F-T2", "task", parent="[[F-T1]]")
    before = dict(blocked.files)
    with pytest.raises(BrainClientError) as ei:
        _bulk(
            blocked,
            [
                {"id": "F-T1", "patch": {"type": "epic"}},
                {"id": "F-T2", "patch": {"type": "story"}},
            ],
        )
    assert ei.value.error_reason == "epic_has_no_parent"
    assert blocked.files == before


def test_sibling_deadline_outside_the_cone_does_not_block_a_write():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    _seed(vault, "osobni", "OS-E1", "epic", deadline="2026-10-10")
    _seed(vault, "osobni", "OS-S9", "story", parent="[[OS-E1]]", deadline="2026-10-20")
    task = _seed(vault, "finance", "F-T1", "task", parent="[[OS-E1]]", deadline="2026-10-09")
    _update(vault, task, {"deadline": "2026-10-10"})
    assert "deadline: 2026-10-10" in vault.files[task]


def test_append_child_stays_in_the_story_folder_and_uses_the_hub_stem():
    vault = _vault(("finance", "Finance"), ("finance-ops", "Finance-ops"))
    story = (
        "---\nid: F-S1\ntype: story\nslug: not-a-project\nstatus: Next\nparent: \"[[F-E1]]\"\n---\n"
        "## Operativní kroky\n"
    )
    vault.add(_path("finance", "F-S1"), story)
    vault.add("00-System/task-promotion-applied.json", '{"applied_at": "2026-10-16"}\n')
    with patch.object(append_mod, "brain_vault", return_value=_CM(vault)):
        with patch("task_id_allocate.peek_ids", return_value=[("F40", "t")]):
            out = append_mod.append_task_note(
                path=_path("finance", "F-S1"),
                text="Novy krok",
                target="step",
            )
    assert out["path"].startswith("02-PROJEKTY/finance/tasks/")
    assert "not-a-project" not in "".join(vault.mkdirs)
    body = vault.files[out["path"]]
    assert 'project: "[[Finance]]"' in body
    assert "[[Finance-ops]]" not in body


def test_append_unknown_folder_is_refused():
    vault = _vault(("finance", "Finance"))
    vault.add(
        "02-PROJEKTY/auto-superb/tasks/AS-S1.md",
        "---\nid: AS-S1\ntype: story\nslug: auto-superb\nstatus: Next\n---\n## Operativní kroky\n",
    )
    vault.add("00-System/task-promotion-applied.json", '{"applied_at": "2026-10-16"}\n')
    before = dict(vault.files)
    with patch.object(append_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            append_mod.append_task_note(
                path="02-PROJEKTY/auto-superb/tasks/AS-S1.md",
                text="Novy krok",
                target="step",
            )
    assert ei.value.error_reason == "unknown_project"
    assert vault.files == before


def test_close_sees_an_open_child_in_another_project_and_only_suggests_the_parent():
    vault = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    story = _seed(vault, "finance", "F-S1", "story", parent="[[OS-E1]]", body="## Operativní kroky\n- [x] hotovo\n")
    _seed(vault, "osobni", "OS-E1", "epic")
    _seed(vault, "osobni", "OS-T1", "task", parent="[[F-S1]]")
    before = vault.files[story]
    with patch.object(close_mod, "brain_vault", return_value=_CM(vault)):
        with pytest.raises(BrainClientError) as ei:
            close_mod.close_task(path=story, source="test", reason="hotovo")
    assert ei.value.error_reason == "parent_has_open_children"
    assert vault.files[story] == before
    lone = _vault(("finance", "Finance"), ("osobni", "Osobni"))
    parent = _seed(lone, "osobni", "OS-S1", "story", parent="[[OS-E1]]", body="## Operativní kroky\n- [x] hotovo\n")
    _seed(lone, "osobni", "OS-E1", "epic")
    child = _seed(lone, "finance", "F-T1", "task", parent="[[OS-S1]]", body="## Operativní kroky\n- [x] hotovo\n")
    parent_before = lone.files[parent]
    with patch.object(close_mod, "brain_vault", return_value=_CM(lone)):
        out = close_mod.close_task(path=child, source="test", reason="hotovo")
    assert out["suggest_close_parent"] is True
    assert lone.files[parent] == parent_before


def test_create_body_declares_parent():
    text = Path(_BRAIN / "app" / "main.py").read_text()
    assert "parent: str = \"\"" in text
