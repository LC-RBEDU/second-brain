#!/usr/bin/env python3
"""Move people / boundaries / metrics_kpi from hub frontmatter into body sections.

Obsidian Properties UI doesn't support clickable wikilinks in custom string-list
fields. This script:

1. Removes `people`, `boundaries`, `metrics_kpi` from frontmatter
2. Inserts new body sections after `## Scope` (or after `# Téma: …` if Scope missing):
   - `## Lidé / spolupráce`
   - `## Hranice / vymezení`
   - `## Metriky / KPI`
3. Skips section if hub already has it (idempotent — won't duplicate on re-run)
4. Converts string formats:
   - "Jméno (Role)" / "Jméno — Role" / "Jméno - Role" → "[[Jméno]] — Role"
     (or just "[[Jméno]]" if no role)
   - "Komaseparovaný (Role)" — split on commas, each gets own bullet
   - "[[slug]]" boundary → "[[slug]] — (vymezení doplň ručně)"
   - "<KPI> → <target> (<measured_at>)" → "**<KPI>** — target: <target>, měřeno: <measured_at>"

Idempotent: re-running on already-migrated hub is no-op.

Usage:
    python3 scripts/move_hub_fields_to_body.py --dry-run
    python3 scripts/move_hub_fields_to_body.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml not installed.\n")
    sys.exit(1)

DEFAULT_VAULT = Path(
    "~/GitHub/second-brain-vault"
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
PERSON_ROLE_RE = re.compile(r"^(.+?)\s*[\(\[—–\-]\s*(.+?)[\)\]]?\s*$")


def parse_person(s: str) -> list[str]:
    """Parse person string into list of bullet lines.

    Inputs handled:
        "Luboš Malý (Co-strategist)"            -> ["[[Luboš Malý]] — Co-strategist"]
        "Luboš Malý — Co-strategist"            -> ["[[Luboš Malý]] — Co-strategist"]
        "Martin, Lukáš, Lenka (Strategy tým)"   -> ["[[Martin]] — Strategy tým", ...]
        "Pavel Kroupa"                          -> ["[[Pavel Kroupa]]"]
    """
    s = s.strip()
    if not s:
        return []
    # Try to split into name(s) + role
    m = re.match(r"^(.+?)\s*\((.+?)\)\s*$", s)
    role: Optional[str] = None
    names_part = s
    if m:
        names_part = m.group(1).strip()
        role = m.group(2).strip()
    else:
        # try em-dash / hyphen separator
        for sep in [" — ", " – ", " - "]:
            if sep in s:
                a, b = s.split(sep, 1)
                names_part = a.strip()
                role = b.strip()
                break
    # Names can be comma-separated
    if "," in names_part:
        names = [n.strip() for n in names_part.split(",") if n.strip()]
    else:
        names = [names_part.strip()]
    out = []
    for n in names:
        if role:
            out.append(f"- [[{n}]] — {role}")
        else:
            out.append(f"- [[{n}]]")
    return out


def parse_boundary(s: str) -> str:
    """Convert boundary string to bullet line."""
    s = s.strip()
    if not s:
        return ""
    # Already wikilink?
    m = WIKILINK_RE.search(s)
    if m:
        slug = m.group(1)
        rest = WIKILINK_RE.sub("", s).strip(" —–-")
        if rest:
            return f"- [[{slug}]] — {rest}"
        return f"- [[{slug}]] — (vymezení doplň)"
    return f"- {s}"


def parse_kpi(s: str) -> str:
    """Convert KPI string to bullet line.

    Inputs:
        "Adopce X → 3 (2026-09-30)" -> "- **Adopce X** — target: 3, měřeno: 2026-09-30"
        "Free text"                 -> "- **Free text**"
    """
    s = s.strip()
    if not s:
        return ""
    target = ""
    measured = ""
    text = s
    m = re.match(r"^(.+?)\s*→\s*(.+?)\s*\((.+?)\)\s*$", s)
    if m:
        text, target, measured = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    else:
        m = re.match(r"^(.+?)\s*→\s*(.+)$", s)
        if m:
            text, target = m.group(1).strip(), m.group(2).strip()
    parts = []
    if target:
        parts.append(f"target: {target}")
    if measured:
        parts.append(f"měřeno: {measured}")
    if parts:
        return f"- **{text}** — " + ", ".join(parts)
    return f"- **{text}**"


def render_section(title: str, lines: list[str]) -> str:
    if not lines:
        return ""
    return f"\n## {title}\n\n" + "\n".join(lines) + "\n"


def has_section(body: str, title: str) -> bool:
    pattern = rf"^##\s+{re.escape(title)}\s*$"
    return bool(re.search(pattern, body, re.MULTILINE))


def insert_after_scope(body: str, new_sections: str) -> str:
    """Insert new_sections after `## Scope` block, or after H1 if Scope missing."""
    if not new_sections:
        return body
    # Find ## Scope block end (next ## heading or EOF)
    scope_match = re.search(r"^##\s+Scope\s*$", body, re.MULTILINE)
    if scope_match:
        # Find next H2 after scope
        rest = body[scope_match.end():]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        if next_h2:
            insert_pos = scope_match.end() + next_h2.start()
        else:
            insert_pos = len(body)
        return body[:insert_pos].rstrip() + "\n" + new_sections + "\n" + body[insert_pos:].lstrip("\n")
    # Fallback: insert after first H1
    h1_match = re.search(r"^#\s+.+?$", body, re.MULTILINE)
    if h1_match:
        rest = body[h1_match.end():]
        next_h2 = re.search(r"^##\s+", rest, re.MULTILINE)
        if next_h2:
            insert_pos = h1_match.end() + next_h2.start()
        else:
            insert_pos = len(body)
        return body[:insert_pos].rstrip() + "\n" + new_sections + "\n" + body[insert_pos:].lstrip("\n")
    return body + "\n" + new_sections


def patch_hub(path: Path, dry_run: bool = False) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ! {path}: {e}")
        return False
    m = FRONTMATTER_RE.match(text)
    if not m:
        return False
    fm_yaml, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_yaml) or {}
    except yaml.YAMLError as e:
        print(f"  ! YAML error in {path.name}: {e}")
        return False
    if not isinstance(fm, dict) or (fm.get("type") or "").lower() != "project":
        return False

    people = fm.get("people")
    boundaries = fm.get("boundaries")
    kpis = fm.get("metrics_kpi")

    # Build sections only if data present and section not already there
    new_sections = []
    if people and isinstance(people, list) and not has_section(body, "Lidé / spolupráce"):
        lines: list[str] = []
        for p in people:
            if isinstance(p, str):
                lines.extend(parse_person(p))
            elif isinstance(p, dict):
                name = (p.get("name") or "").strip()
                role = (p.get("role") or "").strip()
                if name:
                    lines.append(f"- [[{name}]] — {role}" if role else f"- [[{name}]]")
        if lines:
            new_sections.append(render_section("Lidé / spolupráce", lines))

    if boundaries and isinstance(boundaries, list) and not has_section(body, "Hranice / vymezení"):
        lines = []
        for b in boundaries:
            if isinstance(b, str):
                line = parse_boundary(b)
                if line:
                    lines.append(line)
        if lines:
            new_sections.append(render_section("Hranice / vymezení", lines))

    if kpis and isinstance(kpis, list) and not has_section(body, "Metriky / KPI"):
        lines = []
        for k in kpis:
            if isinstance(k, str):
                line = parse_kpi(k)
                if line:
                    lines.append(line)
            elif isinstance(k, dict):
                kpi_text = (k.get("kpi") or "").strip()
                target = k.get("target", "")
                measured = (k.get("measured_at") or "").strip()
                if kpi_text:
                    parts = []
                    if target != "" and target is not None:
                        parts.append(f"target: {target}")
                    if measured:
                        parts.append(f"měřeno: {measured}")
                    if parts:
                        lines.append(f"- **{kpi_text}** — " + ", ".join(parts))
                    else:
                        lines.append(f"- **{kpi_text}**")
        if lines:
            new_sections.append(render_section("Metriky / KPI", lines))

    new_body = body
    if new_sections:
        new_body = insert_after_scope(body, "".join(new_sections))

    # Remove fields from frontmatter
    new_fm = {k: v for k, v in fm.items() if k not in ("people", "boundaries", "metrics_kpi")}

    if new_fm == fm and new_body == body:
        return False

    new_yaml = yaml.safe_dump(
        new_fm, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    if not new_body.startswith("\n"):
        new_body = "\n" + new_body
    new_text = f"---\n{new_yaml}---{new_body}"
    if dry_run:
        print(f"  ~ {path.name} would change ({len(new_sections)} new sections)")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"  ✓ {path.name} migrated ({len(new_sections)} sections)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    projekty = args.vault / "02-PROJEKTY"
    if not projekty.exists():
        sys.stderr.write(f"vault not found: {args.vault}\n")
        return 1
    n = 0
    for hub in sorted(projekty.glob("*.md")):
        if hub.name.startswith("_"):
            continue
        if patch_hub(hub, dry_run=args.dry_run):
            n += 1
    mode = "dry-run" if args.dry_run else "patched"
    print(f"\nmove_hub_fields_to_body: {n} hubs {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
