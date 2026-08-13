#!/usr/bin/env python3
"""Doplní `related_tasks:` do frontmatteru materiálů a outputů.

Tasky nesou `materials:` — odkaz vede jedním směrem, takže z otevřeného
materiálu není vidět, ke kterému úkolu patří. Skript tu mapu otočí: pro každý
materiál, na který se odkazuje aspoň jeden task, doplní zpětný odkaz.

Odkazy z `materials:` mířící na jiný task (tasky se občas odkazují navzájem)
se ignorují — zpětný odkaz dostávají jen skutečné soubory v `materials/`
a `outputs/`.

Usage:
    python3 scripts/backfill_material_related_tasks.py --dry-run
    python3 scripts/backfill_material_related_tasks.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip install pyyaml\n")
    sys.exit(1)

DEFAULT_VAULT = Path(
    os.environ.get(
        "SECOND_BRAIN_VAULT",
        str(Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"),
    )
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
WIKILINK_RE = re.compile(r"^\[\[(?P<target>[^\]|#]+)")


def parse(text: str) -> tuple[dict, str, str] | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    return fm, m.group(1), m.group(2)


def link_target(value: str) -> str | None:
    m = WIKILINK_RE.match(str(value).strip())
    return m.group("target").strip() if m else None


BARE_ID_RE = re.compile(r"^[A-Z]{1,4}\d+$")


def normalize_bare_links(fm_yaml: str, by_id: dict[str, str]) -> tuple[str, list[str]]:
    """Rewrite `related_tasks: ['[[F30]]']` to the full task filename.

    A bare ID relies on the task's alias, and an alias loses to any file
    literally named `F30.md` — an archived inbox tombstone was hijacking the
    link. Unknown IDs are left alone rather than guessed at.
    """
    out: list[str] = []
    changed: list[str] = []
    inside = False
    for line in fm_yaml.split("\n"):
        if re.match(r"^related_tasks:", line):
            inside = True
            out.append(line)
            continue
        # YAML lists appear both indented and at zero indent in this vault.
        if inside and not re.match(r"^\s*-\s", line):
            inside = False
        if inside:
            m = re.match(r"^(\s*-\s+)'?\[\[([^\]|#]+)\]\]'?\s*$", line)
            if m and BARE_ID_RE.fullmatch(m.group(2).strip()):
                stem = by_id.get(m.group(2).strip())
                if stem:
                    line = f"{m.group(1)}{yaml_single_quoted(f'[[{stem}]]')}"
                    changed.append(m.group(2).strip())
        out.append(line)
    return "\n".join(out), changed


def tasks_by_id(vault: Path) -> dict[str, str]:
    """ID → filename stem, only for IDs owned by exactly one file."""
    seen: dict[str, list[str]] = {}
    for tf in task_files(vault):
        parsed = parse(tf.read_text(encoding="utf-8"))
        if not parsed:
            continue
        fm, _, _ = parsed
        if (fm.get("type") or "") != "task":
            continue
        tid = str(fm.get("id") or "")
        if tid:
            seen.setdefault(tid, []).append(tf.stem)
    return {tid: stems[0] for tid, stems in seen.items() if len(stems) == 1}


def task_files(vault: Path) -> list[Path]:
    return sorted((vault / "02-PROJEKTY").glob("*/tasks/*.md")) + sorted(
        (vault / "07-ARCHIV" / "tasks-done").glob("*/*.md")
    )


def material_files(vault: Path) -> list[Path]:
    base = vault / "02-PROJEKTY"
    return sorted(base.glob("*/materials/*.md")) + sorted(base.glob("*/outputs/*.md"))


def yaml_single_quoted(value: str) -> str:
    """Quote for YAML. Apostrophes inside titles must be doubled, otherwise
    they close the scalar and corrupt the whole frontmatter."""
    return "'" + value.replace("'", "''") + "'"


def insert_related_tasks(fm_yaml: str, task_stems: list[str]) -> str:
    """Insert a `related_tasks:` block, keeping the rest of the YAML verbatim."""
    block = "related_tasks:\n" + "".join(
        f"  - {yaml_single_quoted(f'[[{stem}]]')}\n" for stem in task_stems
    )
    lines = fm_yaml.split("\n")

    # Prefer right after the `projects:` block — that is where the existing
    # hand-written materials keep it.
    anchor = next((i for i, ln in enumerate(lines) if ln.startswith("projects:")), None)
    if anchor is not None:
        i = anchor + 1
        while i < len(lines) and (lines[i].startswith((" ", "-", "\t")) or not lines[i].strip()):
            if not lines[i].strip():
                break
            i += 1
        return "\n".join(lines[:i]) + "\n" + block + "\n".join(lines[i:])
    return fm_yaml + block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    material_stems = {p.stem: p for p in material_files(args.vault)}

    backlinks: dict[str, list[str]] = defaultdict(list)
    for tf in task_files(args.vault):
        parsed = parse(tf.read_text(encoding="utf-8"))
        if not parsed:
            continue
        fm, _, _ = parsed
        if (fm.get("type") or "") != "task":
            continue
        for raw in fm.get("materials") or []:
            target = link_target(raw)
            if target and target in material_stems and tf.stem not in backlinks[target]:
                backlinks[target].append(tf.stem)

    by_id = tasks_by_id(args.vault)

    patched = 0
    already = 0
    orphans = 0
    normalized = 0
    for stem, path in material_stems.items():
        parsed = parse(path.read_text(encoding="utf-8"))
        if not parsed:
            continue
        fm, fm_yaml, body = parsed
        # Key presence, not truthiness — an empty `related_tasks:` must not
        # end up duplicated in the frontmatter.
        if "related_tasks" in fm or re.search(r"^related_tasks:", fm_yaml, re.MULTILINE):
            already += 1
            new_fm, changed = normalize_bare_links(fm_yaml, by_id)
            if changed:
                normalized += 1
                rel = path.relative_to(args.vault)
                verb = "would normalize" if args.dry_run else "normalized"
                print(f"{verb}: {rel} → {', '.join(changed)}")
                if not args.dry_run:
                    path.write_text(f"---\n{new_fm}---\n{body}", encoding="utf-8")
            continue
        tasks = backlinks.get(stem)
        if not tasks:
            orphans += 1
            continue
        new_fm = insert_related_tasks(fm_yaml, sorted(tasks))
        patched += 1
        rel = path.relative_to(args.vault)
        print(f"{'would patch' if args.dry_run else 'patched'}: {rel} → {', '.join(sorted(tasks))}")
        if not args.dry_run:
            path.write_text(f"---\n{new_fm}---\n{body}", encoding="utf-8")

    print(
        f"materials={len(material_stems)} patched={patched} normalized={normalized} "
        f"already_linked={already} no_task_reference={orphans} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
