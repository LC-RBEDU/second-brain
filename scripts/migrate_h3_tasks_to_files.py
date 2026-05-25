#!/usr/bin/env python3
"""F3.3: H3 → file-per-task migration script.

Reads vault hubs (02-PROJEKTY/*.md), parses H3 task blocks + HOTOVO sections,
writes file-per-task .md files + ARCHIV files. Globally rewrites wikilinks.

Idempotentní — opakované spouštění nevytvoří duplicity, jen přeskočí existující.

Usage:
    python3 scripts/migrate_h3_tasks_to_files.py --dry-run
    python3 scripts/migrate_h3_tasks_to_files.py --execute
    python3 scripts/migrate_h3_tasks_to_files.py --execute --slug=finance
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

try:
    from unidecode import unidecode
except ImportError:
    sys.stderr.write(
        "ERROR: unidecode not installed. Run: "
        "python3 -m pip install --user --break-system-packages unidecode pyyaml\n"
    )
    sys.exit(1)

VAULT_ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN_ROOT = VAULT_ROOT / "OBSIDIAN"
PROJEKTY_DIR = OBSIDIAN_ROOT / "02-PROJEKTY"
ARCHIV_DIR = OBSIDIAN_ROOT / "07-ARCHIV" / "tasks-done"
MAPPING_FILE = VAULT_ROOT / "scripts" / "migration-mapping.json"

MAX_SLUG_LEN = 50

# === Parser regex (z sync_tasks_from_projekty.py) ===
TASK_HEAD_RE = re.compile(
    r"^###\s+(~~)?([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)(?:~~)?\s*(✅|HOTOVO)?\s*$",
    re.MULTILINE,
)
HOTOVO_SECTION_RE = re.compile(r"^##\s+.*HOTOVO", re.MULTILINE | re.IGNORECASE)
HOTOVO_HEAD_RE = re.compile(
    r"^###\s+([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)\s*✅\s*$",
    re.MULTILINE,
)
HOTOVO_ITEM_RE = re.compile(
    r"^-\s+\*\*([A-Z]+\d+[a-z]?)\*\*\s*[—–-]\s*(.+)$",
    re.MULTILINE,
)
HOTOVO_DATE_RE = re.compile(r"_\((\d{4}-\d{2}-\d{2})\)_")

PRIORITY_RE = re.compile(r"\b(ASAP|Q1|Q2|Next|Backlog|Doing)\b", re.IGNORECASE)
WAITING_RE = re.compile(
    r"\*\*Waiting\s*\|\s*Čekat\s+do:\s*(\d{4}-\d{2}-\d{2})(?:[^*]*)?\*\*",
    re.IGNORECASE,
)
WAITING_MARK_RE = re.compile(r"\*\*Waiting\b", re.IGNORECASE)
DATE_RE = re.compile(r"\*\*Vrátit se\*\*:\s*(\d{4}-\d{2}-\d{2})")
DEADLINE_RE = re.compile(r"Deadline\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
ICE_RE = re.compile(r"ICE\s+I(\d+)\s+C(\d+)\s+E(\d+)", re.IGNORECASE)
SOURCE_RE = re.compile(r"^_Zdroj:\s*(.+?)_?\s*$", re.MULTILINE)
DETAIL_RE = re.compile(r"\*\*Detail\*\*[:\s]+(.+?)(?=\n\n|\n-\s*\[|\n\*\*|\Z)", re.DOTALL)
CHECK_RE = re.compile(r"^-\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)


# === Slugify (F0.3) ===
def slugify(title: str) -> str:
    if not title:
        return ""
    s = unidecode(title)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", "-", s.strip())
    if len(s) > MAX_SLUG_LEN:
        cut = s[:MAX_SLUG_LEN].rsplit("-", 1)[0]
        s = cut if cut else s[:MAX_SLUG_LEN]
    return s.strip("-")


# === Status mapping ===
STATUS_MAP = {
    "ASAP": "ASAP",
    "Q1": "ASAP",
    "Next": "Next",
    "Q2": "Next",
    "Backlog": "Backlog",
    "Waiting": "Waiting",
    "Doing": "Doing",
}


@dataclass
class ParsedTask:
    task_id: str
    title: str
    status: str
    ice_i: int = 5
    ice_c: int = 5
    ice_e: int = 5
    deadline: Optional[str] = None
    wait_until: Optional[str] = None
    source: str = ""
    detail: str = ""
    checkboxes: list[tuple[bool, str]] = field(default_factory=list)
    is_done: bool = False
    done_date: Optional[str] = None  # for HOTOVO archives


def parse_task_block(head_match: re.Match, body: str) -> ParsedTask:
    striked = bool(head_match.group(1))
    task_id = head_match.group(2)
    title = head_match.group(3).strip()
    done_marker = head_match.group(4)
    is_done = bool(striked or done_marker)

    head_and_body = head_match.group(0) + "\n" + body[:600]

    # Status detection
    waiting_m = WAITING_RE.search(head_and_body)
    if waiting_m:
        status = "Waiting"
        wait_until = waiting_m.group(1)
    elif WAITING_MARK_RE.search(head_and_body):
        status = "Waiting"
        wait_until = None
    else:
        wait_until = None
        prio_m = PRIORITY_RE.search(head_and_body)
        status = STATUS_MAP.get(prio_m.group(1).upper() if prio_m else "Next", "Next") if prio_m else "Next"

    if is_done:
        status = "Done"

    # ICE
    ice_m = ICE_RE.search(head_and_body)
    if ice_m:
        ice_i = int(ice_m.group(1))
        ice_c = int(ice_m.group(2))
        ice_e = int(ice_m.group(3))
    else:
        ice_i, ice_c, ice_e = 5, 5, 5

    # Deadline
    deadline = None
    dm = DATE_RE.search(head_and_body)
    if dm:
        deadline = dm.group(1)
    else:
        dm = DEADLINE_RE.search(head_and_body)
        if dm:
            deadline = dm.group(1)

    # Source
    src_m = SOURCE_RE.search(body)
    source = src_m.group(1).strip() if src_m else ""

    # Detail (free-form)
    det_m = DETAIL_RE.search(body)
    detail = det_m.group(1).strip() if det_m else ""

    # Checkboxes (Operativní kroky)
    checkboxes: list[tuple[bool, str]] = []
    for cm in CHECK_RE.finditer(body):
        done = cm.group(1).lower() == "x"
        text = cm.group(2).strip()
        checkboxes.append((done, text))

    # Auto-Done if all checkboxes done and we have at least 1
    if checkboxes and all(c[0] for c in checkboxes):
        is_done = True
        status = "Done"

    return ParsedTask(
        task_id=task_id,
        title=title,
        status=status,
        ice_i=ice_i,
        ice_c=ice_c,
        ice_e=ice_e,
        deadline=deadline,
        wait_until=wait_until,
        source=source,
        detail=detail,
        checkboxes=checkboxes,
        is_done=is_done,
    )


def parse_hub(text: str) -> tuple[list[ParsedTask], dict[str, ParsedTask]]:
    """Parse hub. Returns (active_tasks, hotovo_map).

    Active = H3 outside HOTOVO section (status from priority).
    Hotovo = H3 inside HOTOVO section, or HOTOVO list items.
    """
    # Split out HOTOVO section
    hotovo_m = HOTOVO_SECTION_RE.search(text)
    if hotovo_m:
        active_text = text[:hotovo_m.start()]
        hotovo_text = text[hotovo_m.start():]
        next_h2 = re.search(r"\n##\s+", hotovo_text[1:])
        if next_h2:
            after_hotovo = hotovo_text[next_h2.end():]
            hotovo_text = hotovo_text[:next_h2.start() + 1]
            active_text += "\n" + after_hotovo
    else:
        active_text = text
        hotovo_text = ""

    active: list[ParsedTask] = []
    seen_ids: set[str] = set()

    for m in TASK_HEAD_RE.finditer(active_text):
        next_m = TASK_HEAD_RE.search(active_text, m.end())
        body = active_text[m.end():next_m.start() if next_m else len(active_text)]
        # Cut off at next ## boundary
        next_h2 = re.search(r"\n##\s+", body)
        if next_h2:
            body = body[:next_h2.start()]
        task = parse_task_block(m, body)
        if task.task_id in seen_ids:
            continue
        seen_ids.add(task.task_id)
        active.append(task)

    hotovo_map: dict[str, ParsedTask] = {}

    if hotovo_text:
        # H3 in HOTOVO section
        for m in HOTOVO_HEAD_RE.finditer(hotovo_text):
            tid = m.group(1)
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            title = m.group(2).strip()
            # Try to find date in same line context
            line_end = hotovo_text.find("\n", m.end())
            line_block = hotovo_text[m.start():line_end if line_end > 0 else len(hotovo_text)]
            date_m = HOTOVO_DATE_RE.search(line_block)
            done_date = date_m.group(1) if date_m else None

            hotovo_map[tid] = ParsedTask(
                task_id=tid,
                title=title,
                status="Done",
                is_done=True,
                done_date=done_date,
            )

        # Inline list items
        for m in HOTOVO_ITEM_RE.finditer(hotovo_text):
            tid = m.group(1)
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            text_part = m.group(2)
            text_part = re.sub(r"\s*✅.*$", "", text_part).strip()
            title = re.sub(r"\s*_\([^)]*\)_\s*$", "", text_part).strip()
            date_m = HOTOVO_DATE_RE.search(m.group(0))
            done_date = date_m.group(1) if date_m else None

            hotovo_map[tid] = ParsedTask(
                task_id=tid,
                title=title,
                status="Done",
                is_done=True,
                done_date=done_date,
            )

    # Remove from active any ID already in hotovo_map
    active = [t for t in active if t.task_id not in hotovo_map]

    # Move done active tasks to hotovo
    still_active = []
    for t in active:
        if t.is_done:
            hotovo_map[t.task_id] = t
        else:
            still_active.append(t)

    return still_active, hotovo_map


# === File generation ===
def task_filename(task_id: str, title: str) -> str:
    slug_t = slugify(title)
    if slug_t:
        return f"{task_id}-{slug_t}.md"
    return f"{task_id}.md"


_MAPPING_CACHE: dict[str, str] | None = None


def _hub_basename_for(slug: str) -> str:
    """Resolve slug → hub filename (without .md). Falls back to slug if unmapped."""
    global _MAPPING_CACHE
    if _MAPPING_CACHE is None:
        try:
            raw = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
        except Exception:
            _MAPPING_CACHE = {}
        else:
            _MAPPING_CACHE = {
                row["slug"]: row["hub_filename"].removesuffix(".md")
                for row in raw
                if row.get("slug") and row.get("hub_filename")
            }
    return _MAPPING_CACHE.get(slug, slug)


def render_task_file(task: ParsedTask, project_slug: str, source_default: str = "") -> str:
    today_str = str(date.today())
    hub_target = _hub_basename_for(project_slug)
    title_escaped = task.title.replace("\\", "\\\\").replace('"', '\\"')
    fm_lines = [
        "---",
        f"id: {task.task_id}",
        "type: task",
        f'title: "{title_escaped}"',
        f'project: "[[{hub_target}]]"',
        f"slug: {project_slug}",
        f"status: {task.status}",
        f"ice_i: {task.ice_i}",
        f"ice_c: {task.ice_c}",
        f"ice_e: {task.ice_e}",
    ]
    fm_lines.append(f"deadline:{(' ' + task.deadline) if task.deadline else ''}")
    fm_lines.append(f"waitUntil:{(' ' + task.wait_until) if task.wait_until else ''}")
    if task.is_done and task.done_date:
        fm_lines.append(f"created: {task.done_date}")
        fm_lines.append(f"updated: {task.done_date}")
    else:
        fm_lines.append(f"created: {today_str}")
        fm_lines.append(f"updated: {today_str}")
    fm_lines.append("materials: []")
    src = task.source or source_default
    src_escaped = src.replace('"', '\\"')
    fm_lines.append(f'source: "{src_escaped}"')
    fm_lines.append("blocked_by: []")
    fm_lines.append("---")

    # Body
    body_lines = [
        "",
        f"# {task.task_id} — {task.title}",
        "",
    ]
    if src:
        body_lines.append(f"**Z:** {src}")
    if task.detail:
        body_lines.append(f"**Detail:** {task.detail}")
    body_lines.append("")

    if task.is_done:
        body_lines.extend([
            "## Poznámky / log",
            f"- {task.done_date or today_str}: Done — migrováno z původního H3 bloku.",
            "",
        ])
    else:
        body_lines.append("## Operativní kroky")
        if task.checkboxes:
            for done, text in task.checkboxes:
                marker = "x" if done else " "
                body_lines.append(f"- [{marker}] {text}")
        else:
            body_lines.append("- [ ] (doplň operativní kroky)")
        body_lines.append("")
        body_lines.extend([
            "## Poznámky / log",
            f"- {today_str}: Migrováno z původního H3 bloku v hubu.",
            "",
        ])

    return "\n".join(fm_lines) + "\n".join(body_lines)


# === Main migration ===
def load_mapping() -> list[dict]:
    return json.loads(MAPPING_FILE.read_text(encoding="utf-8"))


def get_existing_ids(slug: str) -> set[str]:
    """Scan existing task soubory pro daný slug, return set of IDs."""
    ids: set[str] = set()
    tasks_dir = PROJEKTY_DIR / slug / "tasks"
    if tasks_dir.exists():
        for f in tasks_dir.glob("*.md"):
            m = re.match(r"^([A-Z]+\d+[a-z]?)", f.name)
            if m:
                ids.add(m.group(1))
    archive_dir = ARCHIV_DIR / slug
    if archive_dir.exists():
        for f in archive_dir.glob("*.md"):
            m = re.match(r"^([A-Z]+\d+[a-z]?)", f.name)
            if m:
                ids.add(m.group(1))
    return ids


def migrate_project(entry: dict, dry_run: bool, only_slug: Optional[str]) -> dict:
    slug = entry["slug"]
    if only_slug and slug != only_slug:
        return {"slug": slug, "skipped": True, "reason": "filtered by --slug"}
    if entry.get("skip"):
        return {
            "slug": slug,
            "skipped": True,
            "reason": entry.get("skip_reason", "skip:true in mapping"),
        }

    hub_path = PROJEKTY_DIR / entry["hub_filename"]
    if not hub_path.exists():
        return {"slug": slug, "skipped": True, "reason": f"hub not found: {hub_path}"}

    text = hub_path.read_text(encoding="utf-8")
    active, hotovo_map = parse_hub(text)

    existing_ids = get_existing_ids(slug)
    written: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    tasks_dir = PROJEKTY_DIR / slug / "tasks"
    archive_dir = ARCHIV_DIR / slug

    for task in active:
        target = tasks_dir / task_filename(task.task_id, task.title)
        if task.task_id in existing_ids or target.exists():
            skipped.append(f"  skip {task.task_id} (already exists in tasks/ or archive)")
            continue
        content = render_task_file(task, slug)
        if dry_run:
            written.append(f"  WRITE {target.relative_to(VAULT_ROOT)} ({len(content)}B)")
        else:
            tasks_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(f"  WROTE {target.relative_to(VAULT_ROOT)}")

    for tid, task in hotovo_map.items():
        target = archive_dir / task_filename(task.task_id, task.title)
        if task.task_id in existing_ids or target.exists():
            skipped.append(f"  skip {task.task_id} (already exists)")
            continue
        content = render_task_file(task, slug)
        if dry_run:
            written.append(f"  WRITE {target.relative_to(VAULT_ROOT)} ({len(content)}B)")
        else:
            archive_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(f"  WROTE {target.relative_to(VAULT_ROOT)}")

    return {
        "slug": slug,
        "active_parsed": len(active),
        "hotovo_parsed": len(hotovo_map),
        "written": written,
        "skipped": skipped,
        "errors": errors,
    }


# === Wikilink rewrite ===
def rewrite_wikilinks(mapping: list[dict], dry_run: bool) -> dict:
    """Rewrite [[02-PROJEKTY/<HubFilename>]] → [[<slug>]] across vault.

    Skip Templates/, Bases/, .obsidian/. Skip anchor references.
    """
    rewrites: dict[str, str] = {}
    for entry in mapping:
        hub_no_ext = entry["hub_filename"][:-3] if entry["hub_filename"].endswith(".md") else entry["hub_filename"]
        slug = entry["slug"]
        rewrites[f"[[02-PROJEKTY/{hub_no_ext}]]"] = f"[[{slug}]]"
        rewrites[f"[[02-PROJEKTY/{hub_no_ext}|"] = f"[[{slug}|"

    skip_dirs = {"00-System/Templates", "00-System/Bases", ".obsidian"}
    files_changed: list[str] = []
    total_replacements = 0

    for md_file in OBSIDIAN_ROOT.rglob("*.md"):
        rel = md_file.relative_to(OBSIDIAN_ROOT).as_posix()
        if any(rel.startswith(d) for d in skip_dirs):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        for old, new in rewrites.items():
            text = text.replace(old, new)
        if text != original:
            replacements = sum(text.count(new) - original.count(new) for old, new in rewrites.items())
            total_replacements += replacements
            files_changed.append(f"  {rel} ({replacements} replacement(s))")
            if not dry_run:
                md_file.write_text(text, encoding="utf-8")

    return {
        "rewrites": rewrites,
        "files_changed": files_changed,
        "total_replacements": total_replacements,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="No-write preview")
    parser.add_argument("--execute", action="store_true", help="Actually write changes")
    parser.add_argument("--slug", help="Migrate only single project slug (debugging)")
    parser.add_argument("--skip-wikilinks", action="store_true", help="Skip global wikilink rewrite")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        sys.stderr.write("ERROR: pass --dry-run or --execute\n")
        sys.exit(2)

    dry_run = args.dry_run

    print("=" * 70)
    print(f"H3 → file-per-task migration ({'DRY-RUN' if dry_run else 'EXECUTE'})")
    print(f"Vault root: {VAULT_ROOT}")
    print("=" * 70)

    mapping = load_mapping()
    summary = {"projects_migrated": 0, "projects_skipped": 0, "tasks_written": 0}

    for entry in mapping:
        result = migrate_project(entry, dry_run, args.slug)
        print(f"\n--- {entry['slug']} ({entry['hub_filename']}) ---")
        if result.get("skipped"):
            print(f"  SKIPPED: {result.get('reason', '')}")
            summary["projects_skipped"] += 1
            continue
        summary["projects_migrated"] += 1
        print(f"  Active parsed: {result['active_parsed']}")
        print(f"  HOTOVO parsed: {result['hotovo_parsed']}")
        for w in result["written"]:
            print(w)
            summary["tasks_written"] += 1
        for s in result["skipped"]:
            print(s)
        for e in result["errors"]:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 70)
    print("WIKILINK REWRITE")
    print("=" * 70)
    if args.skip_wikilinks:
        print("  Skipped (--skip-wikilinks)")
    else:
        wl = rewrite_wikilinks(mapping, dry_run)
        print(f"  Patterns: {len(wl['rewrites'])}")
        print(f"  Files changed: {len(wl['files_changed'])}")
        print(f"  Total replacements: {wl['total_replacements']}")
        for fc in wl["files_changed"][:50]:
            print(fc)
        if len(wl["files_changed"]) > 50:
            print(f"  ... and {len(wl['files_changed']) - 50} more")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {summary['projects_migrated']} migrated, "
          f"{summary['projects_skipped']} skipped, "
          f"{summary['tasks_written']} task files written")
    print("=" * 70)


if __name__ == "__main__":
    main()
