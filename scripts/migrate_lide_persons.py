#!/usr/bin/env python3
"""Migrate 05-RESOURCES/lide/*.md to F6.4 person template structure (idempotent).

Preserves ## Zmínky a materiály table from sync_lide_people.py.
Usage:
  python3 scripts/migrate_lide_persons.py
  python3 scripts/migrate_lide_persons.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIDE = REPO / "OBSIDIAN" / "05-RESOURCES" / "lide"
SKIP = {"_ŠABLONA-person.md", "_index.md"}

SECTIONS_ORDER = [
    "## Kontakty",
    "## Významná data",
    "## Témata",
    "## Projekty a tasky",
    "## Zmínky a materiály",
    "## Log",
]

DEFAULT_SECTION_BODY = {
    "## Kontakty": "- E-mail: —\n- Telefon: —\n- Slack: —",
    "## Významná data": "- Narozeniny: —",
    "## Témata": "- _(doplň)_",
    "## Projekty a tasky": "- _(doplň wikilinks na huby)_",
    "## Log": "- _(prázdné)_",
}


def _parse_frontmatter(text: str) -> tuple[str, str, dict]:
    if not text.startswith("---"):
        return "", text, {}
    end = text.find("\n---", 3)
    if end < 0:
        return "", text, {}
    fm = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    return fm, body, {}


def _ensure_fm_fields(fm: str, name: str) -> str:
    today = date.today().isoformat()
    lines = fm.splitlines()
    keys = {ln.split(":", 1)[0].strip() for ln in lines if ":" in ln}
    additions = []
    if "type:" not in keys:
        additions.append("type: person")
    if "aliases:" not in keys:
        additions.append(f"aliases:\n- {name}")
    if "role:" not in keys:
        additions.append("role: —")
    if "org:" not in keys:
        additions.append("org: Red Button EDU")
    if "email:" not in keys:
        additions.append("email: —")
    if "phone:" not in keys:
        additions.append("phone: \"\"")
    if "birthday:" not in keys:
        additions.append("birthday: \"\"")
    if "significant_dates:" not in keys:
        additions.append("significant_dates: []")
    if "projects:" not in keys:
        additions.append("projects: []")
    if "topics:" not in keys:
        additions.append("topics:\n  - lide")
    if "updated:" not in keys:
        additions.append(f"updated: {today}")
    if additions:
        lines.extend(additions)
    return "\n".join(lines)


def _extract_section(body: str, header: str) -> tuple[str, str]:
    pattern = re.compile(rf"^{re.escape(header)}\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
    m = pattern.search(body)
    if not m:
        return body, ""
    content = m.group(1).strip()
    new_body = body[: m.start()] + body[m.end() :]
    new_body = re.sub(r"\n{3,}", "\n\n", new_body).strip()
    return new_body, content


def migrate_file(path: Path, dry_run: bool) -> bool:
    name = path.stem
    text = path.read_text(encoding="utf-8")
    fm, body, _ = _parse_frontmatter(text)

    # title line
    title_m = re.match(r"^#\s+(.+)$", body, re.M)
    display = title_m.group(1).strip() if title_m else name

    sections: dict[str, str] = {}
    remaining = body
    for hdr in SECTIONS_ORDER:
        remaining, content = _extract_section(remaining, hdr)
        if content:
            sections[hdr] = content

    # drop old stray content between title and first section (keep title + optional přezdívka)
    preamble_lines: list[str] = []
    for line in remaining.splitlines():
        if line.startswith("# "):
            preamble_lines.append(line)
        elif line.startswith("*Přezdívka"):
            preamble_lines.append(line)
        elif not line.strip():
            if preamble_lines:
                preamble_lines.append(line)
    preamble = "\n".join(preamble_lines).strip()

    new_fm = _ensure_fm_fields(fm, display)
    parts = [f"---\n{new_fm}\n---\n"]
    if preamble:
        parts.append(preamble + "\n\n")
    else:
        parts.append(f"# {display}\n\n")

    for hdr in SECTIONS_ORDER:
        parts.append(hdr + "\n\n")
        if hdr in sections and sections[hdr]:
            parts.append(sections[hdr] + "\n\n")
        elif hdr == "## Zmínky a materiály":
            parts.append(
                "| Datum | Typ | Odkaz | Kontext |\n"
                "|-------|-----|-------|--------|\n"
                "| — | — | — | _(sync_lide_people.py doplní)_ |\n\n"
            )
        else:
            parts.append(DEFAULT_SECTION_BODY[hdr] + "\n\n")

    new_text = "".join(parts).rstrip() + "\n"
    if new_text == text:
        return False
    if dry_run:
        print(f"would migrate: {path.name}")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"migrated: {path.name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not LIDE.is_dir():
        print(f"ERROR: {LIDE} missing", file=sys.stderr)
        return 1
    n = 0
    for p in sorted(LIDE.glob("*.md")):
        if p.name in SKIP:
            continue
        if migrate_file(p, args.dry_run):
            n += 1
    print(f"migrate_lide_persons: {n} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
