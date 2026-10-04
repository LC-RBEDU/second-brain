"""Strukturální kontrakt create balíčku firemních priorit (B1, B4, DoD lock)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "ŠABLONY/skills/wiki-firemni-priority"
BUNDLE = SKILL / "create-bundle.md"
TODAY = date(2026, 10, 4)

H2 = [
    "## Název",
    "## Co to konkrétně znamená",
    "## Kontext",
    "## Owner",
    "## Klíčové osoby",
    "## DoD + aktuální stav plnění",
    "## Přehled milníků se zvýrazněním nejbližšího",
]

CP4_DOD = (
    "Tým používá AI agenty. Klesá množství dotazů "
    "(kde najdu / jak děláme / máme někde…) a duplicitních řešení, "
    "která vznikla, protože nikdo nenašel standard."
)

MILESTONE = re.compile(
    r"^- (?P<bold>\*\*)?(?P<date>\d{4}-\d{2}-\d{2}) — (?P<text>.+?)(?:\*\*)?$"
)


def pages() -> dict[str, str]:
    text = BUNDLE.read_text(encoding="utf-8")
    parts = re.split(r"<!-- page: ([^>]+) -->\n", text)
    # parts[0] is preamble, then path, body, path, body...
    out = {}
    for i in range(1, len(parts), 2):
        out[parts[i].strip()] = parts[i + 1]
    return out


def dod_block(body: str) -> str:
    start = body.index("## DoD + aktuální stav plnění")
    rest = body[start:]
    end = rest.index("### Stav plnění")
    return rest[:end]


def milestone_lines(body: str) -> list[re.Match[str]]:
    section = body.split("## Přehled milníků se zvýrazněním nejbližšího", 1)[1]
    found = []
    for line in section.splitlines():
        m = MILESTONE.match(line.strip())
        if m:
            found.append(m)
    return found


def expected_nearest(matches: list[re.Match[str]]) -> re.Match[str] | None:
    future = [m for m in matches if date.fromisoformat(m.group("date")) >= TODAY]
    if not future:
        return None
    best = min(future, key=lambda m: date.fromisoformat(m.group("date")))
    best_date = best.group("date")
    return next(m for m in future if m.group("date") == best_date)


def test_ten_pages_and_seven_headings():
    found = pages()
    assert len(found) == 10
    for n in range(1, 10):
        key = next(k for k in found if k.startswith(f"strategicke-priority-rb-edu/cp{n}-"))
        body = found[key]
        headings = [line for line in body.splitlines() if line.startswith("## ")]
        assert headings == H2, key
        assert "progress: neznámé" in body
        assert "### Historie změn" in body
        assert "\n## Historie" not in body


def test_cp4_dod_verbatim_and_cp2_open():
    found = pages()
    cp4 = next(v for k, v in found.items() if "/cp4-" in k)
    assert CP4_DOD in dod_block(cp4)
    cp2 = next(v for k, v in found.items() if "/cp2-" in k)
    block = dod_block(cp2)
    assert "Mizí dotazy „koho se mám zeptat“" in block
    assert "DoD neuzavřené" in block
    assert "cp_owner: Mária Falterová" in cp2


def test_no_vault_and_no_ice_heading():
    text = BUNDLE.read_text(encoding="utf-8")
    assert "OBSIDIAN/" not in text
    assert "\n## ICE" not in text
    assert "company_priorities" not in text


def test_nearest_milestone_matches_today():
    found = pages()
    for key, body in found.items():
        if not re.search(r"/cp\d-", key):
            continue
        matches = milestone_lines(body)
        nearest = expected_nearest(matches)
        if nearest is None:
            assert 'nearest_milestone: ""' in body, key
            assert 'nearest_milestone_date: ""' in body, key
            assert not any(m.group("bold") for m in matches), key
        else:
            assert nearest.group("bold") == "**", key
            for m in matches:
                if m is not nearest:
                    assert m.group("bold") is None, (key, m.group(0))
            assert f"nearest_milestone_date: {nearest.group('date')}" in body


def test_dashboard_sidelined_without_cp_ids():
    body = pages()["strategicke-priority-rb-edu/prehled.md"]
    assert body.count("\n| [CP") == 9
    sidelined = body.split("## Co teď není priorita", 1)[1]
    assert not re.search(r"CP\d", sidelined)
    for item in (
        "LD komunita",
        "Exponential Circles",
        "LD noha",
        "odměňování",
        "PR ODY+EDU",
        "Anti-Švarc",
        "Partnerships",
        "Redesign RBL",
    ):
        assert item in sidelined


def test_skill_guards():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "wiki_write" in skill and "index.md" in skill
    assert "Chybí wiki MCP. Karty firemních priorit bez něj neukážu ani nezměním." in skill
    assert "OBSIDIAN" not in skill or "nečte" in skill
    assert "zapiš znovu" in skill
    instructions = (SKILL / "project-instructions.md").read_text(encoding="utf-8")
    assert "wiki-firemni-priority" in instructions
    assert "z hlavy" in instructions
