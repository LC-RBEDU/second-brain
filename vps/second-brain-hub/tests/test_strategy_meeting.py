"""Tests for strategy meeting context extraction."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from datetime import datetime, timezone  # noqa: E402

from drive_io import FileMeta  # noqa: E402
from strategy_meeting import (  # noqa: E402
    build_strategy_meeting_block,
    collect_strategy_meeting_from_drive,
    _parse_pillars,
)


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


def _parse_fm(text: str):
    if not text.startswith("---"):
        return {}, text
    _, raw, body = text.split("---", 2)
    fm: dict = {}
    for line in raw.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip()
    return fm, body


def test_drive_collector_uses_file_meta_name():
    name = "2026-09-07 — Strategická schůzka (Sembly).md"
    material = (
        "---\n"
        "title: Strategická schůzka\n"
        "created: 2026-09-07\n"
        "---\n"
        "body\n"
    )

    class Vault:
        def read_text(self, rel: str):
            if rel.endswith("Strategy.md"):
                return "---\n---\n" + HUB_SNIPPET, None
            return material, None

        def list_dir(self, rel: str, pattern: str | None = None):
            return [
                FileMeta(
                    id="skip",
                    name="_draft — Strategická schůzka.md",
                    mime_type="text/markdown",
                    modified_time=datetime(2026, 9, 8, tzinfo=timezone.utc),
                    size=1,
                    parent_id="p",
                    rel_path="02-PROJEKTY/strategy/materials/_draft — Strategická schůzka.md",
                ),
                FileMeta(
                    id="ok",
                    name=name,
                    mime_type="text/markdown",
                    modified_time=datetime(2026, 9, 7, tzinfo=timezone.utc),
                    size=10,
                    parent_id="p",
                    rel_path=f"02-PROJEKTY/strategy/materials/{name}",
                ),
            ]

    block = collect_strategy_meeting_from_drive(Vault(), parse_frontmatter=_parse_fm)
    assert block["latest_meeting"]["date"] == "2026-09-07"
    assert block["latest_meeting"]["path"].endswith(name)
