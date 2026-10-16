"""Closes of an old checkbox id follows the alias window."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from github_rbu_closes import apply_close_action, classify_ref, resolve_closes_target  # noqa: E402

SLUG = "rb-universe-development"


def _file(**fm):
    return SimpleNamespace(frontmatter={"slug": SLUG, **fm}, body="", rel_path="t.md")


def test_active_alias_closes_the_task_file_not_the_story():
    story = _file(id="RBU-S7", type="story", status="Doing")
    child = _file(id="RBU-T12", type="task", status="Next", promoted_from="RBU-S7-1")
    found, promoted = resolve_closes_target(classify_ref("RBU-S7-1"), [story, child], alias="active")
    assert promoted is True
    assert found.frontmatter["id"] == "RBU-T12"


def test_expired_alias_does_not_close_the_story():
    story = _file(id="RBU-S7", type="story", status="Doing")
    child = _file(id="RBU-T12", type="task", status="Next", promoted_from="RBU-S7-1")
    assert resolve_closes_target(classify_ref("RBU-S7-1"), [story, child], alias="expired") is None


def test_expired_alias_still_checks_a_micro_step_on_the_task_file():
    story = _file(id="RBU-S7", type="story", status="Doing")
    child = _file(id="RBU-T12", type="task", status="Next", promoted_from="RBU-S7-1")
    found, promoted = resolve_closes_target(classify_ref("RBU-T12-1"), [story, child], alias="expired")
    assert promoted is False
    assert found.frontmatter["id"] == "RBU-T12"


def test_micro_step_is_checked_without_closing_the_parent(monkeypatch):
    task = _file(id="RBU-T12", type="task", status="Next")
    task.body = "- [ ] **RBU-T12-1** krok\n- [ ] **RBU-T12-2** další\n"
    task.is_terminal = False
    seen: dict = {}

    def _update(_vault, item, **kwargs):
        seen["status"] = kwargs.get("new_status")
        seen["body"] = item.body
        return True

    monkeypatch.setattr("github_rbu_closes.update_task", _update)
    result, _detail = apply_close_action(None, task, classify_ref("RBU-T12-1"), today_str="2026-10-16")
    assert result == "applied"
    assert "- [x] **RBU-T12-1**" in seen["body"]
    assert seen["status"] is None


def test_missing_checkbox_does_not_mark_the_story_done(monkeypatch):
    story = _file(id="RBU-S7", type="story", status="Doing")
    story.body = "- [x] **RBU-S7-2** hotovo\n"
    story.is_terminal = False
    calls: list[dict] = []
    monkeypatch.setattr(
        "github_rbu_closes.update_task",
        lambda *args, **kwargs: calls.append(kwargs) or True,
    )
    result, _detail = apply_close_action(None, story, classify_ref("RBU-S7-1"), today_str="2026-10-16")
    assert result == "noop"
    assert calls == []
