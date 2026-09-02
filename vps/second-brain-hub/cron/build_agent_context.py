#!/usr/bin/env python3
"""F8.2 (VPS): Build agent-context.json snapshot from Drive vault.

Cron runs every 15 min during workhours (07-22). See deploy/crontab.

Reads via DriveVault, writes 00-System/agent-context.json (no CAS — single writer).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402
from task_io import (  # noqa: E402
    iter_active_tasks,
    iter_archive_tasks,
    parse_iso_date,
    parse_task_text,
)
from focus import (  # noqa: E402
    FOCUS_LIMIT,
    STATUS_CANCELLED,
    STATUS_DONE,
    current_focus_week,
    is_focus_current,
    is_terminal,
    normalise_agent,
    parse_focus,
)
from lifecycle_promotion import select_focus_suggestions  # noqa: E402
from today_priority import (  # noqa: E402
    URGENCY_BONUS_OVERDUE,
    URGENCY_BONUS_TODAY,
    URGENCY_BONUS_TOMORROW,
    is_queue_eligible,
    select_top_priority,
)
from task_identity import check_task_identity  # noqa: E402
from hub_state import (  # noqa: E402
    STALE_AREA_WEEKS,
    STALE_NARRATIVE_DAYS,
    compute_last_task_activity,
    is_narrative_stale,
)
from hierarchy import (  # noqa: E402
    TYPE_EPIC,
    normalise_work_type,
    parse_parent_id,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
OUTPUT_REL = "00-System/agent-context.json"
HUB_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _to_int(v, default=5):
    try:
        return int(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def _date_str(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v).strip()
    return s or None


def _list_str(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def _section_excerpt(body: str, heading: str, max_len: int = 800):
    pat = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    m = pat.search(body or "")
    if not m:
        return None
    rest = body[m.end() :]
    nxt = re.search(r"^##\s+\S", rest, re.MULTILINE)
    block = (rest[: nxt.start()] if nxt else rest).strip()
    if len(block) > max_len:
        block = block[: max_len - 20] + "…"
    return block or None


def _workspace_dict(v):
    if not v or not isinstance(v, dict):
        return {}
    return {k: _list_str(v.get(k)) for k in ("calendar", "gmail", "drive")}


def task_to_dict(task) -> dict:
    fm = task.frontmatter
    tid = str(fm.get("id") or "")
    body = task.body or ""
    title = str(fm.get("title") or "").strip()
    if not title:
        mt = HUB_TITLE_RE.search(body)
        if mt:
            title = re.sub(rf"^{re.escape(tid)}\s*[—–-]\s*", "", mt.group(1).strip()).strip()
    i = _to_int(fm.get("ice_i"))
    c = _to_int(fm.get("ice_c"))
    e = max(_to_int(fm.get("ice_e")), 1)
    work_type = normalise_work_type(fm.get("type"))
    parent = parse_parent_id(fm.get("parent"))
    return {
        "id": tid,
        "slug": str(fm.get("slug") or ""),
        "status": str(fm.get("status") or "Next"),
        "title": title or tid,
        "rel_path": task.rel_path,
        "type": work_type,
        "parent": parent,
        "ice_i": i, "ice_c": c, "ice_e": e,
        "priority_score": round((i * c) / e, 2),
        "deadline": _date_str(fm.get("deadline")),
        "waitUntil": _date_str(fm.get("waitUntil")),
        "focus": parse_focus(fm.get("focus")),
        "agent": normalise_agent(fm.get("agent")),
        "updated": _date_str(fm.get("updated")),
        "materials": _list_str(fm.get("materials")),
        "blocked_by": _list_str(fm.get("blocked_by")),
        "source": fm.get("source"),
        "is_recurring": bool(fm.get("recurring")),
        "extra_module": fm.get("extra_module"),
    }


def collect_projects(vault: DriveVault) -> list[dict]:
    out = []
    try:
        hubs = vault.list_dir("02-PROJEKTY", pattern="*.md")
    except DriveNotFoundError:
        return out
    for meta in sorted(hubs, key=lambda m: m.name):
        if meta.name.startswith("_"):
            continue
        try:
            text, _ = vault.read_text(meta.rel_path)
        except DriveNotFoundError:
            continue
        parsed = parse_task_text(text, rel_path=meta.rel_path)
        fm = parsed.frontmatter
        if (fm.get("type") or "").lower() != "project":
            continue
        body = parsed.body or ""
        slug = fm.get("slug") or meta.name.removesuffix(".md").lower().replace(" ", "-")
        title = (HUB_TITLE_RE.search(body) or [None, fm.get("title") or meta.name])
        if HUB_TITLE_RE.search(body):
            title = HUB_TITLE_RE.search(body).group(1).strip()
        else:
            title = fm.get("title") or meta.name.removesuffix(".md")
        out.append({
            "slug": slug,
            "hub_filename": meta.name,
            "title": str(title).strip(),
            "status": str(fm.get("status") or "active"),
            "aliases": _list_str(fm.get("aliases")),
            "area": fm.get("area"),
            "open_tasks_count": 0,
            "updated": _date_str(fm.get("updated")),
            "sources": _list_str(fm.get("sources")),
            "notebooklm": _list_str(fm.get("notebooklm")),
            "workspace": _workspace_dict(fm.get("workspace")),
            "context_source": fm.get("context_source"),
            "charter_scope": _section_excerpt(body, "## Scope"),
            "charter_kontext": _section_excerpt(body, "## Kontext"),
            "charter_cil": _section_excerpt(body, "## Cíl"),
            "charter_definition_of_done": _section_excerpt(body, "## Definition of done"),
            "charter_people": _section_excerpt(body, "## People"),
            "has_zdroje_dat": "## Zdroje dat" in body,
            "hierarchy": bool(
                fm.get("hierarchy") is True
                or str(fm.get("hierarchy") or "").lower() in {"true", "1", "yes"}
                or (fm.get("slug") or "") == "rb-universe-development"
            ),
        })
    return out


def collect_areas(vault: DriveVault) -> list[dict]:
    out = []
    try:
        files = vault.list_dir("03-AREAS", pattern="*.md")
    except DriveNotFoundError:
        return out
    for meta in files:
        if meta.name.startswith("_"):
            continue
        try:
            text, _ = vault.read_text(meta.rel_path)
        except DriveNotFoundError:
            continue
        parsed = parse_task_text(text, rel_path=meta.rel_path)
        fm = parsed.frontmatter
        if (fm.get("type") or "").lower() != "area":
            continue
        projects = fm.get("projects") or []
        if isinstance(projects, str):
            projects = [projects]
        out.append({
            "slug": fm.get("slug") or meta.name.removesuffix(".md"),
            "filename": meta.name,
            "projects": list(projects),
            "updated": _date_str(fm.get("updated")),
            "review_cadence": fm.get("review_cadence") or "weekly",
        })
    return out


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date()
    today_str = today.isoformat()

    projects = collect_projects(vault)
    areas = collect_areas(vault)
    active_dicts = [task_to_dict(t) for t in iter_active_tasks(vault)]
    archive_dicts = [task_to_dict(t) for t in iter_archive_tasks(vault)]

    open_count: dict[str, int] = {}
    epic_count: dict[str, int] = {}
    for t in active_dicts:
        if is_terminal(t["status"]):
            continue
        open_count[t["slug"]] = open_count.get(t["slug"], 0) + 1
        if t.get("type") == TYPE_EPIC:
            epic_count[t["slug"]] = epic_count.get(t["slug"], 0) + 1
    for p in projects:
        p["open_tasks_count"] = open_count.get(p["slug"], 0)
        p["open_epics_count"] = epic_count.get(p["slug"], 0)

    open_tasks = [t for t in active_dicts if not is_terminal(t["status"])]
    # Epics stay in open_tasks for charter counts; select_top_priority excludes them.
    top_priority_today, top_priority = select_top_priority(open_tasks, today)
    open_epics = [t for t in open_tasks if t.get("type") == TYPE_EPIC]

    focus_week = current_focus_week(today)
    focused = [t for t in open_tasks if is_focus_current(t.get("focus"), today)]
    suggestion_pool = [
        t
        for t in open_tasks
        if not is_focus_current(t.get("focus"), today) and is_queue_eligible(t, today)
    ]
    focus_suggestions = select_focus_suggestions(
        suggestion_pool,
        today=today,
        current_focus_count=len(focused),
    )

    week_ago = today - timedelta(days=7)
    recently_done = []
    recently_cancelled = []
    for t in archive_dicts + active_dicts:
        if t["status"] == STATUS_CANCELLED:
            upd_c = t.get("updated")
            if upd_c:
                try:
                    if date.fromisoformat(upd_c[:10]) >= week_ago:
                        recently_cancelled.append(t)
                except ValueError:
                    pass
            continue
        if t["status"] != STATUS_DONE:
            continue
        upd = t.get("updated")
        if not upd:
            continue
        try:
            d = date.fromisoformat(upd[:10])
        except ValueError:
            continue
        if d >= week_ago:
            recently_done.append(t)
    recently_done.sort(key=lambda t: t.get("updated") or "", reverse=True)
    recently_cancelled.sort(key=lambda t: t.get("updated") or "", reverse=True)

    upcoming = []
    soon = today + timedelta(days=7)
    for t in open_tasks:
        dl = t.get("deadline")
        if not dl:
            continue
        try:
            d = date.fromisoformat(dl[:10])
        except ValueError:
            continue
        if today <= d <= soon:
            upcoming.append(t)
    upcoming.sort(key=lambda t: t.get("deadline") or "")

    recurring_done = [
        t for t in active_dicts if t.get("is_recurring") and t["status"] == STATUS_DONE
    ]
    blocked = {t["id"]: t.get("blocked_by", []) for t in active_dicts if t.get("blocked_by")}

    stale_hubs: list[dict] = []
    for p in projects:
        slug = p["slug"]
        slug_tasks = [t for t in active_dicts if t.get("slug") == slug]
        arch_slug = [t for t in archive_dicts if t.get("slug") == slug]

        def _last_act(tasks_list):
            latest = None
            for t in tasks_list:
                upd = t.get("updated")
                if not upd:
                    continue
                try:
                    d = date.fromisoformat(str(upd)[:10])
                except ValueError:
                    continue
                if latest is None or d > latest:
                    latest = d
            return latest

        last_act = _last_act(slug_tasks + arch_slug)
        if is_narrative_stale(p.get("updated"), last_act, threshold_days=STALE_NARRATIVE_DAYS):
            stale_hubs.append({
                "slug": slug,
                "hub_filename": p.get("hub_filename"),
                "hub_updated": p.get("updated"),
                "last_task_activity": last_act.isoformat() if last_act else None,
                "open_tasks_count": p.get("open_tasks_count", 0),
            })

    threshold = today - timedelta(days=STALE_AREA_WEEKS * 7)
    stale_areas: list[dict] = []
    for area in areas:
        slugs = set(area.get("projects") or [])
        area_tasks = [t for t in active_dicts if t.get("slug") in slugs]
        open_in = [t for t in area_tasks if not is_terminal(t.get("status"))]

        def _last_act(tasks_list):
            latest = None
            for t in tasks_list:
                upd = t.get("updated")
                if not upd:
                    continue
                try:
                    d = date.fromisoformat(str(upd)[:10])
                except ValueError:
                    continue
                if latest is None or d > latest:
                    latest = d
            return latest

        last_act = _last_act(area_tasks)
        if not open_in and not last_act:
            continue
        if last_act and last_act >= threshold:
            continue
        if not last_act and open_in:
            continue
        stale_areas.append({
            "slug": area["slug"],
            "filename": area["filename"],
            "projects": list(slugs),
            "last_task_activity": last_act.isoformat() if last_act else None,
            "open_tasks_in_area": len(open_in),
        })

    snapshot = {
        "version": 2,
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "vault_path": "drive://" + root_id,
        "today": today_str,
        "stats": {
            "active_projects": sum(1 for p in projects if p["status"] in ("active", "")),
            "total_open_tasks": len(open_tasks),
            "recently_done_7d": len(recently_done),
            "recently_cancelled_7d": len(recently_cancelled),
            "focus_week": focus_week,
            "focus_count": len(focused),
            "focus_limit": FOCUS_LIMIT,
            "upcoming_deadlines_7d": len(upcoming),
            "recurring_pending_rotation": len(recurring_done),
        },
        "projects": projects,
        "areas": areas,
        "priority_rules": {
            "model": "v2 — status (co vůbec) / deadline (externí závazek) / focus (na co teď)",
            "base": "priority_score = (ice_i * ice_c) / ice_e",
            "today_score": "priority_score + urgency_bonus(deadline)",
            "urgency_bonus": {
                "overdue": URGENCY_BONUS_OVERDUE,
                "deadline_today": URGENCY_BONUS_TODAY,
                "deadline_tomorrow": URGENCY_BONUS_TOMORROW,
            },
            "top_eligible": (
                f"focus == {focus_week} (aktuální ISO týden), max {FOCUS_LIMIT}; "
                "nikdy Waiting/Backlog/Done/Cancelled"
            ),
            "focus_owner": "člověk — žádný cron nesmí zapisovat do focus",
            "sort": "today_score DESC",
        },
        "focus_week": focus_week,
        "focus_suggestions": focus_suggestions,
        "top_priority_today": top_priority_today,
        "top_priority": top_priority,
        "open_epics": open_epics,
        "recently_done": recently_done[:25],
        "recently_cancelled": recently_cancelled[:25],
        "upcoming_deadlines": upcoming,
        "recurring_pending": recurring_done,
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

    vault.write_json(OUTPUT_REL, snapshot)
    s = snapshot["stats"]
    print(
        f"agent-context: projects={s['active_projects']} "
        f"open={s['total_open_tasks']} done7d={s['recently_done_7d']} "
        f"upcoming={s['upcoming_deadlines_7d']} → drive://{OUTPUT_REL}"
    )


if __name__ == "__main__":
    main()
