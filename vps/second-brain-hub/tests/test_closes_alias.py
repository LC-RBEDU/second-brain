"""Closes of an old checkbox id follows the alias window."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from github_rbu_closes import classify_ref, resolve_closes_target  # noqa: E402

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
