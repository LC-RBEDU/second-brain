"""Tests for lib/operational_steps.py."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from operational_steps import (  # noqa: E402
    is_operational_header,
    sort_operational_steps,
    subtask_sort_key,
)


def test_header_detection():
    assert is_operational_header("## Operativní kroky")
    assert is_operational_header("## Operativni kroky")
    assert not is_operational_header("## Poznámky / log")
    assert not is_operational_header("### Operativní kroky")


def test_sort_key_open_before_done():
    assert subtask_sort_key(False, "**S12-9** x", 0) < subtask_sort_key(True, "**S12-1** x", 1)


def test_sort_key_numeric_not_lexicographic():
    assert subtask_sort_key(False, "**S12-4** x", 0) < subtask_sort_key(False, "**S12-14** x", 1)


def test_sort_key_letter_suffix_follows_base():
    base = subtask_sort_key(False, "**F41-3** x", 0)
    suffix = subtask_sort_key(False, "**F41-3b** x", 1)
    later = subtask_sort_key(False, "**F41-4** x", 2)
    assert base < suffix < later


def test_basic_reordering():
    body = "\n".join([
        "# T",
        "",
        "## Operativní kroky",
        "- [x] **S12-1** hotovo",
        "- [ ] **S12-14** otevřené vysoké",
        "- [x] **S12-9** taky hotovo",
        "- [ ] **S12-4** otevřené nízké",
        "",
        "## Poznámky / log",
        "- něco",
        "",
    ])
    new, changed = sort_operational_steps(body)
    assert changed
    steps = [l for l in new.split("\n") if l.startswith("- [")]
    assert steps == [
        "- [ ] **S12-4** otevřené nízké",
        "- [ ] **S12-14** otevřené vysoké",
        "- [x] **S12-1** hotovo",
        "- [x] **S12-9** taky hotovo",
    ]
    assert "## Poznámky / log" in new
    assert "- něco" in new


def test_idempotent():
    body = "\n".join([
        "## Operativní kroky",
        "- [ ] **A1-2** b",
        "- [ ] **A1-10** c",
        "- [x] **A1-1** a",
        "",
    ])
    once, _ = sort_operational_steps(body)
    twice, changed = sort_operational_steps(once)
    assert once == twice
    assert not changed


def test_h3_subheadings_are_boundaries():
    body = "\n".join([
        "## Operativní kroky",
        "- [x] **AF14-1** a",
        "- [ ] **AF14-13** open in first block",
        "",
        "### Import expense forecastu",
        "- [x] **AF14-6** f",
        "- [x] **AF14-5** e",
        "",
        "## Poznámky / log",
        "",
    ])
    new, _ = sort_operational_steps(body)
    lines = [l for l in new.split("\n") if l.strip()]
    i_head = lines.index("### Import expense forecastu")
    before = [l for l in lines[:i_head] if l.startswith("- [")]
    after = [l for l in lines[i_head:] if l.startswith("- [")]
    # open item stays in its own block, never jumps above the subheading
    assert before == ["- [ ] **AF14-13** open in first block", "- [x] **AF14-1** a"]
    assert after == ["- [x] **AF14-5** e", "- [x] **AF14-6** f"]


def test_continuation_lines_travel_with_item():
    body = "\n".join([
        "## Operativní kroky",
        "- [x] **FP27-2** done",
        "- [ ] **FP27-1** open",
        "  - Mapovat PD sales vs. realizace",
        "  - **Pipedrive fáze 5**",
        "",
    ])
    new, _ = sort_operational_steps(body)
    lines = [l for l in new.split("\n") if l.strip()]
    assert lines[1] == "- [ ] **FP27-1** open"
    assert lines[2].startswith("  - Mapovat")
    assert lines[3].startswith("  - **Pipedrive")
    assert lines[4] == "- [x] **FP27-2** done"


def test_no_operational_section_is_untouched():
    body = "# T\n\n## Poznámky / log\n- a\n"
    new, changed = sort_operational_steps(body)
    assert new == body
    assert not changed


def test_unparsed_item_sinks_but_keeps_order():
    body = "\n".join([
        "## Operativní kroky",
        "- [ ] volný krok bez ID",
        "- [ ] **X1-2** druhý",
        "- [ ] **X1-1** první",
        "",
    ])
    new, _ = sort_operational_steps(body)
    steps = [l for l in new.split("\n") if l.startswith("- [")]
    assert steps == [
        "- [ ] **X1-1** první",
        "- [ ] **X1-2** druhý",
        "- [ ] volný krok bez ID",
    ]


if __name__ == "__main__":
    import traceback

    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                fails += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    raise SystemExit(1 if fails else 0)
