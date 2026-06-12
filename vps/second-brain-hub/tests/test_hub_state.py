"""Tests for hub_state marker block generation."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from hub_state import (  # noqa: E402
    build_state_content,
    is_narrative_stale,
    upsert_state_in_hub_body,
    wrap_state_block,
)


def _task(
    tid: str,
    slug: str = "finance",
    status: str = "Next",
    title: str = "Test task",
    deadline: str | None = None,
    updated: str | None = "2026-06-10",
    blocked_by: list | None = None,
    ice_i=7,
    ice_c=8,
    ice_e=5,
):
    return {
        "id": tid,
        "slug": slug,
        "status": status,
        "title": title,
        "deadline": deadline,
        "updated": updated,
        "blocked_by": blocked_by or [],
        "ice_i": ice_i,
        "ice_c": ice_c,
        "ice_e": ice_e,
    }


def test_build_state_content_counts():
    tasks = [
        _task("F1", status="ASAP", ice_i=10, ice_c=10, ice_e=2),
        _task("F2", status="Next"),
        _task("F3", status="Waiting"),
    ]
    inner, stale = build_state_content(
        "finance", tasks, [], date(2026, 6, 12),
        hub_updated="2026-05-01",
    )
    assert "Otevřené:** 3" in inner
    assert "ASAP 1" in inner
    assert "**F1**" in inner
    assert stale is True


def test_stale_when_hub_old():
    assert is_narrative_stale("2026-05-01", date(2026, 6, 12)) is True
    assert is_narrative_stale("2026-06-10", date(2026, 6, 12)) is False


def test_upsert_state_in_body():
    body = "# Téma: Finance\n\n## Scope\n\nFoo.\n"
    inner = "line one"
    out = upsert_state_in_hub_body(body, inner)
    assert "<!-- SB:STATE:BEGIN -->" in out
    assert "line one" in out
    out2 = upsert_state_in_hub_body(out, "line two")
    assert "line two" in out2
    assert "line one" not in out2


def test_wrap_state_block():
    block = wrap_state_block("x")
    assert "## Stav (auto)" in block
    assert "<!-- SB:STATE:END -->" in block
