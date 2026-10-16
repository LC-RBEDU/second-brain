"""find_tasks and the 90-day checkbox alias."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from task_query import find_tasks, resolve_task, tree_for  # noqa: E402

APPLIED = date(2026, 10, 1)
INSIDE = date(2026, 10, 16)
OUTSIDE = date(2027, 1, 1)


def _task(**fm):
    body = fm.pop("body", "")
    path = fm.pop("path", "02-PROJEKTY/finance/tasks/x.md")
    return SimpleNamespace(frontmatter=fm, body=body, rel_path=path)


def test_find_matches_title_or_body_and_returns_deadline():
    tasks = [
        _task(id="F-S87", title="Saurusmedia", status="Next", type="story", slug="finance", deadline="2026-11-01", body="nic"),
        _task(id="F-S1", title="Jiné", status="Next", type="story", slug="finance", body="Saurusmedia v těle"),
    ]
    rows = find_tasks(tasks, query="Saurusmedia", alias="inactive")
    assert [row["id"] for row in rows] == ["F-S87", "F-S1"]
    assert rows[0]["deadline"] == "2026-11-01"


def test_old_checkbox_id_resolves_only_inside_the_window():
    task = _task(id="IAD-T9", title="Krok", status="Next", type="task", promoted_from="IAD-S55-1", slug="it-ai-data")
    found, resolved, error = resolve_task([task], "IAD-S55-1", applied_at=APPLIED, today=INSIDE)
    assert error is None and resolved == "IAD-S55-1" and found.frontmatter["id"] == "IAD-T9"
    _task_out, _res, expired = resolve_task([task], "IAD-S55-1", applied_at=APPLIED, today=OUTSIDE)
    assert expired == "alias_expired"
    direct, resolved_direct, error_direct = resolve_task([task], "IAD-T9", applied_at=None, today=INSIDE)
    assert error_direct is None and resolved_direct is None and direct is task


def test_checkbox_alias_without_anchor_is_inactive_even_when_the_file_exists():
    task = _task(id="IAD-T9", title="Krok", status="Next", type="task", promoted_from="IAD-S55-1", slug="it-ai-data")
    _found, _resolved, error = resolve_task([task], "IAD-S55-1", applied_at=None, today=INSIDE)
    assert error == "alias_inactive"


def test_tree_counts_open_descendants():
    tasks = [
        _task(id="E1", title="Epic", status="Doing", type="epic", slug="finance"),
        _task(id="S1", title="Story", status="Next", type="story", slug="finance", parent="[[E1 — Epic]]"),
        _task(id="T1", title="Task", status="Next", type="task", slug="finance", parent="[[S1 — Story]]", deadline="2026-10-20"),
    ]
    tree = tree_for(tasks, "E1")
    assert tree is not None
    assert tree["open_descendants"] == 2
    assert tree["children"][0]["id"] == "S1"
    assert tree["children"][0]["open_descendants"] == 1
