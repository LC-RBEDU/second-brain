"""Tests for agent-context light + charters projection."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from agent_context_light import (  # noqa: E402
    build_charters,
    parse_people_from_section,
    project_light,
    write_context_bundle,
)


PEOPLE_SECTION = """
| Kdo | Role |
|-----|------|
| **[[Lukáš Cypra]]** | Owner |
| **[[Dominik Holíček]]** | Finance ops |
| **[[Martina Mašková]]** | Účetní — via [[Finance]] |
"""


def test_parse_people_first_column_only():
    names = parse_people_from_section(PEOPLE_SECTION)
    assert names == ["Lukáš Cypra", "Dominik Holíček", "Martina Mašková"]
    assert "Finance" not in names


def _snapshot():
    return {
        "version": 2,
        "generated_at": "2026-09-10T16:08:50+02:00",
        "today": "2026-09-10",
        "stats": {"total_open_tasks": 2},
        "priority_rules": {"model": "v2"},
        "focus_week": "2026-W37",
        "projects": [
            {
                "slug": "finance",
                "title": "Finance",
                "status": "active",
                "aliases": ["finance"],
                "area": "[[03-AREAS/Finance a strategie]]",
                "open_tasks_count": 2,
                "updated": "2026-09-07",
                "charter_scope": "scope text",
                "charter_kontext": "kontext text",
                "charter_cil": "cil",
                "charter_definition_of_done": "dod",
                "charter_people": PEOPLE_SECTION,
                "hub_filename": "Finance.md",
            }
        ],
        "top_priority_today": [
            {
                "id": "F54",
                "slug": "finance",
                "status": "Next",
                "title": "Fix",
                "materials": ["[[a]]", "[[b]]"],
                "priority_score": 21.33,
            }
        ],
        "top_priority": [{"id": "F54", "slug": "finance", "status": "Next", "title": "Fix"}],
        "upcoming_deadlines": [],
        "focus_suggestions": [{"id": "F99", "slug": "finance", "status": "Next", "title": "Sug"}],
        "open_epics": [{"id": "F56", "slug": "finance", "type": "epic", "status": "Doing", "title": "Epic"}],
    }


def test_project_light_shape_and_ids():
    snap = _snapshot()
    open_tasks = [
        {
            "id": "F54",
            "slug": "finance",
            "type": "story",
            "parent": "F56",
            "status": "Next",
            "title": "Fix",
            "deadline": None,
            "waitUntil": None,
            "focus": None,
            "agent": "assist",
            "priority_score": 21.33,
            "updated": "2026-09-07",
            "materials": ["[[a]]", "[[b]]"],
            "blocked_by": [],
        },
        {
            "id": "F99",
            "slug": "finance",
            "type": "story",
            "parent": None,
            "status": "Waiting",
            "title": "Waiting side",
            "deadline": None,
            "priority_score": 5.0,
            "materials": [],
            "blocked_by": [],
        },
        {
            "id": "F56",
            "slug": "finance",
            "type": "epic",
            "status": "Doing",
            "title": "Epic",
            "priority_score": 1.0,
            "materials": [],
            "blocked_by": [],
        },
    ]
    light = project_light(snap, open_tasks, today=date(2026, 9, 10))
    assert light["generated_at"] == snap["generated_at"]
    assert light["top_priority_today"] == ["F54"]
    assert light["focus_suggestions"] == ["F99"]
    assert light["open_epics"] == ["F56"]
    assert {t["id"] for t in light["tasks"]} == {"F54", "F99", "F56"}
    f54 = next(t for t in light["tasks"] if t["id"] == "F54")
    assert f54["materials_count"] == 2
    assert "materials" not in f54
    proj = light["projects"][0]
    assert "charter_scope" not in proj
    assert proj["people"] == ["Lukáš Cypra", "Dominik Holíček", "Martina Mašková"]
    # every listed id exists in tasks
    task_ids = {t["id"] for t in light["tasks"]}
    for key in (
        "top_priority_today",
        "top_priority",
        "focus_suggestions",
        "open_epics",
        "due_soon",
        "needs_decision",
        "no_review_deadline",
        "stale_focus",
    ):
        for tid in light.get(key) or []:
            assert tid in task_ids


def test_charters_and_generated_at():
    snap = _snapshot()
    charters = build_charters(snap)
    assert charters["generated_at"] == snap["generated_at"]
    assert charters["charters"]["finance"]["scope"] == "scope text"
    assert set(charters["charters"]) == {"finance"}


def test_write_bundle_full_survives_light_failure(tmp_path: Path, monkeypatch):
    snap = _snapshot()
    open_tasks = [
        {
            "id": "F54",
            "slug": "finance",
            "status": "Next",
            "title": "Fix",
            "priority_score": 1,
            "materials": [],
            "blocked_by": [],
        }
    ]

    def boom(*_a, **_k):
        raise RuntimeError("light explode")

    monkeypatch.setattr(
        "agent_context_light.project_light",
        boom,
    )
    written = write_context_bundle(tmp_path, snap, open_tasks, today=date(2026, 9, 10))
    assert written["full"] is not None
    assert written["full"].exists()
    full = json.loads(written["full"].read_text(encoding="utf-8"))
    assert full["generated_at"] == snap["generated_at"]
    assert written["light"] is None
