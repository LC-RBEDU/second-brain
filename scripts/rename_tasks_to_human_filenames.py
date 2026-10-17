#!/usr/bin/env python3
"""Rename task files to human-readable convention `<ID> — <Title>.md`.

Drives the F-fundamental refactor:
1. Rename `02-PROJEKTY/<slug>/tasks/<ID>-<slugify>.md` (+ archive variant) to
   `<ID> — <sanitize(title)>.md` (em-dash U+2014).
2. Rewrite wikilinks across the whole `OBSIDIAN/` vault — bare, pipe-aliased,
   anchor, and path-style variants.
3. Append `<ID>` to `aliases:` in each task frontmatter so `[[<ID>]]` keeps
   resolving in Obsidian.
4. Re-number subtasks in detected `##` "operativní" sections with
   `**<ID>-N**` prefix.

Dry-run by default; pass `--write` to actually mutate the vault.

Usage:
    python3 scripts/rename_tasks_to_human_filenames.py            # dry-run
    python3 scripts/rename_tasks_to_human_filenames.py --write    # apply
"""
from __future__ import annotations

import os

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: pyyaml not installed. Run: "
        "pip3 install --user --break-system-packages pyyaml\n"
    )
    sys.exit(1)

VAULT_ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN_ROOT = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault"))
PROJEKTY_DIR = OBSIDIAN_ROOT / "02-PROJEKTY"
ARCHIV_DIR = OBSIDIAN_ROOT / "07-ARCHIV" / "tasks-done"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)

EM_DASH = "\u2014"  # —
SEPARATOR = f" {EM_DASH} "

OPERATIONAL_HEADERS = {
    "## Operativní kroky",
    "## Akční kroky",
    "## Subtasky",
    "## Steps",
    "## Akční položky",
}

WIKILINK_SCAN_DIRS = (
    "00-System",
    "01-INBOX",
    "02-PROJEKTY",
    "03-AREAS",
    "05-RESOURCES",
    "06-CANVAS",
    "07-ARCHIV",
)


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

def sanitize_title(title: str) -> str:
    """Filesystem + Google-Drive safe rendering of a human-readable title.

    Mirrors the table in the spec. Keeps diacritics + emoji intact; only
    replaces FS-hostile chars.
    """
    if not title:
        return ""
    s = title
    s = s.replace("\n", " ").replace("\t", " ").replace("\r", " ")
    s = s.replace(":", " ")
    s = s.replace("/", " -")
    s = s.replace("\\", " -")
    s = s.replace("?", "")
    s = s.replace("*", "")
    s = s.replace("<", "\u2039")
    s = s.replace(">", "\u203a")
    s = s.replace("|", "-")
    s = s.replace('"', "'")
    s = "".join(ch for ch in s if ord(ch) >= 0x20)
    s = re.sub(r" +", " ", s).strip()
    return s


def task_filename(task_id: str, title: str) -> str:
    sanitized = sanitize_title(title or "")
    if sanitized:
        return f"{task_id}{SEPARATOR}{sanitized}.md"
    return f"{task_id}.md"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

@dataclass
class TaskFile:
    path: Path
    rel_path: str
    frontmatter: dict
    body: str
    archive: bool

    @property
    def task_id(self) -> str:
        return str(self.frontmatter.get("id") or "")

    @property
    def title(self) -> str:
        return str(self.frontmatter.get("title") or "")

    @property
    def old_stem(self) -> str:
        return self.path.stem

    @property
    def new_filename(self) -> str:
        return task_filename(self.task_id, self.title)

    @property
    def new_stem(self) -> str:
        return self.new_filename[:-3]

    @property
    def new_path(self) -> Path:
        return self.path.parent / self.new_filename


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def discover_tasks() -> list[TaskFile]:
    out: list[TaskFile] = []

    for tasks_dir in sorted(PROJEKTY_DIR.glob("*/tasks")):
        if not tasks_dir.is_dir():
            continue
        for md in sorted(tasks_dir.glob("*.md")):
            tf = _load_task(md, archive=False)
            if tf is not None:
                out.append(tf)

    if ARCHIV_DIR.exists():
        for slug_dir in sorted(ARCHIV_DIR.iterdir()):
            if not slug_dir.is_dir():
                continue
            for md in sorted(slug_dir.glob("*.md")):
                tf = _load_task(md, archive=True)
                if tf is not None:
                    out.append(tf)

    return out


