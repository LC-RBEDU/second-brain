"""Unit tests for rank_key / deadline bucket / company_bonus (priority model v2.2)."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from today_priority import (
    COMPANY_PRIORITY_BONUS,
    company_bonus,
    effective_due,
    in_deadline_bucket,
    needs_decision,
    rank_key,
    rank_score,
    select_top_priority,
)

TODAY = date(2026, 10, 3)


def _task(**kwargs):
    base = {
        "id": "T",
        "slug": "finance",
        "status": "Next",
        "type": "story",
        "title": "x",
        "ice_i": 5,
        "ice_c": 5,
        "ice_e": 5,
        "deadline": None,
        "review_deadline": None,
        "company_priorities": [],
        "focus": None,
    }
    base.update(kwargs)
    base["priority_score"] = round(
        (base["ice_i"] * base["ice_c"]) / max(base["ice_e"], 1), 2
    )
    return base


def test_b1_deadline_bucket_before_high_ice():
    near = _task(id="NEAR", deadline=(TODAY + timedelta(days=3)).isoformat(), ice_i=1, ice_c=1, ice_e=1)
    near["priority_score"] = 1.0
    high = _task(id="HIGH", ice_i=9, ice_c=9, ice_e=1)
    high["priority_score"] = 81.0
    _, top = select_top_priority([near, high], TODAY)
    assert [t["id"] for t in top] == ["NEAR", "HIGH"]
    assert top[0]["in_deadline_bucket"] is True
    assert top[1]["in_deadline_bucket"] is False


def test_b2_overdue_in_deadline_bucket():
    overdue = _task(id="OD", deadline=(TODAY - timedelta(days=2)).isoformat())
    assert in_deadline_bucket(overdue["deadline"], TODAY) is True
    assert rank_key(overdue, TODAY)[0] == 0


def test_b3_review_does_not_affect_rank_key():
    a = _task(id="A", review_deadline=(TODAY - timedelta(days=5)).isoformat(), ice_i=5, ice_c=5, ice_e=5)
    b = _task(id="B", review_deadline=(TODAY + timedelta(days=1)).isoformat(), ice_i=5, ice_c=5, ice_e=5)
    a["priority_score"] = b["priority_score"] = 5.0
    assert rank_key(a, TODAY) == rank_key(b, TODAY)


def test_b4_company_bonus_strip():
    assert company_bonus(_task(company_priorities=["[[CP8 — Exponential Summit]]"])) == COMPANY_PRIORITY_BONUS
    assert company_bonus(_task(company_priorities=[""])) == 0.0
    assert company_bonus(_task(company_priorities=["—"])) == 0.0
    assert company_bonus(_task(company_priorities=["  "])) == 0.0
    assert company_bonus(_task(company_priorities=[])) == 0.0
    t = _task(company_priorities=["[[CP1]]"], ice_i=5, ice_c=5, ice_e=5)
    t["priority_score"] = 5.0
    assert rank_score(t) == 10.0


def test_b5_focus_suggestions_same_rank_key():
    from lifecycle_promotion import select_focus_suggestions

    near = _task(id="NEAR", deadline=(TODAY + timedelta(days=2)).isoformat(), ice_i=2, ice_c=2, ice_e=1)
    near["priority_score"] = 4.0
    high = _task(id="HIGH", ice_i=9, ice_c=9, ice_e=1)
    high["priority_score"] = 81.0
    sug = select_focus_suggestions(
        [high, near], today=TODAY, current_focus_count=0, target=5
    )
    assert [t["id"] for t in sug[:2]] == ["NEAR", "HIGH"]


def test_b6_effective_due_exclusive():
    assert effective_due("2026-10-10", "2026-10-01") == date(2026, 10, 10)
    assert needs_decision(
        _task(deadline="2026-10-10", review_deadline="2026-09-01"), TODAY
    ) is False
    assert needs_decision(
        _task(deadline=None, review_deadline="2026-09-01"), TODAY
    ) is True


def test_b7_horizon_day_7_vs_8():
    d7 = (TODAY + timedelta(days=7)).isoformat()
    d8 = (TODAY + timedelta(days=8)).isoformat()
    assert in_deadline_bucket(d7, TODAY) is True
    assert in_deadline_bucket(d8, TODAY) is False


def test_b8_within_bucket_deadline_asc():
    older = _task(id="OLD", deadline=(TODAY - timedelta(days=5)).isoformat(), ice_i=9, ice_c=9, ice_e=1)
    older["priority_score"] = 81.0
    nearer = _task(id="NEAR", deadline=(TODAY + timedelta(days=1)).isoformat(), ice_i=1, ice_c=1, ice_e=1)
    nearer["priority_score"] = 1.0
    _, top = select_top_priority([nearer, older], TODAY)
    assert [t["id"] for t in top] == ["OLD", "NEAR"]


def test_b9_hub_state_rank_key():
    from hub_state import build_state_content

    low_dl = _task(
        id="LOW",
        status="Next",
        deadline=(TODAY + timedelta(days=1)).isoformat(),
        ice_i=1,
        ice_c=1,
        ice_e=1,
        title="low ice near deadline",
    )
    low_dl["priority_score"] = 1.0
    high = _task(
        id="HIGH",
        status="Doing",
        ice_i=9,
        ice_c=9,
        ice_e=1,
        title="high ice no deadline",
    )
    high["priority_score"] = 81.0
    md, _ = build_state_content(
        slug="finance",
        all_tasks=[low_dl, high],
        archived_tasks=[],
        today=TODAY,
    )
    # TOP 3 table: LOW must appear before HIGH
    idx_top = md.index("TOP 3 podle skóre")
    chunk = md[idx_top:]
    assert chunk.index("LOW") < chunk.index("HIGH")


def test_far_deadline_does_not_beat_high_ice_without_deadline():
    far = _task(id="FAR", deadline=(TODAY + timedelta(days=20)).isoformat(), ice_i=1, ice_c=1, ice_e=1)
    far["priority_score"] = 1.0
    high = _task(id="HIGH", ice_i=9, ice_c=9, ice_e=1)
    high["priority_score"] = 81.0
    _, top = select_top_priority([far, high], TODAY)
    assert [t["id"] for t in top] == ["HIGH", "FAR"]


def test_paused_project_helpers_exclude_from_queue():
    from today_priority import (
        exclude_paused_project_tasks,
        is_active_project_status,
        paused_project_slugs,
    )

    assert is_active_project_status("paused") is False
    projects = [
        {"slug": "finance", "status": "active"},
        {"slug": "kratky-potlesk", "status": "paused"},
    ]
    paused = paused_project_slugs(projects)
    tasks = [
        {
            "id": "KP1",
            "slug": "kratky-potlesk",
            "status": "Next",
            "focus": "2026-W40",
            "type": "story",
            "ice_i": 9,
            "ice_c": 9,
            "ice_e": 1,
            "title": "paused",
            "priority_score": 81.0,
        },
        {
            "id": "F1",
            "slug": "finance",
            "status": "Next",
            "focus": "2026-W40",
            "type": "story",
            "ice_i": 5,
            "ice_c": 5,
            "ice_e": 5,
            "title": "active",
            "priority_score": 5.0,
        },
    ]
    today = date(2026, 9, 28)  # W40
    queue = exclude_paused_project_tasks(tasks, paused)
    assert [t["id"] for t in queue] == ["F1"]
    top_today, _ = select_top_priority(queue, today)
    assert [t["id"] for t in top_today] == ["F1"]
