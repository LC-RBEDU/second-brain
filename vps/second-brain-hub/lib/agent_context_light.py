"""Project full agent-context.json → light index + charters.json.

Light is for ``agenda-meeting-prep`` only. Full snapshot stays SSOT for
other skills. Same ``generated_at`` ties the three files together.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from today_priority import today_score as compute_today_score

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")

# Slim task fields for the flat open-task index (meeting-prep).
LIGHT_TASK_KEYS = (
    "id",
    "slug",
    "type",
    "parent",
    "status",
    "title",
    "deadline",
    "review_deadline",
    "due",
    "waitUntil",
    "focus",
    "agent",
    "priority_score",
    "today_score",
    "updated",
    "blocked_by",
)

# Project metadata kept in light (no charter_*). Explicit allow-list — meeting-prep only.
LIGHT_PROJECT_KEYS = (
    "slug",
    "hub_filename",
    "title",
    "status",
    "aliases",
    "area",
    "open_tasks_count",
    "hierarchy",
    "updated",
)

ID_LIST_KEYS = (
    "top_priority_today",
    "top_priority",
    "upcoming_deadlines",
    "due_soon",
    "needs_decision",
    "no_review_deadline",
    "stale_focus",
    "focus_suggestions",
    "open_epics",
)


def parse_people_from_section(people_section: str | None) -> list[str]:
    """First wikilink per table row in hub ``## People`` (= Kdo column)."""
    if not people_section:
        return []
    names: list[str] = []
    seen: set[str] = set()
    for line in people_section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        if re.search(r"\|\s*Kdo\s*\|", stripped, re.I):
            continue
        m = WIKILINK_RE.search(stripped)
        if not m:
            continue
        name = m.group(1).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _ids_from_list(items: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(items, list):
        return out
    for item in items:
        if isinstance(item, dict):
            tid = item.get("id")
            if tid:
                out.append(str(tid))
        elif item is not None:
            out.append(str(item))
    return out


def _slim_task(task: dict, today: date) -> dict:
    materials = task.get("materials") or []
    mats = materials if isinstance(materials, list) else []
    ps = float(task.get("priority_score") or 0)
    ts = task.get("today_score")
    if ts is None:
        ts = compute_today_score(
            ps, task.get("deadline"), today, task.get("review_deadline")
        )
    slim = {k: task.get(k) for k in LIGHT_TASK_KEYS}
    slim["priority_score"] = ps
    slim["today_score"] = float(ts)
    slim["materials_count"] = len(mats)
    slim["blocked_by"] = list(task.get("blocked_by") or [])
    return slim


def build_charters(snapshot: dict) -> dict:
    """Narativy keyed by project slug."""
    charters: dict[str, dict[str, str | None]] = {}
    for proj in snapshot.get("projects") or []:
        if not isinstance(proj, dict):
            continue
        slug = proj.get("slug")
        if not slug:
            continue
        charters[str(slug)] = {
            "scope": proj.get("charter_scope"),
            "kontext": proj.get("charter_kontext"),
            "cil": proj.get("charter_cil"),
            "definition_of_done": proj.get("charter_definition_of_done"),
            "people": proj.get("charter_people"),
        }
    return {
        "generated_at": snapshot.get("generated_at"),
        "charters": charters,
    }


def project_light(
    snapshot: dict,
    open_tasks: list[dict],
    *,
    today: date | None = None,
) -> dict:
    """Derive meeting-prep light index from a full snapshot + all open tasks."""
    if today is None:
        today_s = snapshot.get("today")
        today = date.fromisoformat(str(today_s)) if today_s else date.today()

    projects_light: list[dict] = []
    for proj in snapshot.get("projects") or []:
        if not isinstance(proj, dict):
            continue
        light_proj = {k: proj.get(k) for k in LIGHT_PROJECT_KEYS if k in proj or k in ("aliases",)}
        light_proj["aliases"] = list(proj.get("aliases") or [])
        light_proj["people"] = parse_people_from_section(proj.get("charter_people"))
        projects_light.append(light_proj)

    # Deduplicate open tasks by id (first wins); skip empty ids.
    tasks_by_id: dict[str, dict] = {}
    for task in open_tasks:
        if not isinstance(task, dict):
            continue
        tid = task.get("id")
        if not tid or tid in tasks_by_id:
            continue
        tasks_by_id[str(tid)] = _slim_task(task, today)

    light: dict[str, Any] = {
        "version": snapshot.get("version", 2),
        "generated_at": snapshot.get("generated_at"),
        "today": snapshot.get("today"),
        "stats": snapshot.get("stats"),
        "priority_rules": snapshot.get("priority_rules"),
        "focus_week": snapshot.get("focus_week"),
        "projects": projects_light,
        "tasks": list(tasks_by_id.values()),
    }
    for key in ID_LIST_KEYS:
        light[key] = _ids_from_list(snapshot.get(key))
    return light


def atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON via temp + replace so readers never see a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_context_bundle(
    out_dir: Path,
    snapshot: dict,
    open_tasks: list[dict],
    *,
    today: date | None = None,
) -> dict[str, Path | None]:
    """Write full + light + charters. Full always written; light/charters best-effort.

    Returns paths written (None if a side file failed).
    """
    full_path = out_dir / "agent-context.json"
    light_path = out_dir / "agent-context-light.json"
    charters_path = out_dir / "charters.json"

    # Drop internal-only keys before persisting full.
    full = {k: v for k, v in snapshot.items() if not str(k).startswith("_")}
    atomic_write_json(full_path, full)

    written: dict[str, Path | None] = {
        "full": full_path,
        "light": None,
        "charters": None,
    }
    try:
        light = project_light(snapshot, open_tasks, today=today)
        atomic_write_json(light_path, light)
        written["light"] = light_path
    except Exception as exc:  # noqa: BLE001 — side file must not block SSOT
        print(f"WARNING: agent-context-light.json write failed: {exc}")

    try:
        charters = build_charters(snapshot)
        atomic_write_json(charters_path, charters)
        written["charters"] = charters_path
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: charters.json write failed: {exc}")

    return written
