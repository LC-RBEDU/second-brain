#!/usr/bin/env python3
"""Backfill ``title:`` frontmatter on Second Brain v2 task files.

Extracts the first H1 from each task body and writes it into the YAML
frontmatter as ``title:`` (placed immediately after ``type:``). Idempotent —
files that already carry ``title:`` are left untouched.

Convention handled:
  ``# <ID> — <Title>`` → ``title: <Title>`` (drops ID prefix + em/en/hyphen dash)
  ``# <Title>``         → ``title: <Title>``

Targets (default):
  - OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md
  - OBSIDIAN/07-ARCHIV/tasks-done/<slug>/*.md

Usage:
  python3 scripts/backfill_task_title.py            # dry-run, summary + samples
  python3 scripts/backfill_task_title.py --write    # actually edit files
  python3 scripts/backfill_task_title.py --root <path>  # alternative vault root
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VAULT_DEFAULT = REPO_ROOT / "OBSIDIAN"

# Task ID prefix used in H1 headings (e.g. "S2 — ...", "RBU13 — ...").
ID_RE = re.compile(r"^[A-Z]{1,5}\d+$")
# Acceptable separators between ID and title in H1 (em dash, en dash, hyphen).
SEP_RE = re.compile(r"\s+[—–-]\s+")

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Plan:
    path: Path
    h1: str
    new_title: str
    insert_after_line: int  # 0-indexed line index of `type:` (or `id:` fallback)


def split_frontmatter(text: str) -> tuple[list[str], list[str]] | None:
    """Return (frontmatter_lines, body_lines) or None if no frontmatter."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None
    lines = text.splitlines(keepends=False)
    if lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :]
    return None


def has_title_key(fm_lines: list[str]) -> bool:
    for line in fm_lines:
        if re.match(r"^title\s*:", line):
            return True
    return False


def find_first_h1(body_lines: list[str]) -> str | None:
    for line in body_lines:
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def extract_title(h1: str) -> str:
    """``S2 — Foo`` → ``Foo``; bare ``Foo`` stays ``Foo``."""
    parts = SEP_RE.split(h1, maxsplit=1)
    if len(parts) == 2 and ID_RE.match(parts[0]):
        return parts[1].strip()
    return h1.strip()


def yaml_quote(value: str) -> str:
    """Quote string for YAML scalar inline form (always double-quoted to keep punctuation safe)."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def find_insert_index(fm_lines: list[str]) -> int:
    """Insert ``title:`` right after ``type:`` (or after ``id:`` if no type line)."""
    type_idx = id_idx = -1
    for i, line in enumerate(fm_lines):
        if type_idx == -1 and re.match(r"^type\s*:", line):
            type_idx = i
        if id_idx == -1 and re.match(r"^id\s*:", line):
            id_idx = i
    if type_idx >= 0:
        return type_idx + 1
    if id_idx >= 0:
        return id_idx + 1
    return 0


def iter_task_files(vault: Path) -> list[Path]:
    files: list[Path] = []
    for sub in ("02-PROJEKTY", "07-ARCHIV/tasks-done"):
        root = vault / sub
        if not root.exists():
            continue
        for p in root.rglob("*.md"):
            parts = p.parts
            if sub == "02-PROJEKTY":
                if "tasks" not in parts:
                    continue
            files.append(p)
    return sorted(files)


def build_plan(path: Path) -> Plan | str | None:
    """Return Plan, a string error/skip reason, or None for already-good files."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        return f"unicode-error: {e}"
    parts = split_frontmatter(text)
    if parts is None:
        return "no-frontmatter"
    fm_lines, body_lines = parts
    if has_title_key(fm_lines):
        return None
    h1 = find_first_h1(body_lines)
    if not h1:
        return "no-h1"
    title = extract_title(h1)
    if not title:
        return "empty-title"
    return Plan(
        path=path,
        h1=h1,
        new_title=title,
        insert_after_line=find_insert_index(fm_lines),
    )


def apply_plan(plan: Plan) -> None:
    text = plan.path.read_text(encoding="utf-8")
    parts = split_frontmatter(text)
    assert parts is not None
    fm_lines, body_lines = parts
    new_line = f"title: {yaml_quote(plan.new_title)}"
    insert_at = plan.insert_after_line
    new_fm = fm_lines[:insert_at] + [new_line] + fm_lines[insert_at:]
    rebuilt = "---\n" + "\n".join(new_fm) + "\n---\n" + "\n".join(body_lines)
    if not rebuilt.endswith("\n"):
        rebuilt += "\n"
    plan.path.write_text(rebuilt, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="actually patch files (default: dry-run)")
    parser.add_argument("--root", type=Path, default=VAULT_DEFAULT, help="vault root (defaults to OBSIDIAN/)")
    parser.add_argument("--samples", type=int, default=8, help="sample count to print in dry-run")
    args = parser.parse_args()

    vault = args.root.resolve()
    if not vault.exists():
        print(f"vault not found: {vault}", file=sys.stderr)
        return 2

    files = iter_task_files(vault)
    plans: list[Plan] = []
    skips: dict[str, list[Path]] = {}
    for f in files:
        result = build_plan(f)
        if result is None:
            continue
        if isinstance(result, Plan):
            plans.append(result)
        else:
            skips.setdefault(result, []).append(f)

    print(f"task files scanned: {len(files)}")
    print(f"already-have-title: {len(files) - len(plans) - sum(len(v) for v in skips.values())}")
    print(f"to-patch:           {len(plans)}")
    for reason, paths in sorted(skips.items()):
        print(f"skipped ({reason}): {len(paths)}")
        for p in paths[:5]:
            print(f"   - {p.relative_to(vault)}")

    if plans:
        print("\nsamples:")
        for p in plans[: args.samples]:
            print(f"  {p.path.relative_to(vault)}")
            print(f"    H1:    {p.h1}")
            print(f"    title: {p.new_title}")

    if not args.write:
        print("\n(dry-run; re-run with --write to apply)")
        return 0

    print("\napplying patches…")
    for plan in plans:
        apply_plan(plan)
    print(f"patched {len(plans)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
