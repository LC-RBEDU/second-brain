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


def _path_title(title: str, *, new_id: str) -> str:
    """One path segment. Slashes in a checkbox title must not become directories."""
    text = " ".join(str(title).replace("/", " ").replace("\\", " ").split())
    text = "".join(ch for ch in text if ord(ch) >= 32)
    if not text:
        text = "krok"
    stem = f"{new_id} — {text}.md"
    if len(stem.encode("utf-8")) <= 200:
        return text
    budget = 200 - len(f"{new_id} — .md".encode("utf-8"))
    cut = text.encode("utf-8")[: max(budget, 1)].decode("utf-8", "ignore").rstrip()
    return cut or "krok"


def _yaml(value: str) -> str:
    text = str(value)
    if not text:
        return ""
    if text.startswith((" ", "[[", "'", '"')) or any(ch in text for ch in ":{}[]&*!|>%@`#"):
        return json.dumps(text, ensure_ascii=False)
    return text


def _outside_steps(body: str, checkbox_id: str) -> bool:
    index = body.find(f"**{checkbox_id}**")
    if index < 0:
        return False
    head = body[:index]
    marker = head.rfind("\n## ")
    if marker < 0:
        heading = head if head.startswith("## ") else ""
    else:
        heading = head[marker + 1 :].splitlines()[0]
    return "Operativní kroky" not in heading


def _open_checks(body: str) -> list[tuple[str, str, str]]:
    lines = (body or "").splitlines()
    found: list[tuple[str, str, str]] = []
    index = 0
    while index < len(lines):
        matched = OPEN_BOX.match(lines[index].strip())
        if not matched:
            index += 1
            continue
        title = matched.group("title").strip() or matched.group("id")
        extra: list[str] = []
        index += 1
        while index < len(lines) and lines[index].startswith((" ", "\t")) and lines[index].strip():
            extra.append(lines[index].strip())
            index += 1
        found.append((matched.group("id"), title, "\n".join(extra)))
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
        checks = [
            (cid, title, extra)
            for cid, title, extra in _open_checks(task.body or "")
            if cid not in taken
        ]
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
        for checkbox_id, title, extra in checks:
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
                "agent": str(fm.get("agent") or "none"),
                "waitUntil": fm.get("waitUntil") if str(fm.get("status") or "") == "Waiting" else "",
                "detail": extra,
                "focus": focus if give_focus else "",
                "deadline": "" if not single or blocked_by_epic else story_deadline,
                "review_deadline": "" if not single or blocked_by_epic else str(fm.get("review_deadline") or "")[:10],
                "clear_story_focus": bool(focus),
                "move_dates": bool(single and not blocked_by_epic and (story_deadline or fm.get("review_deadline"))),
                "blocked_by_epic": blocked_by_epic,
                "story_deadline": story_deadline,
                "epic_id": epic_id or "",
                "epic_deadline": epic_deadline,
                "outside_steps": _outside_steps(task.body or "", checkbox_id),
            }
            plans.append(item)
    return plans


def _child_markdown(item: dict[str, Any]) -> str:
    lines = [
        "---",
        f"id: {item['new_id']}",
        "type: task",
        f"title: {_yaml(item['title'])}",
        f"slug: {item['slug']}",
        f"status: {item['status']}",
        f"parent: \"[[{item['story_id']}]]\"",
        f"promoted_from: {item['checkbox_id']}",
        f"agent: {item.get('agent') or 'none'}",
        f"focus: {item['focus']}" if item.get("focus") else "focus:",
        f"deadline: {item['deadline']}" if item.get("deadline") else "deadline:",
        f"review_deadline: {item['review_deadline']}" if item.get("review_deadline") else "review_deadline:",
        f"waitUntil: {item['waitUntil']}" if item.get("waitUntil") else "waitUntil:",
        "---",
        "",
        f"# {item['new_id']} — {item['title']}",
        "",
        item.get("detail") or "",
        "",
        "## Operativní kroky",
        "",
        "## Poznámky / log",
        f"- {item.get('today', '')}: převedeno z {item['checkbox_id']}.",
        "",
    ]
    return "\n".join(lines)


_EMBED = re.compile(r"(?m)^!\[\[[^\]]*\.base[^\]]*\]\]\s*\n?")


