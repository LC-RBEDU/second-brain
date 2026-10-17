"""create_task — ceiling + write + tombstone under mutate session (R6 / B4 / B31)."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from context_tombstone import delete_context_tombstone  # noqa: E402
from deadline_order import DeadlineNode, evaluate_deadline_order, node_from_frontmatter  # noqa: E402
from hierarchy import parse_parent_id  # noqa: E402
from task_id_allocate import peek_ids, with_level  # noqa: E402
from task_io import iter_active_tasks, parse_task_text  # noqa: E402

from app.errors import BrainClientError  # noqa: E402
from app.tools.parent_link import resolve_parent_raw  # noqa: E402
from app.tools.project_guard import require_project  # noqa: E402
from app.fm_contract import strip_aliases_for_new_write  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

_SAFE_TITLE = re.compile(r"[^\w\s\-—]+", re.UNICODE)


def _slugify_title(title: str) -> str:
    t = _SAFE_TITLE.sub("", title).strip()
    t = re.sub(r"\s+", "-", t)
    return t[:80] or "task"


def _render_task(
    *,
    task_id: str,
    title: str,
    slug: str,
    hub: str,
    level: str,
    status: str,
    detail: str,
    parent: str = "",
    deadline: str = "",
    review_deadline: str = "",
    promoted_from: str = "",
    hierarchy: bool = True,
) -> str:
    hierarchy = True
    today = date.today().isoformat()
    type_map = {"epic": "epic", "story": "story", "task": "task"}
    work_type = type_map.get(level, "story")
    fm = {
        "id": task_id,
        "type": work_type,
        "title": title,
        "project": f"[[{hub}]]",
        "slug": slug,
        "status": status,
        "parent": parent,
        "focus": "",
        "agent": "none",
        "deadline": deadline,
        "review_deadline": review_deadline,
        "waitUntil": "",
        "created": today,
        "updated": today,
        "materials": [],
        "source": "brain-api",
        "promoted_from": promoted_from,
        "company_priorities": [],
        "blocked_by": [],
    }
    if not (hierarchy and work_type == "task"):
        fm["ice_i"] = 5
        fm["ice_c"] = 5
        fm["ice_e"] = 5
    if promoted_from:
        fm["promoted_from"] = promoted_from
    else:
        fm.pop("promoted_from", None)
    fm = strip_aliases_for_new_write(fm)
    # YAML by hand — avoid dumping empty aliases
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: []")
        elif v == "" and k in ("parent", "focus", "deadline", "review_deadline", "waitUntil"):
            lines.append(f"{k}:")
        elif isinstance(v, str) and (":" in v or v.startswith("[[")):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {task_id} — {title}")
    lines.append("")
    lines.append(f"**Z:** brain-api")
    lines.append(f"**Detail:** {detail or '—'}")
    lines.append("")
    lines.append("## Operativní kroky")
    if not (hierarchy and work_type in {"task", "story"}):
        lines.append(f"- [ ] **{task_id}-1** …")
    lines.append("")
    lines.append("## Poznámky / log")
    lines.append(f"- {today}: Založeno přes Brain API.")
    lines.append("")
    return "\n".join(lines)


def _promoted_taken(vault: Any, slug: str, promoted_from: str) -> bool:
    if not promoted_from:
        return False
    try:
        files = vault.list_dir(f"02-PROJEKTY/{slug}/tasks", pattern="*.md")
    except Exception:
        return False
    needle = f"promoted_from: {promoted_from}"
    open_box = f"- [ ] **{promoted_from}**"
    for meta in files:
        try:
            text, _ = vault.read_text(getattr(meta, "rel_path", ""))
        except Exception:
            continue
        if needle in text or open_box in text:
            return True
    return False


def _reject_deadline_order(
    prepared: list[dict[str, Any]],
    bare_ids: list[tuple[str, str]],
    existing_tasks: list[Any],
) -> None:
    """409 and zero writes when a new deadline sits after an ancestor in the narrow cone."""
    fresh: list[DeadlineNode] = []
    for spec, (bare, _where) in zip(prepared, bare_ids):
        deadline = str(spec.get("deadline") or "").strip()
        if not deadline:
            continue
        parent = parse_parent_id(spec.get("parent_link") or spec.get("parent"))
        fresh.append(
            DeadlineNode(
                id=with_level(bare, str(spec.get("level") or "story")),
                parent_id=parent,
                status=str(spec.get("status") or "Next"),
                deadline=deadline[:10],
            )
        )
    if not fresh:
        return
    existing = [
        node_from_frontmatter(task.frontmatter)
        for task in existing_tasks
    ]
    order = evaluate_deadline_order(
        existing + fresh,
        touched_ids={node.id for node in fresh},
    )
    if order.get("ok"):
        return
    raise BrainClientError(
        message="deadline_order",
        status_code=409,
        error_reason="deadline_order",
        detail=order,
    )


def create_task(
    *,
    slug: str,
    title: str = "",
    detail: str = "",
    level: str = "story",
    status: str = "Next",
    parent: str = "",
    deadline: str = "",
    review_deadline: str = "",
    promoted_from: str = "",
    dry_run: bool = False,
    items: list[dict[str, Any]] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    slug = (slug or "").strip()
    if not slug:
        raise BrainClientError(message="slug required", status_code=400, error_reason="missing_slug")
    specs = items or [
        {
            "title": title,
            "detail": detail,
            "level": level,
            "status": status,
            "parent": parent,
            "deadline": deadline,
            "review_deadline": review_deadline,
            "promoted_from": promoted_from,
        }
    ]
    for spec in specs:
        if not str(spec.get("title") or "").strip():
            raise BrainClientError(message="title required", status_code=400, error_reason="missing_title")
        if spec.get("level", "story") not in ("epic", "story", "task"):
            raise BrainClientError(message="level must be epic|story|task", status_code=400, error_reason="bad_level")

    mode = "read" if dry_run else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        hub = require_project(vault, slug)
        if mode == "mutate":
            delete_context_tombstone(vault)
        active = list(iter_active_tasks(vault))
        prepared: list[dict[str, Any]] = []
        seen_promoted: set[str] = set()
        for spec in specs:
            spec_level = str(spec.get("level") or "story")
            spec_parent = str(spec.get("parent") or "").strip()
            parent_link = resolve_parent_raw(
                spec_parent,
                active,
                child_id="",
                child_type=spec_level,
            )
            promo = str(spec.get("promoted_from") or "").strip()
            if promo:
                if promo in seen_promoted or _promoted_taken(vault, slug, promo):
                    raise BrainClientError(message="promoted_from taken", status_code=409, error_reason="promoted_from_taken")
                seen_promoted.add(promo)
            prepared.append({**spec, "level": spec_level, "parent_link": parent_link, "promoted_from": promo})
        bare_ids = peek_ids(vault, slug, len(prepared))
        _reject_deadline_order(prepared, bare_ids, active)
        created: list[dict[str, str]] = []
        rel_dir = f"02-PROJEKTY/{slug}/tasks"
        if not dry_run:
            vault.mkdir_p(rel_dir)
        for spec, (bare, where) in zip(prepared, bare_ids):
            task_id = with_level(bare, spec["level"])
            rel = f"{rel_dir}/{task_id} — {_slugify_title(str(spec['title']))}.md"
            body = _render_task(
                task_id=task_id,
                title=str(spec["title"]).strip(),
                slug=slug,
                hub=hub,
                level=spec["level"],
                status=str(spec.get("status") or "Next"),
                detail=str(spec.get("detail") or ""),
                parent=spec["parent_link"],
                deadline=str(spec.get("deadline") or ""),
                review_deadline=str(spec.get("review_deadline") or ""),
                promoted_from=spec["promoted_from"],
                hierarchy=True,
            )
            if not dry_run:
                vault.write_text(rel, body)
            created.append({"id": task_id, "path": rel, "ceiling_source": where})
    if len(created) == 1 and not items:
        return {**created[0], "title": title, "slug": slug, "dry_run": dry_run}
    return {"slug": slug, "dry_run": dry_run, "created": created}
