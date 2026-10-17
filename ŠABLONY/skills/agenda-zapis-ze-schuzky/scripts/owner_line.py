#!/usr/bin/env python3
"""Owner řádek pro HTML karty zápisu (div.owner).

Pravidlo: owner nikdy není v seznamu klíčových (case-insensitive, trim).
Když po odebrání ownera klíčoví prázdní → jen „Vlastní: …“.

Použití při generování body.html (agent / skript):
    from owner_line import format_owner_div, format_owner_line

    format_owner_line("Lukáš Cypra", ["Luboš Malý", "Lukáš Cypra"])
    # → "Vlastní: Lukáš Cypra · klíčoví: Luboš Malý"

    format_owner_div("Kateřina Bayerová", "Luboš Malý, Kateřina Bayerová")
    # → '<div class="owner">Vlastní: Kateřina Bayerová · klíčoví: Luboš Malý</div>'
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable


def _norm_name(name: str) -> str:
    """Porovnání jmen: trim, lower, sjednocení whitespace, bez NBSP."""
    s = (name or "").replace("\u00a0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = unicodedata.normalize("NFC", s)
    return s.casefold()


def _split_people(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"\s*,\s*", value.strip())
        return [p for p in parts if p]
    out: list[str] = []
    for item in value:
        if item is None:
            continue
        s = str(item).strip()
        if s:
            out.append(s)
    return out


def filter_key_people(
    owner: str,
    key_people: str | Iterable[str] | None,
) -> list[str]:
    """Vrátí klíčové bez ownera (a bez duplicit jména, case-insensitive)."""
    owner_n = _norm_name(owner)
    seen: set[str] = set()
    result: list[str] = []
    for person in _split_people(key_people):
        n = _norm_name(person)
        if not n or n == owner_n or n in seen:
            continue
        seen.add(n)
        result.append(person.strip())
    return result


def format_owner_line(
    owner: str,
    key_people: str | Iterable[str] | None = None,
) -> str:
    """Text uvnitř div.owner (bez HTML tagu)."""
    owner = (owner or "").strip()
    if not owner:
        return ""
    keys = filter_key_people(owner, key_people)
    if not keys:
        return f"Vlastní: {owner}"
    return f"Vlastní: {owner} · klíčoví: {', '.join(keys)}"


def format_owner_div(
    owner: str,
    key_people: str | Iterable[str] | None = None,
) -> str:
    """Celý <div class=\"owner\">…</div>."""
    line = format_owner_line(owner, key_people)
    if not line:
        return ""
    return f'<div class="owner">{line}</div>'


def rewrite_owner_div_inner(inner: str) -> str:
    """Opraví už sestavený vnitřek div.owner (Vlastní: … · klíčoví: …)."""
    m = re.match(
        r"^Vlastní:\s*(.+?)(?:\s*·\s*klíčoví:\s*(.*))?$",
        inner.strip(),
        flags=re.DOTALL,
    )
    if not m:
        return inner
    owner = m.group(1).strip()
    keys_raw = (m.group(2) or "").strip()
    return format_owner_line(owner, keys_raw or None)


if __name__ == "__main__":
    import sys

    assert format_owner_line("Lukáš Cypra", ["Luboš Malý", "Lukáš Cypra", "Jan Mašek"]) == (
        "Vlastní: Lukáš Cypra · klíčoví: Luboš Malý, Jan Mašek"
    )
    assert format_owner_line("Kateřina Bayerová", "Luboš Malý, Kateřina Bayerová") == (
        "Vlastní: Kateřina Bayerová · klíčoví: Luboš Malý"
    )
    assert format_owner_line("Luboš Malý", ["Luboš Malý"]) == "Vlastní: Luboš Malý"
    assert format_owner_line("luboš malý", "Luboš Malý, Jan Mašek") == (
        "Vlastní: luboš malý · klíčoví: Jan Mašek"
    )
    fixed = rewrite_owner_div_inner(
        "Vlastní: Lukáš Cypra · klíčoví: Luboš Malý, Jan Mašek, Lukáš Cypra"
    )
    assert fixed == "Vlastní: Lukáš Cypra · klíčoví: Luboš Malý, Jan Mašek"
    print("OK: owner_line self-check passed", file=sys.stderr)