def _load_task(path: Path, archive: bool) -> TaskFile | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ! cannot read {path}: {e}", file=sys.stderr)
        return None
    fm, body = parse_frontmatter(text)
    if (fm.get("type") or "task").lower() != "task":
        return None
    tid = str(fm.get("id") or "")
    if not tid:
        return None
    rel_path = str(path.relative_to(OBSIDIAN_ROOT))
    return TaskFile(path=path, rel_path=rel_path, frontmatter=fm, body=body, archive=archive)


# ---------------------------------------------------------------------------
# Aliases + subtask renumber
# ---------------------------------------------------------------------------

def ensure_id_in_aliases(fm: dict, task_id: str) -> dict:
    new_fm = dict(fm)
    existing = new_fm.get("aliases")
    if existing is None:
        new_fm["aliases"] = [task_id]
        return new_fm
    if isinstance(existing, str):
        existing_list = [existing]
    elif isinstance(existing, list):
        existing_list = [str(x) for x in existing if x]
    else:
        existing_list = [str(existing)]
    if task_id not in existing_list:
        existing_list.append(task_id)
    new_fm["aliases"] = existing_list
    return new_fm


_LEADING_NUM_PATTERNS = [
    re.compile(r"^\*\*([A-Z]+\d+[a-z]?)-\d+\*\*\s+"),
    re.compile(r"^\*\*\d+\.\*\*\s+"),
    re.compile(r"^\*\*\d+\)\*\*\s+"),
    re.compile(r"^\d+\.\s+"),
    re.compile(r"^\d+\)\s+"),
]


def _strip_existing_prefix(text: str) -> str:
    for pat in _LEADING_NUM_PATTERNS:
        m = pat.match(text)
        if m:
            return text[m.end():]
    return text


_CHECKBOX_RE = re.compile(r"^(\s*-\s+\[[ xX]\]\s+)(.*)$")


def renumber_subtasks(body: str, task_id: str) -> tuple[str, int]:
    """Walk body, find ## sections in OPERATIONAL_HEADERS, and replace each
    checkbox item with `- [<state>] **<ID>-N** <text>` (1-indexed per section).
    """
    lines = body.splitlines()
    out: list[str] = []
    in_op_section = False
    counter = 0
    changes = 0

    for line in lines:
        if line.startswith("## "):
            in_op_section = line.strip() in OPERATIONAL_HEADERS
            counter = 0
            out.append(line)
            continue

        if in_op_section:
            m = _CHECKBOX_RE.match(line)
            if m:
                prefix = m.group(1)
                rest = m.group(2)
                cleaned = _strip_existing_prefix(rest)
                counter += 1
                new_line = f"{prefix}**{task_id}-{counter}** {cleaned}"
                if new_line != line:
                    changes += 1
                out.append(new_line)
                continue
            out.append(line)
            continue

        out.append(line)

    new_body = "\n".join(out)
    if body.endswith("\n") and not new_body.endswith("\n"):
        new_body += "\n"
    return new_body, changes


# ---------------------------------------------------------------------------
# YAML serialization preserving order
# ---------------------------------------------------------------------------

PREFERRED_ORDER = [
    "id", "type", "title", "project", "slug", "aliases",
    "status", "ice_i", "ice_c", "ice_e",
    "deadline", "waitUntil", "created", "updated", "done_at",
    "materials", "source", "blocked_by",
    "recurring", "extra_module", "extra_state_file",
]


def serialize_frontmatter(fm: dict) -> str:
    ordered: dict = {}
    for key in PREFERRED_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key not in ordered:
            ordered[key] = value
    return yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=1000,
    )


