"""Tests for strategy meeting context extraction."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from strategy_meeting import build_strategy_meeting_block, _parse_pillars  # noqa: E402


HUB_SNIPPET = """
## Strategy meeting (prep)

**Aktuální pilíře H2 (září 2026 – únor 2027):**

| Pilíř | Obsah |
|-------|--------|
| **Jsme v EDU rádi** | Identita · info flow |
| **Rosteme** | Edutéka · KAM |

**Otevřená strategická rozhodnutí:** org chart v1, finance+data vs. split IT/Systems, Town Hall = priority + retro.
"""


def test_parse_pillars():
    pillars = _parse_pillars(HUB_SNIPPET)
    assert len(pillars) == 2
    assert pillars[0]["name"] == "Jsme v EDU rádi"
    assert "Identita" in pillars[0]["summary"]


def test_build_strategy_meeting_block():
    block = build_strategy_meeting_block(
        HUB_SNIPPET,
        latest_material_fm={
            "title": "Strategická schůzka",
            "created": "2026-09-07",
            "topics": ["org design", "priority H2"],
        },
        latest_material_rel="02-PROJEKTY/strategy/materials/2026-09-07 — Strategická schůzka (Sembly).md",
    )
    assert block["latest_meeting"]["date"] == "2026-09-07"
    assert "org design" in block["themes"]
    assert "Jsme v EDU rádi" in block["themes"]
    assert len(block["open_decisions"]) >= 2
