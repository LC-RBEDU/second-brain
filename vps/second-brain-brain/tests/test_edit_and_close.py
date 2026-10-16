"""Body edit stays unwritten without confirm. Closing the last task only suggests the story."""
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
from app.tools import close_task as close_mod  # noqa: E402
from app.tools import edit_task_body as edit_mod  # noqa: E402
from app.tools.task_catalog import file_hash  # noqa: E402

PATH = "02-PROJEKTY/it-ai-data/tasks/IAD-T1 — Krok.md"
STORY = "02-PROJEKTY/it-ai-data/tasks/IAD-S1 — Story.md"


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *a):
        return False


def _md(body: str, *, task_id: str = "IAD-T1", status: str = "Next", parent: str = "[[IAD-S1 — Story]]", typ: str = "task") -> str:
    return (
        f"---\nid: {task_id}\ntype: {typ}\ntitle: Krok\nslug: it-ai-data\n"
        f"status: {status}\nparent: \"{parent}\"\nfocus: 2026-W42\n---\n{body}"
    )


def test_edit_without_confirm_does_not_write():
    text = _md("\nřádek log_append: None\n\n## Poznámky / log\n")
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "oid1"
    vault.read_text.return_value = (text, meta)
    with patch.object(edit_mod, "brain_vault", return_value=_CM(vault)):
        out = edit_mod.edit_task_body(
            path=PATH,
            operation="delete_line",
            match="řádek log_append: None",
            source="Saturnin",
            reason="smazat prázdný log",
        )
    assert out["written"] is False
    vault.write_text.assert_not_called()


def test_edit_confirm_writes_when_hash_matches():
    text = _md("\nřádek log_append: None\n\n## Poznámky / log\n")
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "oid1"
    vault.read_text.return_value = (text, meta)
    meta2 = MagicMock()
    meta2.oid = "oid2"
    vault.write_text.return_value = meta2
    with patch.object(edit_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(edit_mod, "delete_context_tombstone"):
            out = edit_mod.edit_task_body(
                path=PATH,
                operation="delete_line",
                match="řádek log_append: None",
                expected_hash=file_hash(text),
                confirm=True,
                source="Saturnin",
                reason="smazat prázdný log",
            )
    assert out["written"] is True
    written = vault.write_text.call_args.args[1]
    assert "log_append: None" not in written
    assert "Saturnin" in written


def test_close_last_task_suggests_parent_and_leaves_story():
    task_text = _md("\n- [ ] **IAD-T1-1** krok\n")
    story = SimpleNamespace(
        frontmatter={"id": "IAD-S1", "type": "story", "title": "Story", "status": "Doing", "slug": "it-ai-data", "parent": ""},
        body="\n- [x] hotovo\n",
        rel_path=STORY,
    )
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "oid1"
    vault.read_text.return_value = (task_text, meta)
    meta2 = MagicMock()
    meta2.oid = "oid2"
    vault.write_text.return_value = meta2
    with patch.object(close_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(close_mod, "load_tasks", return_value=[story]):
            with patch.object(close_mod, "delete_context_tombstone"):
                out = close_mod.close_task(
                    path=PATH,
                    resolution="done",
                    source="Saturnin",
                    reason="hotovo",
                )
    assert out["suggest_close_parent"] is True
    assert out["open_siblings"] == 0
    assert out["parent_story"] == "IAD-S1"
    written = vault.write_text.call_args.args[1]
    assert "status: Done" in written
    assert STORY not in vault.write_text.call_args.args[0]


def test_close_story_with_open_child_is_rejected():
    story_text = _md("", task_id="IAD-S1", typ="story", parent="")
    child = SimpleNamespace(
        frontmatter={"id": "IAD-T1", "type": "task", "title": "Krok", "status": "Next", "slug": "it-ai-data", "parent": "[[IAD-S1 — Story]]"},
        body="",
        rel_path=PATH,
    )
    vault = MagicMock()
    meta = MagicMock()
    vault.read_text.return_value = (story_text, meta)
    with patch.object(close_mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(close_mod, "load_tasks", return_value=[child]):
            with patch.object(close_mod, "delete_context_tombstone"):
                with pytest.raises(BrainClientError) as ei:
                    close_mod.close_task(path=STORY, resolution="done", source="Saturnin", reason="zavřít")
    assert ei.value.error_reason == "parent_has_open_children"
    vault.write_text.assert_not_called()