def render_task_text(fm: dict, body: str) -> str:
    fm_text = serialize_frontmatter(fm)
    if not body.endswith("\n"):
        body = body + "\n"
    return f"---\n{fm_text}---\n{body}"


# ---------------------------------------------------------------------------
# Wikilink rewrite
# ---------------------------------------------------------------------------

def build_wikilink_table(tasks: list[TaskFile]) -> dict[str, str]:
    table: dict[str, str] = {}
    for t in tasks:
        if t.old_stem == t.new_stem:
            continue
        table[t.old_stem] = t.new_stem
    return table


def _build_wikilink_regex(stems: Iterable[str]) -> re.Pattern[str]:
    alternatives = "|".join(sorted((re.escape(s) for s in stems), key=len, reverse=True))
    if not alternatives:
        return re.compile(r"(?!x)x")
    return re.compile(
        r"\[\["
        r"((?:[^\[\]#|]*?/)?"
        r"(?:" + alternatives + r"))"
        r"(?=[\]|#])"
    )


def rewrite_wikilinks_in_text(text: str, table: dict[str, str], pattern: re.Pattern[str]) -> tuple[str, int]:
    if not table:
        return text, 0

    def _sub(m: re.Match[str]) -> str:
        full_target = m.group(1)
        if "/" in full_target:
            prefix, stem = full_target.rsplit("/", 1)
            prefix = prefix + "/"
        else:
            prefix, stem = "", full_target
        if stem not in table:
            return m.group(0)
        return f"[[{prefix}{table[stem]}"

    new_text, n = pattern.subn(_sub, text)
    return new_text, n


