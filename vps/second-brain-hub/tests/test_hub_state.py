"""Tests for hub_state marker block generation."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from hub_state import (  # noqa: E402
    LEGACY_STATE_BEGIN,
    LEGACY_STATE_END,
    STATE_BEGIN,
    STATE_END,
    build_state_content,
    has_state_block,
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
    focus=None,
):
    return {
        "id": tid,
        "slug": slug,
        "status": status,
        "title": title,
        "deadline": deadline,
        "updated": updated,
        "blocked_by": blocked_by or [],
        "focus": focus,
        "ice_i": ice_i,
        "ice_c": ice_c,
        "ice_e": ice_e,
    }


def test_build_state_content_counts():
    tasks = [
        _task("F1", status="Doing", ice_i=10, ice_c=10, ice_e=2),
        _task("F2", status="Next"),
        _task("F3", status="Waiting"),
        _task("F4", status="Cancelled"),
    ]
    inner, stale = build_state_content(
        "finance", tasks, [], date(2026, 6, 12),
        hub_updated="2026-05-01",
    )
    # Cancelled is closed for good and must not inflate the open count.
    assert "Otevřené: 3" in inner
    assert "Doing 1" in inner
    assert "ASAP" not in inner
    assert "[[F1]]" in inner
    assert stale is True


def test_build_state_content_lists_focus_of_current_week():
    today = date(2026, 6, 12)  # 2026-W24
    tasks = [
        _task("F1", status="Next", focus="2026-W24"),
        _task("F2", status="Next", focus="2026-W23"),
        _task("F3", status="Next"),
    ]
    inner, _ = build_state_content("finance", tasks, [], today, hub_updated="2026-06-11")
    assert "Ve fokusu tento týden" in inner
    focus_section = inner.split("Ve fokusu tento týden")[1].split("**TOP")[0]
    assert "[[F1]]" in focus_section
    assert "[[F2]]" not in focus_section


def test_titles_are_not_truncated():
    long_title = "H2 rozpočty a forecast — alokace, Allfred cost, cashflow a ještě něco navíc"
    tasks = [_task("S12", slug="strategy", status="Next", title=long_title)]
    inner, _ = build_state_content("strategy", tasks, [], date(2026, 6, 12))
    assert long_title in inner


def test_pipe_in_title_is_escaped_for_table():
    tasks = [_task("F1", status="Next", title="A | B")]
    inner, _ = build_state_content("finance", tasks, [], date(2026, 6, 12))
    assert r"A \| B" in inner


def test_link_always_targets_the_full_filename():
    # A bare [[S23]] would be outranked by any stray note named S23.md
    # (e.g. in 01-INBOX/daily), so the link must carry the filename.
    t = _task("S23", slug="strategy", status="Next", title="Zkrácená activation")
    t["rel_path"] = "02-PROJEKTY/strategy/tasks/S23 — Zkrácená activation.md"
    inner, _ = build_state_content("strategy", [t], [], date(2026, 6, 12))
    assert r"[[S23 — Zkrácená activation\|S23]]" in inner
    assert "[[S23]]" not in inner


def test_deadline_task_is_linked_in_callout():
    tasks = [_task("F9", status="Next", deadline="2026-06-20")]
    inner, _ = build_state_content("finance", tasks, [], date(2026, 6, 12))
    assert "> [!abstract]" in inner
    assert "nejbližší deadline **2026-06-20** ([[F9]])" in inner


def test_stale_when_hub_old():
    assert is_narrative_stale("2026-05-01", date(2026, 6, 12)) is True
    assert is_narrative_stale("2026-06-10", date(2026, 6, 12)) is False


def test_upsert_state_in_body():
    body = "# Téma: Finance\n\n## Scope\n\nFoo.\n"
    out = upsert_state_in_hub_body(body, "line one")
    assert STATE_BEGIN in out
    assert "line one" in out
    out2 = upsert_state_in_hub_body(out, "line two")
    assert "line two" in out2
    assert "line one" not in out2


def test_legacy_html_markers_are_migrated():
    body = (
        "# Téma: Finance\n\n"
        f"## Stav (auto)\n{LEGACY_STATE_BEGIN}\nstaré\n{LEGACY_STATE_END}\n\n"
        "## Scope\n\nFoo.\n"
    )
    assert has_state_block(body)
    out = upsert_state_in_hub_body(body, "nové")
    assert LEGACY_STATE_BEGIN not in out
    assert LEGACY_STATE_END not in out
    assert STATE_BEGIN in out and STATE_END in out
    assert "nové" in out and "staré" not in out
    # the rest of the charter survives untouched
    assert "## Scope" in out and "Foo." in out


def test_duplicate_blocks_collapse_to_one():
    # An older build that only knew the HTML markers appends its own block
    # next to the migrated one. The next run must clean that up.
    body = (
        "# Téma: Strategy\n\n"
        f"## Stav (auto)\n{LEGACY_STATE_BEGIN}\nstarý blok\n{LEGACY_STATE_END}\n\n"
        f"## Stav (auto)\n{STATE_BEGIN}\nnový blok\n{STATE_END}\n\n"
        "## Cíl\n\nNěco.\n"
    )
    out = upsert_state_in_hub_body(body, "jediný blok")
    assert out.count("## Stav (auto)") == 1
    assert out.count(STATE_BEGIN) == 1
    assert LEGACY_STATE_BEGIN not in out
    assert "starý blok" not in out and "nový blok" not in out
    assert "jediný blok" in out
    assert "## Cíl" in out and "Něco." in out
    # and it is stable on a second pass
    assert upsert_state_in_hub_body(out, "jediný blok") == out


def test_upsert_preserves_backslash_escapes():
    body = "# T\n\nx\n"
    out = upsert_state_in_hub_body(body, r"| A \| B |")
    assert r"| A \| B |" in out


def test_wrap_state_block():
    block = wrap_state_block("x")
    assert "## Stav (auto)" in block
    assert STATE_END in block
    assert "<!--" not in block