def _rewrite_story(text: str, items: list[dict[str, Any]]) -> str:
    lines = text.splitlines()
    for item in items:
        kept: list[str] = []
        index = 0
        pattern = re.compile(rf"^- \[ \] \*\*{re.escape(item['checkbox_id'])}\*\*")
        while index < len(lines):
            if pattern.match(lines[index].strip()):
                index += 1
                while index < len(lines) and lines[index].startswith((" ", "\t")) and lines[index].strip():
                    index += 1
                continue
            kept.append(lines[index])
            index += 1
        lines = kept
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    traces = [
        f"- {item['checkbox_id']} → [[{item['new_id']} — {item['path_title']}]]"
        for item in items
    ]
    block = "\n".join(traces) + "\n"
    if "## Poznámky / log" in text:
        text = text.replace("## Poznámky / log\n", "## Poznámky / log\n" + block, 1)
    else:
        text += "\n## Poznámky / log\n" + block
    if any(item.get("clear_story_focus") for item in items):
        text = re.sub(r"(?m)^focus:.*$", "focus:", text, count=1)
    if any(item.get("move_dates") for item in items):
        text = re.sub(r"(?m)^deadline:.*$", "deadline:", text, count=1)
        text = re.sub(r"(?m)^review_deadline:.*$", "review_deadline:", text, count=1)
    return text


def strip_bases_and_embeds(vault: Any) -> list[str]:
    """Delete ``00-System/Bases/*.base`` and drop ``![[*.base]]`` embeds."""
    removed: list[str] = []
    try:
        metas = vault.list_dir("00-System/Bases", pattern="*.base", recursive=True)
    except Exception:
        metas = []
    for meta in metas:
        rel = getattr(meta, "rel_path", "")
        if not rel:
            continue
        if hasattr(vault, "delete"):
            vault.delete(rel)
        else:
            vault.write_text(rel, "")
        removed.append(rel)
    paths: list[str] = []
    try:
        hubs = vault.list_dir("02-PROJEKTY", pattern="*.md", recursive=True)
        paths.extend(getattr(meta, "rel_path", "") for meta in hubs)
    except Exception:
        pass
    for rel in paths:
        if not rel:
            continue
        try:
            text, _meta = vault.read_text(rel)
        except Exception:
            continue
        cleaned = _EMBED.sub("", text)
        if cleaned != text:
            vault.write_text(rel, cleaned)
            removed.append(rel)
    return removed


def write_plan(vault: Any, plans: list[dict[str, Any]], *, today: str) -> dict[str, Any]:
    """Write child files, story traces, and the anchor. A second call keeps applied_at."""
    strip_bases_and_embeds(vault)
    grouped: dict[str, list[dict[str, Any]]] = {}
    written_paths: list[str] = []
    for item in plans:
        payload = {**item, "today": today, "path_title": _path_title(item["title"], new_id=item["new_id"])}
        path = f"02-PROJEKTY/{item['slug']}/tasks/{item['new_id']} — {payload['path_title']}.md"
        vault.write_text(path, _child_markdown(payload))
        written_paths.append(path)
        grouped.setdefault(item["story_path"], []).append(payload)
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


def _summarize(plans: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in plans:
        rows.append(
            {
                "story_id": item["story_id"],
                "checkbox_id": item["checkbox_id"],
                "new_id": item["new_id"],
                "focus": item.get("focus") or "",
                "clear_story_focus": bool(item.get("clear_story_focus")),
                "move_dates": bool(item.get("move_dates")),
                "deadline": item.get("deadline") or "",
                "blocked_by_epic": bool(item.get("blocked_by_epic")),
                "story_deadline": item.get("story_deadline") or "",
                "epic_id": item.get("epic_id") or "",
                "epic_deadline": item.get("epic_deadline") or "",
                "outside_steps": bool(item.get("outside_steps")),
            }
        )
    return {"apply": False, "written": False, "count": len(rows), "plans": rows}


def main(
    argv: list[str] | None = None,
    env: dict[str, str] | None = None,
    tasks: list[Any] | None = None,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    env_map = env if env is not None else dict(os.environ)
    apply = "--apply" in args
    if not apply:
        if tasks is None:
            from collections import Counter

            from task_io import iter_active_tasks
            from vault_factory import open_vault

            with open_vault(env=env_map) as vault:
                loaded = list(iter_active_tasks(vault))
                slugs = []
                taken = {str(task.frontmatter.get("promoted_from") or "") for task in loaded}
                taken.discard("")
                for task in loaded:
                    fm = task.frontmatter
                    if str(fm.get("slug") or "") not in HIERARCHY_SLUGS or str(fm.get("type") or "") != "story":
                        continue
                    for checkbox_id, _title, _extra in _open_checks(task.body or ""):
                        if checkbox_id not in taken:
                            slugs.append(str(fm.get("slug")))
                pools = {
                    slug: iter(peek_ids(vault, slug, count))
                    for slug, count in Counter(slugs).items()
                    if count
                }
                sequence = [next(pools[slug])[0] for slug in slugs] or ["TMP1"]
                planned = plan_promotions(loaded, id_for_index=lambda index: sequence[index])
        else:
            planned = plan_promotions(tasks, id_for_index=lambda index: f"TMP{index + 1}")
        print(json.dumps(_summarize(planned), ensure_ascii=False))
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
            for checkbox_id, _title, _extra in _open_checks(task.body or ""):
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
