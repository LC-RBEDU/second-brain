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

_LIB = Path(__file__).resolve().parents[1] / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from today_priority import select_top_priority  # noqa: E402
from hub_state import (  # noqa: E402
    STALE_AREA_WEEKS,
    STALE_NARRATIVE_DAYS,
    compute_last_task_activity,
    is_narrative_stale,
)

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
    source: str | None = None
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
            "source": self.source,
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
    sources: list[str] = None
    notebooklm: list[str] = None
    workspace: dict[str, Any] | None = None
    context_source: str | None = None
    charter_scope: str | None = None
    charter_kontext: str | None = None
    has_zdroje_dat: bool = False

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
            "sources": self.sources or [],
            "notebooklm": self.notebooklm or [],
            "workspace": self.workspace or {},
            "context_source": self.context_source,
            "charter_scope": self.charter_scope,
            "charter_kontext": self.charter_kontext,
            "has_zdroje_dat": self.has_zdroje_dat,
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


def _section_excerpt(body: str, heading: str, max_len: int = 800) -> str | None:
    pat = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    m = pat.search(body)
    if not m:
        return None
    rest = body[m.end() :]
    nxt = re.search(r"^##\s+\S", rest, re.MULTILINE)
    block = (rest[: nxt.start()] if nxt else rest).strip()
    if len(block) > max_len:
        block = block[: max_len - 20] + "…"
    return block or None


def _workspace_dict(v: Any) -> dict[str, list[str]] | None:
    if not v or not isinstance(v, dict):
        return None
    out: dict[str, list[str]] = {}
    for k in ("calendar", "gmail", "drive"):
        out[k] = _list_str(v.get(k))
    return out


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
            sources=_list_str(fm.get("sources")),
            notebooklm=_list_str(fm.get("notebooklm")),
            workspace=_workspace_dict(fm.get("workspace")),
            context_source=fm.get("context_source"),
            charter_scope=_section_excerpt(body, "## Scope"),
            charter_kontext=_section_excerpt(body, "## Kontext"),
            has_zdroje_dat="## Zdroje dat" in body,
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
                source=fm.get("source"),
                is_recurring=bool(fm.get("recurring")),
                extra_module=fm.get("extra_module"),
            ))
    return out


def collect_areas(vault: Path) -> list[dict]:
    areas_dir = vault / "03-AREAS"
    if not areas_dir.exists():
        return []
    out: list[dict] = []
    for f in sorted(areas_dir.glob("*.md")):
        if f.name.startswith("_"):
            continue
        try:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        if (fm.get("type") or "").lower() != "area":
            continue
        projects = fm.get("projects") or []
        if isinstance(projects, str):
            projects = [projects]
        out.append({
            "slug": fm.get("slug") or f.stem,
            "filename": f.name,
            "title": f.stem,
            "projects": list(projects),
            "updated": _date_str(fm.get("updated")),
            "review_cadence": fm.get("review_cadence") or "weekly",
        })
    return out


def compute_stale_areas(
    areas: list[dict],
    active_tasks: list[TaskInfo],
    today: date,
    *,
    threshold_weeks: int = STALE_AREA_WEEKS,
) -> list[dict]:
    threshold = today - timedelta(days=threshold_weeks * 7)
    stale: list[dict] = []
    for area in areas:
        slugs = set(area.get("projects") or [])
        area_tasks = [t for t in active_tasks if t.slug in slugs]
        open_in_area = [t for t in area_tasks if t.status != "Done"]
        last_act = compute_last_task_activity(area_tasks)
        if not open_in_area and not last_act:
            continue
        if last_act and last_act >= threshold:
            continue
        if not last_act and open_in_area:
            # has open tasks but no updated dates — not stale
            continue
        stale.append({
            "slug": area["slug"],
            "filename": area["filename"],
            "projects": list(slugs),
            "last_task_activity": last_act.isoformat() if last_act else None,
            "open_tasks_in_area": len(open_in_area),
        })
    return stale


def build_snapshot(vault: Path) -> dict:
    today = date.today()
    today_str = today.isoformat()
    projects = collect_projects(vault)
    areas = collect_areas(vault)
    active_tasks = collect_tasks(vault, archive=False)
    archived = collect_tasks(vault, archive=True)

    open_count_by_slug: dict[str, int] = {}
    for t in active_tasks:
        if t.status != "Done":
            open_count_by_slug[t.slug] = open_count_by_slug.get(t.slug, 0) + 1
    for p in projects:
        p.open_tasks_count = open_count_by_slug.get(p.slug, 0)

    open_tasks = [t for t in active_tasks if t.status != "Done"]
    top_priority_today, top_priority = select_top_priority(open_tasks, today)

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

    stale_hubs: list[dict] = []
    for p in projects:
        slug_tasks = [t for t in active_tasks if t.slug == p.slug]
        arch_slug = [t for t in archived if t.slug == p.slug]
        last_act = compute_last_task_activity(slug_tasks + arch_slug)
        if is_narrative_stale(p.updated, last_act, threshold_days=STALE_NARRATIVE_DAYS):
            stale_hubs.append({
                "slug": p.slug,
                "hub_filename": p.hub_filename,
                "hub_updated": p.updated,
                "last_task_activity": last_act.isoformat() if last_act else None,
                "open_tasks_count": p.open_tasks_count,
            })

    stale_areas = compute_stale_areas(areas, active_tasks, today)

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
        "areas": areas,
        "priority_rules": {
            "base": "priority_score = (ice_i * ice_c) / ice_e",
            "today_score": "priority_score + urgency_bonus(deadline)",
            "urgency_bonus": {
                "overdue": 35,
                "deadline_today": 30,
                "deadline_tomorrow": 15,
            },
            "top_eligible": "ASAP always; Next only when no open ASAP; never Waiting/Backlog",
            "sort": "today_score DESC",
        },
        "top_priority_today": top_priority_today,
        "top_priority": top_priority,
        "recently_done": [t.to_dict() for t in recently_done[:25]],
        "upcoming_deadlines": [t.to_dict() for t in upcoming],
        "recurring_pending": [t.to_dict() for t in recurring_done],
        "blocked_by_graph": blocked,
        "stale_hubs": stale_hubs,
        "stale_areas": stale_areas,
        "health": {
            "stale_narrative_days": STALE_NARRATIVE_DAYS,
            "stale_hubs_count": len(stale_hubs),
            "stale_areas_weeks": STALE_AREA_WEEKS,
            "stale_areas_count": len(stale_areas),
        },
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
