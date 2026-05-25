#!/usr/bin/env python3
"""F8.2 (local): Build agent-context.json snapshot from local Obsidian vault.

Reads:
- 02-PROJEKTY/<Hub>.md (project frontmatter + charter)
- 02-PROJEKTY/<slug>/tasks/*.md (active tasks)
- 07-ARCHIV/tasks-done/<slug>/*.md (recently archived)

Writes:
- 00-System/agent-context.json

Usage:
    python3 scripts/build_agent_context.py
    python3 scripts/build_agent_context.py --vault PATH       # custom vault root
    python3 scripts/build_agent_context.py --dry-run

Designed to run in <2s for typical vault size (every-write trigger or hooked into
agenda-* skills). For VPS cron, see vps/second-brain-hub/cron/build_agent_context.py
which uses DriveVault.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: pyyaml not installed. Run: pip3 install --user --break-system-packages pyyaml\n"
    )
    sys.exit(1)

DEFAULT_VAULT = Path(
    os.environ.get(
        "SECOND_BRAIN_VAULT",
        str(Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"),
    )
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
HUB_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass
class TaskInfo:
    id: str
    slug: str
    status: str
    title: str
    rel_path: str
    ice_i: int = 5
    ice_c: int = 5
    ice_e: int = 5
    deadline: str | None = None
    waitUntil: str | None = None
    updated: str | None = None
    materials: list[str] = None
    blocked_by: list[str] = None
    is_recurring: bool = False
    extra_module: str | None = None

    @property
    def priority_score(self) -> float:
        e = max(self.ice_e or 1, 1)
        return round((self.ice_i * self.ice_c) / e, 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "status": self.status,
            "title": self.title,
            "rel_path": self.rel_path,
            "ice_i": self.ice_i,
            "ice_c": self.ice_c,
            "ice_e": self.ice_e,
            "priority_score": self.priority_score,
            "deadline": self.deadline,
            "waitUntil": self.waitUntil,
            "updated": self.updated,
            "materials": self.materials or [],
            "blocked_by": self.blocked_by or [],
            "is_recurring": self.is_recurring,
            "extra_module": self.extra_module,
        }


@dataclass
class ProjectInfo:
    slug: str
    hub_filename: str
    title: str
    status: str
    aliases: list[str]
    area: str | None = None
    open_tasks_count: int = 0
    updated: str | None = None

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "hub_filename": self.hub_filename,
            "title": self.title,
            "status": self.status,
            "aliases": self.aliases,
            "area": self.area,
            "open_tasks_count": self.open_tasks_count,
            "updated": self.updated,
        }


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
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


def _to_int(v: Any, default: int = 5) -> int:
    try:
        return int(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def _date_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v).strip()
    return s or None


def _list_str(v: Any) -> list[str]:
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def collect_projects(vault: Path) -> list[ProjectInfo]:
    projekty = vault / "02-PROJEKTY"
    if not projekty.exists():
        return []
    out: list[ProjectInfo] = []
    for hub in sorted(projekty.glob("*.md")):
        if hub.name.startswith("_"):
            continue
        try:
            text = hub.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, body = parse_frontmatter(text)
        if (fm.get("type") or "").lower() != "project":
            continue
        slug = fm.get("slug") or hub.stem.lower().replace(" ", "-")
        title = (HUB_TITLE_RE.search(body) or [None, fm.get("title") or hub.stem])[1] if HUB_TITLE_RE.search(body) else (fm.get("title") or hub.stem)
        out.append(ProjectInfo(
            slug=slug,
            hub_filename=hub.name,
            title=str(title).strip(),
            status=str(fm.get("status") or "active"),
            aliases=_list_str(fm.get("aliases")),
            area=fm.get("area"),
            updated=_date_str(fm.get("updated")),
        ))
    return out


def collect_tasks(vault: Path, archive: bool = False) -> list[TaskInfo]:
    base = vault / ("07-ARCHIV/tasks-done" if archive else "02-PROJEKTY")
    if not base.exists():
        return []
    out: list[TaskInfo] = []
    for slug_dir in sorted(base.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        if archive:
            tasks_dir = slug_dir
        else:
            tasks_dir = slug_dir / "tasks"
            if not tasks_dir.exists():
                continue
        for task_file in sorted(tasks_dir.glob("*.md")):
            try:
                text = task_file.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = parse_frontmatter(text)
            if (fm.get("type") or "task").lower() != "task":
                continue
            tid = str(fm.get("id") or "")
            if not tid:
                continue
            title = str(fm.get("title") or "").strip()
            if not title:
                mt = HUB_TITLE_RE.search(body)
                if mt:
                    title = re.sub(rf"^{re.escape(tid)}\s*[—–-]\s*", "", mt.group(1).strip()).strip()
            try:
                rel_path = str(task_file.relative_to(vault))
            except ValueError:
                rel_path = str(task_file)
            out.append(TaskInfo(
                id=tid,
                slug=str(fm.get("slug") or slug),
                status=str(fm.get("status") or "Next"),
                title=title or tid,
                rel_path=rel_path,
                ice_i=_to_int(fm.get("ice_i"), 5),
                ice_c=_to_int(fm.get("ice_c"), 5),
                ice_e=_to_int(fm.get("ice_e"), 5),
                deadline=_date_str(fm.get("deadline")),
                waitUntil=_date_str(fm.get("waitUntil")),
                updated=_date_str(fm.get("updated")),
                materials=_list_str(fm.get("materials")),
                blocked_by=_list_str(fm.get("blocked_by")),
                is_recurring=bool(fm.get("recurring")),
                extra_module=fm.get("extra_module"),
            ))
    return out


def build_snapshot(vault: Path) -> dict:
    today = date.today()
    today_str = today.isoformat()
    projects = collect_projects(vault)
    active_tasks = collect_tasks(vault, archive=False)
    archived = collect_tasks(vault, archive=True)

    open_count_by_slug: dict[str, int] = {}
    for t in active_tasks:
        if t.status != "Done":
            open_count_by_slug[t.slug] = open_count_by_slug.get(t.slug, 0) + 1
    for p in projects:
        p.open_tasks_count = open_count_by_slug.get(p.slug, 0)

    open_tasks = [t for t in active_tasks if t.status != "Done"]
    open_tasks.sort(key=lambda t: -t.priority_score)
    top_priority = open_tasks[:15]

    week_ago = today - timedelta(days=7)
    recently_done = []
    for t in archived + active_tasks:
        if t.status != "Done":
            continue
        if not t.updated:
            continue
        try:
            d = date.fromisoformat(t.updated[:10])
        except ValueError:
            continue
        if d >= week_ago:
            recently_done.append(t)
    recently_done.sort(key=lambda t: t.updated or "", reverse=True)

    upcoming = []
    soon = today + timedelta(days=7)
    for t in open_tasks:
        if not t.deadline:
            continue
        try:
            d = date.fromisoformat(t.deadline[:10])
        except ValueError:
            continue
        if today <= d <= soon:
            upcoming.append(t)
    upcoming.sort(key=lambda t: t.deadline or "")

    recurring_done = [t for t in active_tasks if t.is_recurring and t.status == "Done"]
    blocked = {t.id: t.blocked_by for t in active_tasks if t.blocked_by}

    return {
        "version": 2,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "vault_path": str(vault),
        "today": today_str,
        "stats": {
            "active_projects": sum(1 for p in projects if p.status in ("active", "")),
            "total_open_tasks": len(open_tasks),
            "recently_done_7d": len(recently_done),
            "upcoming_deadlines_7d": len(upcoming),
            "recurring_pending_rotation": len(recurring_done),
        },
        "projects": [p.to_dict() for p in projects],
        "top_priority": [t.to_dict() for t in top_priority],
        "recently_done": [t.to_dict() for t in recently_done[:25]],
        "upcoming_deadlines": [t.to_dict() for t in upcoming],
        "recurring_pending": [t.to_dict() for t in recurring_done],
        "blocked_by_graph": blocked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.vault.exists():
        sys.stderr.write(f"ERROR: vault not found: {args.vault}\n")
        return 1

    snapshot = build_snapshot(args.vault)
    out = args.out or (args.vault / "00-System" / "agent-context.json")

    if args.dry_run:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2)[:2000])
        print(f"\n(dry-run, would write to {out})")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = snapshot["stats"]
    print(
        f"agent-context: projects={stats['active_projects']} "
        f"open={stats['total_open_tasks']} "
        f"done7d={stats['recently_done_7d']} "
        f"upcoming={stats['upcoming_deadlines_7d']} "
        f"→ {out.relative_to(args.vault) if out.is_relative_to(args.vault) else out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
