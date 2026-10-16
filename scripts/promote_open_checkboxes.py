#!/usr/bin/env python3
"""Turn open **ID-N** checkboxes into task files.

Default is a dry run and writes nothing. ``--apply`` runs only when
``ALLOW_VAULT_APPLY=1``, ``VAULT_BACKEND=git`` and ``GIT_VAULT_ROOT=/data/vault``.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_LIB = _ROOT / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from hierarchy import parse_parent_id  # noqa: E402
from task_id_allocate import peek_ids, with_level  # noqa: E402

ANCHOR = "00-System/task-promotion-applied.json"
OPEN_BOX = re.compile(
    r"^- \[ \] \*\*(?P<id>[A-Za-z]+(?:-[EST])?\d+-\d+[A-Za-z]*)\*\*\s*(?P<title>.*)$"
)
HIERARCHY_SLUGS = frozenset(
    {"rb-universe-development", "it-ai-data", "firemni-procesy", "finance"}
)


def apply_allowed(env: dict[str, str]) -> str | None:
    if env.get("ALLOW_VAULT_APPLY") != "1":
        return "ALLOW_VAULT_APPLY"
    if (env.get("VAULT_BACKEND") or "").strip().lower() != "git":
        return "VAULT_BACKEND"
    if (env.get("GIT_VAULT_ROOT") or "").strip() != "/data/vault":
        return "GIT_VAULT_ROOT"
    return None


def _open_checks(body: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in (body or "").splitlines():
        matched = OPEN_BOX.match(line.strip())
        if not matched:
            continue
        title = matched.group("title").strip() or matched.group("id")
        found.append((matched.group("id"), title))
    return found


def _child_status(story_status: str) -> str:
    if story_status == "Backlog":
        return "Backlog"
    if story_status == "Waiting":
        return "Waiting"
    return "Next"


def plan_promotions(tasks: list[Any], *, id_for_index) -> list[dict[str, Any]]:
    """Pure plan. ``id_for_index(i)`` returns the next bare id, starting at 0."""
    by_id = {}
    for task in tasks:
        fm = task.frontmatter
        if fm.get("id"):
            by_id[str(fm["id"])] = task
    taken = {str(task.frontmatter.get("promoted_from") or "") for task in tasks}
    taken.discard("")
    plans: list[dict[str, Any]] = []
    cursor = 0
    for task in tasks:
        fm = task.frontmatter
        if str(fm.get("slug") or "") not in HIERARCHY_SLUGS:
            continue
        if str(fm.get("type") or "") != "story":
            continue
        checks = [(cid, title) for cid, title in _open_checks(task.body or "") if cid not in taken]
        if not checks:
            continue
        epic_id = parse_parent_id(fm.get("parent"))
        epic = by_id.get(epic_id or "")
        epic_deadline = str((epic.frontmatter.get("deadline") if epic else "") or "")[:10]
        single = len(checks) == 1
        story_deadline = str(fm.get("deadline") or "")[:10]
        blocked_by_epic = bool(single and story_deadline and epic_deadline and story_deadline > epic_deadline)
        focus = str(fm.get("focus") or "")
        give_focus = bool(single and focus)
        for checkbox_id, title in checks:
            bare = id_for_index(cursor)
            cursor += 1
            task_id = with_level(bare, "task")
            item = {
                "story_id": str(fm.get("id") or ""),
                "slug": str(fm.get("slug") or ""),
                "story_path": task.rel_path,
                "checkbox_id": checkbox_id,
                "title": title,
                "new_id": task_id,
                "status": _child_status(str(fm.get("status") or "")),
                "waitUntil": fm.get("waitUntil") if str(fm.get("status") or "") == "Waiting" else "",
                "focus": focus if give_focus else "",
                "deadline": "" if not single or blocked_by_epic else story_deadline,
                "review_deadline": "" if not single or blocked_by_epic else str(fm.get("review_deadline") or "")[:10],
                "clear_story_focus": bool(focus),
                "move_dates": bool(single and not blocked_by_epic and (story_deadline or fm.get("review_deadline"))),
                "outside_steps": "## Operativní kroky" not in (task.body or "").split(checkbox_id)[0][-400:],
            }
            plans.append(item)
    return plans


def _child_markdown(item: dict[str, Any]) -> str:
    lines = [
        "---",
        f"id: {item['new_id']}",
        "type: task",
        f"title: {item['title']}",
        f"slug: {item['slug']}",
        f"status: {item['status']}",
        f"parent: \"[[{item['story_id']}]]\"",
        f"promoted_from: {item['checkbox_id']}",
        f"focus: {item['focus']}" if item.get("focus") else "focus:",
        f"deadline: {item['deadline']}" if item.get("deadline") else "deadline:",
        f"review_deadline: {item['review_deadline']}" if item.get("review_deadline") else "review_deadline:",
        "agent: none",
        "---",
        "",
        f"# {item['new_id']} — {item['title']}",
        "",
        "## Operativní kroky",
        "",
        "## Poznámky / log",
        f"- {item.get('today', '')}: převedeno z {item['checkbox_id']}.",
        "",
    ]
    return "\n".join(lines)


def _rewrite_story(text: str, items: list[dict[str, Any]]) -> str:
    for item in items:
        pattern = re.compile(
            rf"^- \[ \] \*\*{re.escape(item['checkbox_id'])}\*\*.*$",
            re.MULTILINE,
        )
        trace = f"{item['checkbox_id']} → [[{item['new_id']} — {item['title']}]]"
        text = pattern.sub(trace, text, count=1)
    if any(item.get("clear_story_focus") for item in items):
        text = re.sub(r"(?m)^focus:.*$", "focus:", text, count=1)
    if any(item.get("move_dates") for item in items):
        text = re.sub(r"(?m)^deadline:.*$", "deadline:", text, count=1)
        text = re.sub(r"(?m)^review_deadline:.*$", "review_deadline:", text, count=1)
    return text


def write_plan(vault: Any, plans: list[dict[str, Any]], *, today: str) -> dict[str, Any]:
    """Write child files, story traces, and the anchor. A second call keeps applied_at."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    written_paths: list[str] = []
    for item in plans:
        payload = {**item, "today": today}
        path = f"02-PROJEKTY/{item['slug']}/tasks/{item['new_id']} — {item['title']}.md"
        vault.write_text(path, _child_markdown(payload))
        written_paths.append(path)
        grouped.setdefault(item["story_path"], []).append(item)
    for story_path, items in grouped.items():
        text, _meta = vault.read_text(story_path)
        vault.write_text(story_path, _rewrite_story(text, items))
    existing = None
    try:
        raw, _meta = vault.read_text(ANCHOR)
        existing = json.loads(raw).get("applied_at")
    except Exception:
        existing = None
    if not existing:
        vault.write_text(ANCHOR, json.dumps({"applied_at": today}, ensure_ascii=False) + "\n")
        existing = today
    return {"files": written_paths, "applied_at": existing}


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    env_map = env if env is not None else dict(os.environ)
    apply = "--apply" in args
    if not apply:
        print(json.dumps({"apply": False, "written": False}, ensure_ascii=False))
        return 0
    reason = apply_allowed(env_map)
    if reason:
        print(f"apply refused: {reason}", file=sys.stderr)
        return 2
    from collections import Counter

    from task_io import iter_active_tasks
    from vault_factory import open_vault

    with open_vault(env=env_map, discard_dirty_on_error=True) as vault:
        if getattr(vault, "skipped", False):
            print("session skipped", file=sys.stderr)
            return 2
        tasks = list(iter_active_tasks(vault))
        slugs: list[str] = []
        taken = {str(task.frontmatter.get("promoted_from") or "") for task in tasks}
        taken.discard("")
        for task in tasks:
            fm = task.frontmatter
            if str(fm.get("slug") or "") not in HIERARCHY_SLUGS or str(fm.get("type") or "") != "story":
                continue
            for checkbox_id, _title in _open_checks(task.body or ""):
                if checkbox_id not in taken:
                    slugs.append(str(fm.get("slug")))
        pools = {
            slug: iter(peek_ids(vault, slug, count))
            for slug, count in Counter(slugs).items()
            if count
        }
        sequence = [next(pools[slug])[0] for slug in slugs]
        plans = plan_promotions(tasks, id_for_index=lambda index: sequence[index])
        from datetime import datetime
        from zoneinfo import ZoneInfo

        today = datetime.now(ZoneInfo("Europe/Prague")).date().isoformat()
        result = write_plan(vault, plans, today=today)
    print(json.dumps({"apply": True, "files": len(result["files"]), "applied_at": result["applied_at"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
