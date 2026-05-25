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
    return {
        "id": tid,
        "slug": str(fm.get("slug") or ""),
        "status": str(fm.get("status") or "Next"),
        "title": title or tid,
        "rel_path": task.rel_path,
        "ice_i": i, "ice_c": c, "ice_e": e,
        "priority_score": round((i * c) / e, 2),
        "deadline": _date_str(fm.get("deadline")),
        "waitUntil": _date_str(fm.get("waitUntil")),
        "updated": _date_str(fm.get("updated")),
        "materials": _list_str(fm.get("materials")),
        "blocked_by": _list_str(fm.get("blocked_by")),
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
    active_dicts = [task_to_dict(t) for t in iter_active_tasks(vault)]
    archive_dicts = [task_to_dict(t) for t in iter_archive_tasks(vault)]

    open_count: dict[str, int] = {}
    for t in active_dicts:
        if t["status"] != "Done":
            open_count[t["slug"]] = open_count.get(t["slug"], 0) + 1
    for p in projects:
        p["open_tasks_count"] = open_count.get(p["slug"], 0)

    open_tasks = [t for t in active_dicts if t["status"] != "Done"]
    open_tasks.sort(key=lambda t: -t.get("priority_score", 0))
    top_priority = open_tasks[:15]

    week_ago = today - timedelta(days=7)
    recently_done = []
    for t in archive_dicts + active_dicts:
        if t["status"] != "Done":
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

    recurring_done = [t for t in active_dicts if t.get("is_recurring") and t["status"] == "Done"]
    blocked = {t["id"]: t.get("blocked_by", []) for t in active_dicts if t.get("blocked_by")}

    snapshot = {
        "version": 2,
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "vault_path": "drive://" + root_id,
        "today": today_str,
        "stats": {
            "active_projects": sum(1 for p in projects if p["status"] in ("active", "")),
            "total_open_tasks": len(open_tasks),
            "recently_done_7d": len(recently_done),
            "upcoming_deadlines_7d": len(upcoming),
            "recurring_pending_rotation": len(recurring_done),
        },
        "projects": projects,
        "top_priority": top_priority,
        "recently_done": recently_done[:25],
        "upcoming_deadlines": upcoming,
        "recurring_pending": recurring_done,
        "blocked_by_graph": blocked,
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