def iter_vault_md_files() -> Iterable[Path]:
    for sub in WIKILINK_SCAN_DIRS:
        base = OBSIDIAN_ROOT / sub
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            yield path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    total_tasks: int = 0
    rename_planned: int = 0
    rename_done: int = 0
    rename_skipped_idempotent: int = 0
    rename_collisions: list[str] = field(default_factory=list)
    wikilink_files_changed: int = 0
    wikilink_replacements: int = 0
    aliases_added: int = 0
    subtasks_renumbered: int = 0
    frontmatter_rewritten: int = 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--skip-wikilinks", action="store_true")
    parser.add_argument("--skip-subtasks", action="store_true")
    parser.add_argument("--skip-aliases", action="store_true")
    parser.add_argument("--no-rename", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    dry_run = not args.write

    print("=" * 70)
    print(f"rename_tasks_to_human_filenames — {'DRY-RUN' if dry_run else 'WRITE'}")
    print(f"vault root: {OBSIDIAN_ROOT}")
    print("=" * 70)

    tasks = discover_tasks()
    stats = Stats(total_tasks=len(tasks))
    print(f"Discovered {len(tasks)} task files (live + archive).\n")

    # Build planned renames (resolve collisions)
    planned_renames: dict[int, Path] = {}  # id(task) -> new_path
    new_path_owner: dict[Path, TaskFile] = {}
    for t in tasks:
        if t.new_path == t.path:
            stats.rename_skipped_idempotent += 1
            continue
        owner = new_path_owner.get(t.new_path)
        if owner is not None:
            stats.rename_collisions.append(
                f"  ! collision: {t.rel_path} → {t.new_path.relative_to(OBSIDIAN_ROOT)}"
                f" already planned by {owner.rel_path}"
            )
            continue
        # If the target file exists but is not one of our tasks being renamed away
        existing_task_at_target = next(
            (ot for ot in tasks if ot.path == t.new_path), None
        )
        if t.new_path.exists() and existing_task_at_target is None:
            stats.rename_collisions.append(
                f"  ! collision: {t.rel_path} → {t.new_path.relative_to(OBSIDIAN_ROOT)}"
                f" target file already exists (unrelated)"
            )
            continue
        planned_renames[id(t)] = t.new_path
        new_path_owner[t.new_path] = t
        stats.rename_planned += 1

    print(f"Rename plan: {stats.rename_planned} files "
          f"({stats.rename_skipped_idempotent} already conform, "
          f"{len(stats.rename_collisions)} collisions).\n")
    for c in stats.rename_collisions:
        print(c)

    # Build wikilink rewrite table from planned renames
    planned_tasks = [t for t in tasks if id(t) in planned_renames] if not args.no_rename else []
    wikilink_table = build_wikilink_table(planned_tasks)
    pattern = _build_wikilink_regex(wikilink_table.keys())

    # Step: rewrite each task body (subtasks + aliases) + execute rename
    for t in tasks:
        new_fm = t.frontmatter
        new_body = t.body
        changed = False

        if not args.skip_aliases:
            updated_fm = ensure_id_in_aliases(t.frontmatter, t.task_id)
            if updated_fm != t.frontmatter:
                new_fm = updated_fm
                stats.aliases_added += 1
                changed = True

        if not args.skip_subtasks:
            renumbered, n_changes = renumber_subtasks(new_body, t.task_id)
            if n_changes:
                new_body = renumbered
                stats.subtasks_renumbered += n_changes
                changed = True

        new_text = render_task_text(new_fm, new_body) if changed else None
        rename_target = planned_renames.get(id(t)) if not args.no_rename else None

        if dry_run:
            if rename_target is not None:
                rel_new = rename_target.relative_to(OBSIDIAN_ROOT)
                print(f"  RENAME {t.rel_path} → {rel_new}"
                      + ("  [+aliases]" if not args.skip_aliases and "aliases" not in t.frontmatter else "")
                      + (f"  [+{n_changes if (not args.skip_subtasks and 'n_changes' in dir()) else 0} subtask renum]" if changed and not args.skip_subtasks else ""))
            elif changed and args.verbose:
                print(f"  REWRITE {t.rel_path} (frontmatter / subtasks only)")
            continue

        # WRITE mode
        if rename_target is not None:
            rename_target.parent.mkdir(parents=True, exist_ok=True)
            text_to_write = new_text if new_text is not None else t.path.read_text(encoding="utf-8")
            rename_target.write_text(text_to_write, encoding="utf-8")
            try:
                if rename_target.resolve() != t.path.resolve():
                    t.path.unlink()
            except OSError as e:
                print(f"  ! unlink failed for {t.path}: {e}", file=sys.stderr)
            stats.rename_done += 1
            if new_text is not None:
                stats.frontmatter_rewritten += 1
        elif new_text is not None:
            t.path.write_text(new_text, encoding="utf-8")
            stats.frontmatter_rewritten += 1

    # Wikilink rewrite across vault
    if not args.skip_wikilinks and wikilink_table:
        print(f"\nWikilink rewrite — {len(wikilink_table)} stem mappings.")
        for path in iter_vault_md_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new_text, n = rewrite_wikilinks_in_text(text, wikilink_table, pattern)
            if n:
                stats.wikilink_files_changed += 1
                stats.wikilink_replacements += n
                rel = path.relative_to(OBSIDIAN_ROOT)
                print(f"  {'WOULD UPDATE' if dry_run else 'UPDATED'} {rel} ({n} link(s))")
                if not dry_run:
                    path.write_text(new_text, encoding="utf-8")

    print("\n" + "=" * 70)
    print(
        f"SUMMARY (mode={'DRY-RUN' if dry_run else 'WRITE'}):\n"
        f"  total_tasks            = {stats.total_tasks}\n"
        f"  rename_planned         = {stats.rename_planned}\n"
        f"  rename_done            = {stats.rename_done}\n"
        f"  rename_skipped_noop    = {stats.rename_skipped_idempotent}\n"
        f"  rename_collisions      = {len(stats.rename_collisions)}\n"
        f"  aliases_added          = {stats.aliases_added}\n"
        f"  subtasks_renumbered    = {stats.subtasks_renumbered}\n"
        f"  frontmatter_rewritten  = {stats.frontmatter_rewritten}\n"
        f"  wikilink_files_changed = {stats.wikilink_files_changed}\n"
        f"  wikilink_replacements  = {stats.wikilink_replacements}\n"
    )
    if dry_run:
        print("Dry-run only — pass --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
